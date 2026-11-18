import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// En desarrollo, el proxy imita a Nginx (REQ-F-009: el bundle solo usa rutas relativas).
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api/a": { target: "http://localhost:8000", rewrite: (p) => p.replace(/^\/api\/a/, "") },
      "/api/b": { target: "http://localhost:3000", rewrite: (p) => p.replace(/^\/api\/b/, "") },
    },
  },
});
