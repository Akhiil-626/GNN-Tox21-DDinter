"""
Flask Web Application Server for Interactive Molecular Toxicity Prediction.
Provides REST API endpoints for live SMILES inference, atom saliency rendering, and metrics overview.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import time
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
import requests
import torch
from flask import Flask, request, jsonify, send_from_directory
from torch_geometric.data import Batch

from src.featurize import smiles_to_graph
from src.dataset import TOX21_TASKS, Tox21GraphDataset
from src.ddi_model import DualEncoderDDI
from src.ddi_inference import PairRiskExplainer, SymmetricPredictor, find_available_variant
from src.model import get_model, MPNNModel
from src.visualize import compute_atom_saliency, render_molecule_svg
from src.train import train_gnn
from src.ddinter_lookup import (
    build_ddinter_index,
    load_ddinter,
    lookup_pair,
    resolve_input,
    distribution,
    similar_drugs,
    build_analogues,
)

app = Flask(__name__, static_folder='../public', static_url_path='')

# Change this to the model name installed locally with `ollama pull <model>`.
OLLAMA_MODEL = "llama3"

# Global cache for loaded GNN models
LOADED_MODELS = {}
LOADED_DDI_MODELS = {}
SYMMETRIC_PREDICTORS = {}          # arch -> SymmetricPredictor | None (None = not available, don't retry)
RISK_EXPLAINER = PairRiskExplainer(arch='gcn')


def get_symmetric_predictor(arch: str):
    """
    Return the order-independent, abstain-capable DDI predictor for `arch`, or None when no
    trained checkpoint exists (the app then falls back to the original DualEncoderDDI model).
    Created once and cached; a failed load is remembered so requests don't retry it.
    """
    arch = arch.lower()
    if arch in SYMMETRIC_PREDICTORS:
        return SYMMETRIC_PREDICTORS[arch]
    predictor = None
    try:
        variant = find_available_variant(arch)
        if variant is not None:
            predictor = SymmetricPredictor(variant, arch, explainer=RISK_EXPLAINER)
            print(f"Loaded symmetric DDI model (variant {variant}, {arch.upper()}).")
    except Exception as e:
        print(f"Symmetric DDI model unavailable for {arch}: {e}")
        predictor = None
    SYMMETRIC_PREDICTORS[arch] = predictor
    return predictor

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
        if not os.path.exists(csv_path):
            continue
        try:
            frame = pd.read_csv(csv_path)
            for d_a, id_a, d_b, id_b in zip(
                frame['Drug_A'], frame['DDInterID_A'], frame['Drug_B'], frame['DDInterID_B']
            ):
                if pd.notna(d_a) and pd.notna(id_a):
                    index[str(d_a).strip().lower()] = str(id_a).strip()
                if pd.notna(d_b) and pd.notna(id_b):
                    index[str(d_b).strip().lower()] = str(id_b).strip()
        except Exception:
            pass
    return index


DDINTER_NAME_INDEX = build_ddinter_name_index()

try:
    DDINTER_DATA = load_ddinter()
    if DDINTER_DATA is not None:
        print(f"Indexed {len(DDINTER_DATA.pair_levels)} DDInter drug-drug interaction pairs.")
        DDINTER_PAIR_INDEX = DDINTER_DATA
    else:
        print("Warning: DDInter dataset could not be loaded (missing files).")
        DDINTER_DATA = None
        DDINTER_PAIR_INDEX = None
except Exception as e:
    print(f"Warning: Failed to load DDInter dataset: {e}")
    DDINTER_DATA = None
    DDINTER_PAIR_INDEX = None


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

        labels = {0: 'Minor', 1: 'Moderate', 2: 'Major'}
        decision = None
        sym = None
        try:
            sym = get_symmetric_predictor(arch)
        except Exception:
            sym = None

        if sym is not None:
            try:
                sres = sym.predict(smiles_a, smiles_b)
                probs_list = sres['probabilities']
                predicted_class = sres['argmax']
                decision = {
                    'answered': sres['answered'],
                    'prediction_set': sres['prediction_set'],
                    'coverage_target': sres['coverage_target'],
                    'model_variant': sres['variant'],
                }
            except Exception as e:
                print(f"Symmetric predictor error, falling back to DualEncoder: {e}")
                sym = None

        if sym is None:
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
            probs_list = [float(p) for p in probabilities.cpu().tolist()]

        predicted_severity = labels[predicted_class]

        risk_overlap = None
        try:
            risk_overlap = RISK_EXPLAINER.explain(smiles_a, smiles_b)
        except Exception:
            risk_overlap = None

        try:
            record = lookup_pair(DDINTER_PAIR_INDEX, smiles_a, smiles_b)
            agrees = (predicted_severity in record.get('all_levels', [])) if record.get('status') == 'match' else None
            ddinter_record = {
                'status': record.get('status', 'unavailable'),
                'level': record.get('level'),
                'all_levels': record.get('all_levels', []),
                'agrees_with_prediction': agrees
            }
        except Exception:
            ddinter_record = {
                'status': 'unavailable',
                'level': None,
                'all_levels': [],
                'agrees_with_prediction': None
            }

        out = {
            'predicted_severity': predicted_severity,
            'probabilities': {
                labels[idx]: float(probs_list[idx])
                for idx in range(3)
            },
            'smiles_a': smiles_a,
            'smiles_b': smiles_b,
            'name_a': name_a,
            'name_b': name_b,
            'arch': arch.upper(),
            'ddinter_record': ddinter_record,
        }
        if decision is not None:
            out['decision'] = decision
        if risk_overlap is not None:
            out['risk_overlap'] = risk_overlap

        return jsonify(out)

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
    
    id_a = DDINTER_NAME_INDEX.get(name_a.lower())
    id_b = DDINTER_NAME_INDEX.get(name_b.lower())
    print(f"DEBUG: name_a='{name_a}' -> id_a={id_a}")
    print(f"DEBUG: name_b='{name_b}' -> id_b={id_b}")

    entry = fetch_ddinter_interaction(id_a, id_b)
    print(f"DEBUG: entry found (a->b): {entry}")

    if entry is None:
        entry_reverse = fetch_ddinter_interaction(id_b, id_a)
        print(f"DEBUG: entry found (b->a): {entry_reverse}")


def _query_ddinter_page(
    drug_id: str,
    session: requests.Session,
    max_retries: int = 2,
) -> tuple[list | None, int]:
    """Fetch one drug's DDInter interaction page with DataTables parameters."""
    detail_url = f"https://ddinter.scbdd.com/ddinter/drug-detail/{drug_id}/"
    visited_pages = getattr(session, '_ddinter_visited_detail_pages', set())
    if drug_id not in visited_pages:
        try:
            session.get(detail_url, timeout=10)
        except requests.RequestException as e:
            print(f"DDInter detail page request failed for {drug_id}: {e}")
        visited_pages.add(drug_id)
        session._ddinter_visited_detail_pages = visited_pages

    session.headers.update({"Referer": detail_url})
    params = {
        "draw": 1,
        "start": 0,
        "length": 500,
        "search[value]": "",
        "search[regex]": "false",
        "order[0][column]": 0,
        "order[0][dir]": "asc",
        "columns[0][data]": "drug_id",
        "columns[0][searchable]": "true",
        "columns[0][orderable]": "true",
    }

    last_status_code = 0
    for attempt in range(1, max_retries + 2):
        try:
            response = session.get(
                f"https://ddinter.scbdd.com/ddinter/interact-with/{drug_id}/",
                params=params,
                timeout=10,
            )
            last_status_code = response.status_code
            print(f"DDInter interact-with attempt {attempt} for {drug_id}: {last_status_code}")
            if last_status_code == 200:
                try:
                    data = response.json()
                    rows = data.get('data')
                    if isinstance(rows, list):
                        return rows, last_status_code
                except (ValueError, AttributeError):
                    pass
        except requests.RequestException as e:
            last_status_code = getattr(getattr(e, 'response', None), 'status_code', 0) or 0
            print(f"DDInter interact-with attempt {attempt} for {drug_id}: {last_status_code}")

        if attempt <= max_retries:
            time.sleep(1.5)

    return None, last_status_code


