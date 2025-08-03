/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_SENTRY_ENV:
    | "localhost"
    | "development"
    | "staging"
    | "production"
    | "production_jp-bank"
    | "production_jsbank"
    | "production_ibk"
    | "production_nrtas-ana"
    | "production_sbis-bank"
    | "production_kyuden"
    | "production_oss-bank";
  readonly VITE_AUTH0_DOMAIN: string;
  readonly VITE_AUTH0_CLIENT_ID: string;
  readonly VITE_AUTH0_AUDIENCE: string;
  readonly VITE_EXTERNAL_API_URL: string;
  readonly VITE_API_BASE_URL: string;
  readonly VITE_APP_BASE_URL: string;
  readonly VITE_ADMINISTRATOR_API_BASE_URL: string;
  readonly VITE_LAUNCH_DARKLY_CLIENT_SIDE_ID: string;
  readonly VITE_SENTRY_DSN: string;
  readonly VITE_SENTRY_AUTH_TOKEN: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
