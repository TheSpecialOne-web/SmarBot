import * as Sentry from "@sentry/react";

const APP_ENV = import.meta.env.VITE_SENTRY_ENV ?? "localhost";

Sentry.init({
  enabled: APP_ENV !== "localhost",
  dsn: "https://af70207f31f4d421138d4c4439dad10e@o4507856054779904.ingest.us.sentry.io/4507856063234048",
  environment: APP_ENV,
  integrations: [
    Sentry.browserTracingIntegration(),
    Sentry.browserProfilingIntegration(),
    Sentry.replayIntegration(),
  ],
  tracesSampleRate: 1.0,
  tracePropagationTargets: [
    import.meta.env.VITE_API_BASE_URL,
    import.meta.env.VITE_ADMINISTRATOR_API_BASE_URL,
  ],
  profilesSampleRate: 1.0,
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,
});
