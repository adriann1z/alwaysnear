import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        cream: "#fff7ed",
        skysoft: "#dff3ff",
        lavender: "#ebe4ff",
        ink: "#253044",
        meadow: "#dff5e7",
        emergency: "#dc2626"
      },
      boxShadow: {
        soft: "0 24px 80px rgba(63, 76, 105, 0.12)"
      }
    }
  },
  plugins: [require("tailwindcss-animate")]
};

export default config;
