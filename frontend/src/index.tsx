import "./index.css";

import { Auth0Provider } from "@auth0/auth0-react";
import { ThemeProvider } from "@mui/material";
import { LocalizationProvider } from "@mui/x-date-pickers";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import * as Sentry from "@sentry/react";
import React from "react";
import ReactDOM from "react-dom/client";
import { SWRConfig } from "swr";

import App from "./App";
import { CustomSnackbarProvider } from "./contexts/SnackbarContext";
import { theme } from "./theme";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    {/* TODO: ErrorFallback を定義する */}
    <Sentry.ErrorBoundary fallback={<p>予期しないエラーが発生しました。</p>}>
      <Auth0Provider
        domain={import.meta.env.VITE_AUTH0_DOMAIN}
        clientId={import.meta.env.VITE_AUTH0_CLIENT_ID}
        authorizationParams={{
          audience: import.meta.env.VITE_AUTH0_AUDIENCE,
          redirect_uri: window.location.origin,
        }}
      >
        <SWRConfig
          value={{
            revalidateOnFocus: false,
          }}
        >
          <ThemeProvider theme={theme}>
            <LocalizationProvider dateAdapter={AdapterDayjs}>
              <CustomSnackbarProvider>
                <App />
              </CustomSnackbarProvider>
            </LocalizationProvider>
          </ThemeProvider>
        </SWRConfig>
      </Auth0Provider>
    </Sentry.ErrorBoundary>
  </React.StrictMode>,
);
