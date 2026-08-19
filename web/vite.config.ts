import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Base path for GitHub Pages project site: https://<user>.github.io/Finta_tipster/
// Override with BASE_PATH=/ for local root deploys.
export default defineConfig({
  plugins: [react()],
  base: process.env.BASE_PATH ?? "/Finta_tipster/",
});
