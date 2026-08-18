import { defineConfig } from "vite";

export default defineConfig({
  base: "/pilot/",
  server: {
    host: "0.0.0.0",
    port: 4173,
    proxy: {
      "/v1": "http://127.0.0.1:8000",
      "/healthz": "http://127.0.0.1:8000",
    },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
});
