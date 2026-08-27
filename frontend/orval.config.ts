import { defineConfig } from "orval";

export default defineConfig({
  astroimage: {
    input: {
      target: "../backend/openapi.json",
    },
    output: {
      mode: "tags-split",
      target: "./src/api/generated/endpoints.ts",
      schemas: "./src/api/generated/model",
      client: "react-query",
      httpClient: "fetch",
      clean: true,
      override: {
        mutator: {
          path: "./src/lib/api-client.ts",
          name: "customFetch",
        },
      },
    },
  },
});
