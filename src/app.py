"""
Flask Web Application Server for Interactive Molecular Toxicity Prediction.
Provides REST API endpoints for live SMILES inference, atom saliency rendering, and metrics overview.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import numpy as np
import pandas as pd
import requests
import torch
from flask import Flask, request, jsonify, send_from_directory
from torch_geometric.data import Batch

from src.featurize import smiles_to_graph
from src.dataset import TOX21_TASKS, Tox21GraphDataset
from src.ddi_model import DualEncoderDDI
from src.model import get_model, MPNNModel
from src.visualize import compute_atom_saliency, render_molecule_svg
from src.train import train_gnn

app = Flask(__name__, static_folder='../public', static_url_path='')

# Change this to the model name installed locally with `ollama pull <model>`.
OLLAMA_MODEL = "llama3"

# Global cache for loaded GNN models
LOADED_MODELS = {}
LOADED_DDI_MODELS = {}

PRESET_MOLECULES = [
    {"name": "Aspirin (Analgesic)", "smiles": "CC(=O)OC1=CC=CC=C1C(=O)O"},
    {"name": "Caffeine (Stimulant)", "smiles": "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"},
    {"name": "Ibuprofen (NSAID)", "smiles": "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O"},
    {"name": "Paracetamol (Acetaminophen)", "smiles": "CC(=O)NC1=CC=C(O)C=C1"},
    {"name": "Benzene (Carcinogen)", "smiles": "C1=CC=CC=C1"},
    {"name": "Tox21 Sample (SR-ARE Active)", "smiles": "O=C1C2=CC=CC=C2C(=O)C3=C1C=CC=C3"}
]


def build_ddinter_name_index() -> dict:
    """Build a lowercase DDInter drug-name to ID index from the bulk CSVs."""
    index = {}
    for code in ['A', 'B', 'D', 'H', 'L', 'P', 'R', 'V']:
        csv_path = os.path.join('data', 'raw', f'ddinter_downloads_code_{code}.csv')
        frame = pd.read_csv(csv_path)
        for _, row in frame[['Drug_A', 'DDInterID_A', 'Drug_B', 'DDInterID_B']].iterrows():
            if pd.notna(row['Drug_A']) and pd.notna(row['DDInterID_A']):
                index[str(row['Drug_A']).strip().lower()] = str(row['DDInterID_A']).strip()
            if pd.notna(row['Drug_B']) and pd.notna(row['DDInterID_B']):
                index[str(row['Drug_B']).strip().lower()] = str(row['DDInterID_B']).strip()
    return index


DDINTER_NAME_INDEX = build_ddinter_name_index()


def load_or_train_default_model(arch: str = 'gcn') -> torch.nn.Module:
    """Load pre-trained model checkpoint or train a fast model if missing."""
    arch = arch.lower()
    if arch in LOADED_MODELS:
        return LOADED_MODELS[arch]

    model_path = os.path.join("models", f"best_{arch}.pt")
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    if os.path.exists(model_path):
        print(f"Loading trained weights for {arch.upper()} from {model_path}...")
        ckpt = torch.load(model_path, map_location=device, weights_only=False)
        if isinstance(ckpt, dict) and 'config' in ckpt:
            cfg = ckpt['config']
            model = get_model(cfg.get('arch', arch), in_dim=cfg.get('in_dim', 72),
                              edge_dim=cfg.get('edge_dim', 6), hidden_dim=cfg.get('hidden_dim', 128), num_tasks=12).to(device)
            model.load_state_dict(ckpt['state_dict'])
        else:
            model = get_model(arch, in_dim=72, edge_dim=6, hidden_dim=128, num_tasks=12).to(device)
            model.load_state_dict(ckpt)
    else:
        print(f"No checkpoint found for {arch.upper()}. Training quick model...")
        res = train_gnn(arch=arch, epochs=15, batch_size=64)
        model = res['model']

    model.eval()
    LOADED_MODELS[arch] = model
    return model


def load_ddi_model(arch: str = 'gcn') -> torch.nn.Module:
    """Load and cache a trained dual-encoder DDI severity model."""
    arch = arch.lower()
    if arch not in ('gcn', 'gin'):
        raise ValueError(
            f"Unsupported DDI architecture '{arch}'. Choose 'gcn' or 'gin'; "
            "MPNN was not trained for this feature due to prohibitive CPU training cost."
        )

    if arch in LOADED_DDI_MODELS:
        return LOADED_DDI_MODELS[arch]

    model_path = os.path.join('models', f'best_ddi_{arch}.pt')
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"No DDI checkpoint found at {model_path}. Run "
            f"`python -m src.train_ddi --arch {arch} --epochs 15` first."
        )

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    checkpoint = torch.load(model_path, map_location=device, weights_only=False)
    config = checkpoint['config']
    model = DualEncoderDDI(
        arch=config['arch'],
        in_dim=config['in_dim'],
        edge_dim=config['edge_dim'],
        hidden_dim=config['hidden_dim'],
        num_outputs=config['num_outputs']
    ).to(device)
    model.load_state_dict(checkpoint['state_dict'])
    model.eval()
    LOADED_DDI_MODELS[arch] = model
    return model


@app.route('/')
def index():
    """Serve the main web application UI."""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/presets', methods=['GET'])
def get_presets():
    """Return preset SMILES molecules for testing."""
    return jsonify({'presets': PRESET_MOLECULES})


@app.route('/api/predict', methods=['POST'])
def predict_toxicity():
    """Run GNN toxicity prediction and atom saliency calculation on input SMILES."""
    data = request.get_json() or {}
    smiles = data.get('smiles', '').strip()
    arch = data.get('arch', 'gcn').lower()
    selected_task_idx = int(data.get('task_idx', 0))

    if not smiles:
        return jsonify({'error': 'No SMILES string provided'}), 400

    try:
        model = load_or_train_default_model(arch)
        graph = smiles_to_graph(smiles)

        if graph is None:
            return jsonify({'error': f'Invalid chemical SMILES: "{smiles}". Please verify the syntax.'}), 400

        device = next(model.parameters()).device
        x = graph.x.to(device)
        edge_index = graph.edge_index.to(device)
        edge_attr = graph.edge_attr.to(device) if hasattr(graph, 'edge_attr') and graph.edge_attr is not None else None
        batch = torch.zeros(x.size(0), dtype=torch.long, device=device)

        with torch.no_grad():
            if isinstance(model, MPNNModel):
                logits = model(x, edge_index, edge_attr, batch)
            else:
                logits = model(x, edge_index, batch)

            probs = torch.sigmoid(logits)[0].cpu().numpy()

        # Compute atom saliency for the selected task endpoint
        saliency, _, task_name = compute_atom_saliency(model, smiles, task_idx=selected_task_idx)
        svg_rendering = render_molecule_svg(smiles, saliency)

        predictions = []
        for idx, t_name in enumerate(TOX21_TASKS):
            p = float(probs[idx])
            predictions.append({
                'task': t_name,
                'probability': p,
                'status': 'Toxic' if p >= 0.5 else 'Safe',
                'level': 'High' if p >= 0.7 else ('Moderate' if p >= 0.4 else 'Low')
            })

        return jsonify({
            'smiles': smiles,
            'arch': arch.upper(),
            'predictions': predictions,
            'saliency': saliency.tolist() if saliency is not None else [],
            'svg': svg_rendering,
            'selected_task': task_name,
            'num_atoms': x.size(0)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/predict-interaction', methods=['POST'])
def predict_interaction():
    """Predict the severity of a known or suspected drug-drug interaction."""
    try:
        data = request.get_json() or {}
        name_a = data.get('name_a', '').strip()
        name_b = data.get('name_b', '').strip()
        arch = data.get('arch', 'gcn').lower()

        if not name_a or not name_b:
            return jsonify({'error': 'Both name_a and name_b are required.'}), 400

        try:
            smiles_a = name_to_smiles(name_a)
        except Exception as e:
            return jsonify({'error': f"Could not resolve 'name_a' ('{name_a}'): {e}"}), 400

        try:
            smiles_b = name_to_smiles(name_b)
        except Exception as e:
            return jsonify({'error': f"Could not resolve 'name_b' ('{name_b}'): {e}"}), 400

        graph_a = smiles_to_graph(smiles_a)
        if graph_a is None:
            return jsonify({'error': f'Could not parse SMILES for name_a: "{smiles_a}"'}), 400

        graph_b = smiles_to_graph(smiles_b)
        if graph_b is None:
            return jsonify({'error': f'Could not parse SMILES for name_b: "{smiles_b}"'}), 400

        batch_a = Batch.from_data_list([graph_a])
        batch_b = Batch.from_data_list([graph_b])
        model = load_ddi_model(arch)
        device = next(model.parameters()).device
        batch_a = batch_a.to(device)
        batch_b = batch_b.to(device)

        with torch.no_grad():
            logits = model(batch_a, batch_b)
            probabilities = torch.softmax(logits, dim=-1)[0]
            predicted_class = int(torch.argmax(probabilities).item())

        labels = {0: 'Minor', 1: 'Moderate', 2: 'Major'}
        return jsonify({
            'predicted_severity': labels[predicted_class],
            'probabilities': {
                labels[idx]: float(probabilities[idx].cpu().item())
                for idx in range(3)
            },
            'smiles_a': smiles_a,
            'smiles_b': smiles_b,
            'name_a': name_a,
            'name_b': name_b,
            'arch': arch.upper()
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def name_to_smiles(name: str) -> str:
    """Resolve a chemical name to its PubChem SMILES.

    Note: PubChem's PUG-REST API returns the SMILES field under the key
    'ConnectivitySMILES' (its current name for what used to be called
    'CanonicalSMILES'). We check both keys so this keeps working regardless
    of which naming PubChem uses for a given request.
    """
    encoded_name = requests.utils.quote(name, safe='')
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{encoded_name}/property/CanonicalSMILES/JSON"

    def log_response(response=None):
        print(f"PubChem URL: {url}", flush=True)
        print(f"PubChem status: {response.status_code if response is not None else 'unavailable'}", flush=True)
        if response is None:
            print("PubChem response: unavailable", flush=True)
            return
        try:
            print(f"PubChem response: {response.json()}", flush=True)
        except ValueError:
            print(f"PubChem response: {response.text}", flush=True)

    try:
        response = requests.get(url, timeout=10)
    except requests.Timeout as e:
        log_response()
        raise TimeoutError(f'PubChem lookup timed out for "{name}"') from e
    except requests.RequestException as e:
        log_response()
        raise ConnectionError(f'Unable to reach PubChem while looking up "{name}"') from e

    if response.status_code == 404:
        log_response(response)
        raise ValueError(f'Chemical name not found in PubChem: "{name}"')
    if response.status_code != 200:
        log_response(response)
        raise ConnectionError(f'PubChem returned HTTP {response.status_code} for "{name}"')

    try:
        data = response.json()
        props = data['PropertyTable']['Properties'][0]
        smiles = props.get('ConnectivitySMILES') or props.get('CanonicalSMILES')
        if not smiles:
            raise KeyError('No SMILES field present in PubChem response')
        return smiles
    except (ValueError, KeyError, IndexError, TypeError) as e:
        log_response(response)
        raise ValueError(f'Chemical name not found in PubChem: "{name}"') from e


@app.route('/api/name-to-smiles', methods=['POST'])
def resolve_name_to_smiles():
    """Resolve a chemical name through PubChem and return its SMILES."""
    data = request.get_json() or {}
    name = data.get('name', '').strip()

    if not name:
        return jsonify({'error': 'No chemical name provided'}), 400

    try:
        smiles = name_to_smiles(name)
        return jsonify({'smiles': smiles, 'name': name}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except TimeoutError as e:
        return jsonify({'error': str(e)}), 504
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def fetch_ddinter_interaction(id_a: str, id_b: str) -> dict | None:
    """Fetch a direct DDInter interaction record for two DDInter IDs."""
    url = f"https://ddinter.scbdd.com/ddinter/grapher-datasource/{id_a}/"
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/153.0.0.0 Safari/537.36'
        ),
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': f'https://ddinter.scbdd.com/ddinter/drug-detail/{id_a}/',
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            app.logger.warning('DDInter returned HTTP %s for %s', response.status_code, id_a)
            return None
        data = response.json()
        if not isinstance(data, dict):
            app.logger.warning('DDInter returned an unexpected JSON object for %s', id_a)
            return None
        interactions = data.get('interactions', [])
        if not isinstance(interactions, list):
            app.logger.warning('DDInter returned an invalid interactions list for %s', id_a)
            return None
        for interaction in interactions:
            if not isinstance(interaction, dict):
                continue
            if str(interaction.get('id')) == str(id_b):
                return {
                    'drug_id': interaction.get('id'),
                    'name': interaction.get('name'),
                    'level': interaction.get('level', []),
                    'actions': interaction.get('actions', []),
                }
    except (requests.RequestException, ValueError, TypeError) as e:
        app.logger.warning('DDInter lookup failed for %s -> %s: %s', id_a, id_b, e)
    return None


def _ddinter_categories(entry: dict) -> list:
    """Return human-readable labels for active DDInter mechanism flags."""
    actions = entry.get('actions', [])
    if isinstance(actions, str):
        actions = [actions]
    action_labels = {
        'synergy': 'synergistic effect',
        'synergistic_effect': 'synergistic effect',
        'antagonism': 'antagonistic effect',
        'antagonistic_effect': 'antagonistic effect',
        'metabolism': 'metabolic interaction',
        'absorption': 'absorption interaction',
        'distribution': 'distribution interaction',
        'excretion': 'excretion interaction',
        'others': 'other reported mechanism',
    }
    categories = [action_labels.get(str(action), str(action)) for action in actions if action]
    if categories:
        return categories

    category_labels = {
        'synergistic_effect': 'synergistic effect',
        'antagonistic_effect': 'antagonistic effect',
        'metabolism': 'metabolic interaction',
        'absorption': 'absorption interaction',
        'distribution': 'distribution interaction',
        'excretion': 'excretion interaction',
        'others': 'other reported mechanism',
    }
    return [label for key, label in category_labels.items() if str(entry.get(key)) == '1']


def generate_ollama_summary(name_a: str, name_b: str, entry: dict) -> str:
    """Generate a constrained plain-language summary from a DDInter record."""
    categories = _ddinter_categories(entry)
    category_text = ', '.join(categories) if categories else 'no specific mechanism categories listed'
    levels = entry.get('level', [])
    if isinstance(levels, str):
        levels = [levels]
    level_text = ', '.join(str(level) for level in levels if level) or 'not specified'
    frequency = entry.get('frequency')
    frequency_text = f' Frequency count: {frequency}.' if frequency is not None else ''
    prompt = (
        f"DDInter confirms an interaction between {name_a} and {name_b}. "
        f"Reported severity: {level_text}. "
        f"Confirmed mechanism categories: {category_text}.{frequency_text}\n\n"
        "Only describe what is stated above. Do not add any other pharmacological claims, "
        "dosing advice, or medical recommendations not directly supported by the given "
        "categories. Write 2-3 plain, factual sentences for a general audience."
    )

    try:
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={'model': OLLAMA_MODEL, 'prompt': prompt, 'stream': False},
            timeout=30,
        )
        response.raise_for_status()
        summary = response.json()['response'].strip()
        if not summary:
            raise ValueError('Ollama returned an empty summary.')
        return summary
    except (requests.RequestException, ValueError, KeyError, TypeError) as e:
        raise ConnectionError(
            'Could not reach local Ollama server at localhost:11434 -- is it running?'
        ) from e


@app.route('/api/interaction-summary', methods=['POST'])
def interaction_summary():
    """Return a DDInter-backed Ollama summary for a drug pair."""
    try:
        data = request.get_json() or {}
        name_a = data.get('name_a', '').strip()
        name_b = data.get('name_b', '').strip()

        if not name_a or not name_b:
            return jsonify({'error': 'Both name_a and name_b are required.'}), 400

        id_a = DDINTER_NAME_INDEX.get(name_a.lower())
        id_b = DDINTER_NAME_INDEX.get(name_b.lower())
        missing_names = [name for name, identifier in ((name_a, id_a), (name_b, id_b)) if not identifier]
        if missing_names:
            failed = ' and '.join(f'"{name}"' for name in missing_names)
            return jsonify({
                'available': False,
                'reason': f'No DDInter record found for {failed}. Summary unavailable for this pair.'
            }), 200

        entry = fetch_ddinter_interaction(id_a, id_b)
        if entry is None:
            return jsonify({
                'available': False,
                'reason': "These two drugs were found in DDInter individually, but no direct interaction record exists between them in DDInter's database."
            }), 200

        try:
            summary = generate_ollama_summary(name_a, name_b, entry)
        except ConnectionError as e:
            return jsonify({'available': False, 'reason': str(e)}), 200

        return jsonify({
            'available': True,
            'summary': summary,
            'categories': _ddinter_categories(entry),
            'frequency': entry.get('frequency'),
            'source': 'DDInter',
            'license': 'CC BY-NC-SA 4.0',
            'source_url': f'https://ddinter.scbdd.com/ddinter/drug-detail/{id_a}/'
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Return metrics CSV content if available."""
    metrics_path = os.path.join('results', 'metrics.csv')
    if os.path.exists(metrics_path):
        import pandas as pd
        df = pd.read_csv(metrics_path)
        return jsonify(df.to_dict(orient='records'))
    else:
        return jsonify({'message': 'Metrics not evaluated yet. Run evaluate.py first.'})


if __name__ == '__main__':
    print("Pre-loading GNN model suite (GCN, GIN, MPNN)...")
    for a in ['gcn', 'gin', 'mpnn']:
        load_or_train_default_model(a)

    print("\n=======================================================")
    print(" GNN Toxicity Web Dashboard Server Ready!")
    print(" Running at http://127.0.0.1:5000")
    print("=======================================================\n")
    app.run(host='127.0.0.1', port=5000, debug=True, threaded=True)