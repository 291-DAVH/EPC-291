import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Admin console. Same API proxy as the web app, on its own port. Run the API with EPC_ROLE=admin.
export default defineConfig({
  plugins: [react()],
  server: { port: 5174, proxy: { "/api": "http://127.0.0.1:8000" } },
});
