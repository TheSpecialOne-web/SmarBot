import { sentryVitePlugin } from "@sentry/vite-plugin";
import react from "@vitejs/plugin-react";
import dotenv from "dotenv";
import { defineConfig } from "vite";
import tsconfigPaths from "vite-tsconfig-paths";

const IGNORE_WARNING_CODES = ["MODULE_LEVEL_DIRECTIVE", "SOURCEMAP_ERROR"];

dotenv.config({ path: ".env" });

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tsconfigPaths(),
    sentryVitePlugin({
      org: "neoai-inc",
      project: "neoai-chat-frontend",
      authToken: process.env.VITE_SENTRY_AUTH_TOKEN,
      telemetry: false,
      sourcemaps: {
        assets: ["./dist/**"],
        ignore: ["./node_modules/**"],
        filesToDeleteAfterUpload: ["./dist/**/*.js.map"],
      },
    }),
  ],
  build: {
    outDir: "./dist",
    emptyOutDir: true,
    sourcemap: true,
    rollupOptions: {
      onwarn: (warning, warn) => {
        if (warning.code && IGNORE_WARNING_CODES.includes(warning.code)) {
          return;
        }
        warn(warning);
      },
    },
  },
  server: {
    port: 3000,
  },
});
