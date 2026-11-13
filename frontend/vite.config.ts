import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// En desarrollo (npm run dev) el proxy envía /api al backend local.
// En la VM no se usa: allí nginx cumple ese papel (ver nginx.conf).
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