def fetch_ddinter_interaction(
    id_a: str,
    id_b: str,
    max_retries: int = 2,
) -> tuple[dict | None, str]:
    """Find a DDInter record in either drug's interaction list."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json, text/javascript, */*; q=0.01",
    })

    try:
        rows_a, _ = _query_ddinter_page(id_a, session, max_retries)
        if rows_a is None:
            return None, "service_unavailable"
        for entry in rows_a:
            if str(entry.get('drug_id')) == str(id_b):
                return entry, "found"

        rows_b, _ = _query_ddinter_page(id_b, session, max_retries)
        if rows_b is None:
            return None, "service_unavailable"
        for entry in rows_b:
            if str(entry.get('drug_id')) == str(id_a):
                return entry, "found"

        return None, "not_found"
    finally:
        session.close()


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

        entry, status = fetch_ddinter_interaction(id_a, id_b)
        if status == 'not_found':
            return jsonify({
                'available': False,
                'reason': "These two drugs were found in DDInter individually, but no direct interaction record exists between them in DDInter's database."
            }), 200
        if status == 'service_unavailable':
            return jsonify({
                'available': False,
                'reason': "DDInter's interaction lookup service is temporarily unavailable or rate-limited. Please try again in a moment."
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


def predict_pair_severity(smiles_a: Optional[str], smiles_b: Optional[str], arch: str = 'gcn') -> Optional[Dict[str, Any]]:
    """
    Run DDI severity model inference for two SMILES strings without network lookups.
    Returns predicted label and class probabilities, or None on any featurization/inference error.
    """
    if not smiles_a or not smiles_b:
        return None
    try:
        graph_a = smiles_to_graph(smiles_a)
        graph_b = smiles_to_graph(smiles_b)
        if graph_a is None or graph_b is None:
            return None

        labels = {0: 'Minor', 1: 'Moderate', 2: 'Major'}
        sym = None
        try:
            sym = get_symmetric_predictor(arch)
        except Exception:
            sym = None

        decision = None
        sym_result = None
        if sym is not None:
            try:
                sym_result = sym.predict(smiles_a, smiles_b)
                probs_list = sym_result['probabilities']
                predicted_class = sym_result['argmax']
                decision = {
                    'answered': sym_result['answered'],
                    'prediction_set': sym_result['prediction_set'],
                    'coverage_target': sym_result['coverage_target'],
                    'model_variant': sym_result['variant']
                }
            except Exception:
                sym = None

        if sym is None:
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
            probs_list = [float(p) for p in probabilities.cpu().tolist()]

        risk_overlap = None
        try:
            risk_overlap = RISK_EXPLAINER.explain(smiles_a, smiles_b)
        except Exception:
            risk_overlap = None

        res = {
            'label': labels[predicted_class],
            'probabilities': {
                labels[idx]: float(probs_list[idx])
                for idx in range(3)
            }
        }
        if decision is not None:
            res['decision'] = decision
        if risk_overlap is not None:
            res['risk_overlap'] = risk_overlap
        return res
    except Exception:
        return None


@app.route('/api/pair-risk', methods=['POST'])
def pair_risk():
    """
    "Why is this pair risky?" -- shared predicted-toxicity profile for two drugs.
    Body: {"name_a": ..., "name_b": ...} or {"smiles_a": ..., "smiles_b": ...}.
    The score is a research signal derived from lab-assay predictions, not a clinical verdict.
    """
    data = request.get_json() or {}
    try:
        smiles_a = (data.get('smiles_a') or '').strip() or name_to_smiles((data.get('name_a') or '').strip())
        smiles_b = (data.get('smiles_b') or '').strip() or name_to_smiles((data.get('name_b') or '').strip())
    except (ValueError, ConnectionError, TimeoutError) as e:
        return jsonify({'error': str(e)}), 400

    try:
        result = RISK_EXPLAINER.explain(smiles_a, smiles_b)
    except Exception as e:
        return jsonify({'error': f'Risk-profile computation failed: {e}'}), 500
    if result is None:
        return jsonify({
            'error': 'Risk profiles are unavailable.',
            'reason': getattr(RISK_EXPLAINER, 'unavailable_reason', None) or 'One of the molecules could not be parsed.',
        }), 503
    return jsonify({'smiles_a': smiles_a, 'smiles_b': smiles_b, 'risk_overlap': result})


@app.route('/api/ddinter/suggest', methods=['GET'])
def suggest_drugs():
    """
    Autocomplete drug names from DDInter dataset.
    Requires at least 3 characters; returns up to 8 matches prioritizing prefix matches.
    """
    q = request.args.get('q', '').strip()
    if len(q) < 3 or DDINTER_DATA is None:
        return jsonify({'suggestions': []})

    q_lower = q.lower()
    prefix_matches = []
    substring_matches = []

    for d_id, d_name in DDINTER_DATA.id_to_name.items():
        name_lower = d_name.lower()
        if name_lower.startswith(q_lower):
            prefix_matches.append({'name': d_name, 'id': d_id})
        elif q_lower in name_lower:
            substring_matches.append({'name': d_name, 'id': d_id})

    prefix_matches.sort(key=lambda x: (len(x['name']), x['name']))
    substring_matches.sort(key=lambda x: (len(x['name']), x['name']))

    combined = prefix_matches + substring_matches
    seen = set()
    suggestions = []
    for item in combined:
        if item['id'] not in seen:
            seen.add(item['id'])
            suggestions.append(item)
            if len(suggestions) >= 8:
                break

    return jsonify({'suggestions': suggestions})


@app.route('/api/check-prescription', methods=['POST'])
def check_prescription():
    """
    Evaluate multi-drug prescriptions (2 to 5 drugs) against DDInter records and GNN models.
    Returns per-drug resolutions, pairwise interactions, and structural analogues.
    """
    data = request.get_json() or {}
    names = data.get('names')
    arch = data.get('arch', 'gcn').lower()

    if not isinstance(names, list) or len(names) < 2 or len(names) > 5:
        return jsonify({'error': 'Prescription check requires between 2 and 5 drug names.'}), 400

    for idx, raw_n in enumerate(names):
        if not isinstance(raw_n, str) or not raw_n.strip():
            return jsonify({'error': f'Drug name at position {idx + 1} cannot be empty.'}), 400

    resolved_drugs = []
    warnings_list = []
    seen_ids = set()
    seen_smiles = set()

    # Sequential resolution loop (never hits PubChem in parallel)
    for raw_n in names:
        drug_res = resolve_input(DDINTER_DATA, raw_n, resolver=name_to_smiles)
        d_id = drug_res.get('ddinter_id')
        d_smiles = drug_res.get('smiles')

        if d_id:
            if d_id in seen_ids:
                return jsonify({
                    'error': f'Duplicate drug detected: "{raw_n}" resolves to the same DDInter drug ({d_id}) as another input.'
                }), 400
            seen_ids.add(d_id)

        if d_smiles:
            if d_smiles in seen_smiles:
                return jsonify({
                    'error': f'Duplicate chemical structure detected: "{raw_n}" resolves to the same molecule as another input.'
                }), 400
            seen_smiles.add(d_smiles)

        dist = distribution(DDINTER_DATA, d_id)
        drug_res['distribution'] = dist
        resolved_drugs.append(drug_res)

        if drug_res['resolved_via'] == 'unresolved':
            warnings_list.append(f"Could not resolve '{raw_n}' via DDInter or PubChem.")
        elif drug_res['resolved_via'] == 'pubchem_only':
            warnings_list.append(f"'{raw_n}' was resolved via PubChem, but is not documented in DDInter.")

    pairs_list = []
    n_drugs = len(resolved_drugs)
    for i in range(n_drugs):
        for j in range(i + 1, n_drugs):
            drug_a = resolved_drugs[i]
            drug_b = resolved_drugs[j]

            id_a = drug_a.get('ddinter_id')
            id_b = drug_b.get('ddinter_id')
            smiles_a = drug_a.get('smiles')
            smiles_b = drug_b.get('smiles')

            record = lookup_pair(DDINTER_DATA, id_a, id_b)
            model_res = predict_pair_severity(smiles_a, smiles_b, arch=arch)

            analogues_obj = None
            if record.get('status') == 'not_recorded':
                analogues_obj = build_analogues(DDINTER_DATA, id_a, id_b)

            details_url = None
            if record.get('status') in ('match', 'unknown_severity') and id_a:
                details_url = f"https://ddinter.scbdd.com/ddinter/drug-detail/{id_a}/"

            pairs_list.append({
                'a': i,
                'b': j,
                'record': record,
                'model': model_res,
                'analogues': analogues_obj,
                'details_url': details_url,
            })

    return jsonify({
        'drugs': resolved_drugs,
        'pairs': pairs_list,
        'warnings': warnings_list,
    }), 200


if __name__ == '__main__':
    print("Pre-loading GNN model suite (GCN, GIN, MPNN)...")
    for a in ['gcn', 'gin', 'mpnn']:
        load_or_train_default_model(a)

    print("\n=======================================================")
    print(" GNN Toxicity Web Dashboard Server Ready!")
    print(" Running at http://127.0.0.1:5000")
    print("=======================================================\n")
    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False, threaded=True)