export const APP_URL = import.meta.env.VITE_APP_URL ?? '../index.html';

export const MODULE_LINKS = {
  screening: APP_URL + '#screen',
  interactions: APP_URL + '#interact',
  prescription: APP_URL + '#rx-panel',
  performance: APP_URL + '#performance',
};

export const GITHUB_URL = ''; // hide every GitHub link while empty
