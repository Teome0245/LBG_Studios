import { cpSync, existsSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";

const STATIC_DIRS = ["orchestrator_avatar", "office_map", "face_rig", "brain_3d", "assets"];
const configDir = fileURLToPath(new URL(".", import.meta.url));

function copyPilotStaticAssets() {
  return {
    name: "copy-pilot-static-assets",
    closeBundle() {
        const root = configDir;
      const dist = resolve(root, "dist");
      for (const name of STATIC_DIRS) {
        const from = resolve(root, name);
        if (existsSync(from)) {
          cpSync(from, resolve(dist, name), { recursive: true });
        }
      }
    },
  };
}

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
  plugins: [copyPilotStaticAssets()],
});
