/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_APP_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

declare module '*.css';
declare module '*.svg';
declare module '*.png';
declare module '*.jpg';
declare module '*.jpeg';
