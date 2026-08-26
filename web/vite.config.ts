import path from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Base defaults to "/" (Vercel serves the app at the domain root).
// Override with BASE_PATH for sub-path hosting (e.g. GitHub Pages).
export default defineConfig({
  plugins: [react()],
  base: process.env.BASE_PATH ?? "/",
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
