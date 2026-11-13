import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "node:path";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const previewHost = env.__VITE_ADDITIONAL_SERVER_ALLOWED_HOSTS;

  return {
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: { "@": path.resolve(__dirname, "./src") },
    },
    server: {
      host: "0.0.0.0",
      port: 3000,
      strictPort: true,
      allowedHosts: previewHost ? [previewHost] : undefined,
      proxy: {
        "/api": { target: "http://127.0.0.1:8000", changeOrigin: true },
        "/ws": { target: "ws://127.0.0.1:8000", ws: true, changeOrigin: true },
      },
    },
    test: {
      environment: "jsdom",
      globals: true,
      setupFiles: ["./tests/setup.ts"],
      css: false,
    },
  };
});
