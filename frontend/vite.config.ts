import { defineConfig } from "vite";
import eslint from "vite-plugin-eslint";
import react from "@vitejs/plugin-react";
import tailwindcss from "tailwindcss";
export default defineConfig(() => {
  return {
    build: {
      outDir: "build"
    },
    server: {
      port: 8080
    },
    plugins: [react(), eslint()],
    css: {
      postcss: {
        plugins: [tailwindcss()]
      }
    }
  };
});
