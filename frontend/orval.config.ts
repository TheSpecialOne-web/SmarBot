import { defineConfig } from "orval";

export default defineConfig({
  api: {
    input: {
      target: "../backend/api/controllers/api/openapi/openapi.yml",
    },
    output: {
      target: "./src/orval/api.ts",
      schemas: "./src/orval/models/api",
      client: "swr",
      override: {
        mutator: {
          path: "./src/libs/api/mutator.ts",
          name: "useMutator",
        },
      },
    },
    hooks: {
      afterAllFilesWrite: ["prettier --write ./src/orval"],
    },
  },
  "backend-api": {
    input: {
      target: "../backend/api/controllers/backend_api/openapi/openapi.yml",
    },
    output: {
      target: "./src/orval/backend-api.ts",
      schemas: "./src/orval/models/backend-api",
      client: "swr",
      override: {
        mutator: {
          path: "./src/libs/mutator.ts",
          name: "useMutator",
        },
      },
    },
    hooks: {
      afterAllFilesWrite: ["prettier --write ./src/orval"],
    },
  },
  "administrator-api": {
    input: {
      target: "../backend/api/controllers/administrator_api/openapi/openapi.yml",
    },
    output: {
      target: "./src/orval/administrator-api.ts",
      schemas: "./src/orval/models/administrator-api",
      client: "swr",
      override: {
        mutator: {
          path: "./src/libs/administrator/mutator.ts",
          name: "useMutator",
        },
      },
    },
    hooks: {
      afterAllFilesWrite: ["prettier --write ./src/orval"],
    },
  },
});
