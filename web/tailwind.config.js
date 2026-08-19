/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0f1117",
        card: "#1a1d27",
        card2: "#22252f",
        border: "#2a2d3a",
        border2: "#363945",
        text: "#e4e6eb",
        dim: "#8b8e98",
        dimmer: "#5a5d68",
        good: "#00d97e",
        warn: "#ffc107",
        bad: "#f44336",
        accent: "#6c5ce7",
        info: "#3b82f6",
      },
    },
  },
  plugins: [],
};
