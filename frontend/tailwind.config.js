module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#0c0d1b",
        "canvas-subtle": "#0e1026",
        surface: "#13152c",
        paper: "#13152c",
        "paper-glass": "rgba(19, 21, 44, 0.8)",
        ink: "#FFFFFF",
        muted: "#94A3B8",
        line: "rgba(255, 255, 255, 0.1)",
        quiet: "rgba(255, 255, 255, 0.06)",
        accent: "#FF7A00",
        "accent-dark": "#FF4500",
        "brand-orange": "#FF7A00",
        "brand-orange-dark": "#FF4500",
        success: "#10B981",
        warning: "#F59E0B",
        danger: "#F43F5E"
      },
      fontFamily: {
        sans: ["IBM Plex Sans", "Inter", "system-ui", "sans-serif"],
        serif: ["IBM Plex Serif", "Georgia", "serif"]
      },
      maxWidth: {
        site: "76rem"
      },
      boxShadow: {
        restrained: "0 12px 30px rgba(0, 0, 0, 0.3)",
        "glow-orange": "0 0 25px rgba(255, 107, 0, 0.35)",
        "glow-purple": "0 0 30px rgba(168, 85, 247, 0.25)",
        glass: "0 20px 50px rgba(0, 0, 0, 0.4)"
      },
      backgroundImage: {
        "cta-gradient": "linear-gradient(to right, #FF7A00, #FF4500)",
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "ambient-glow": "radial-gradient(circle at 50% 0%, rgba(168, 85, 247, 0.15), rgba(236, 72, 153, 0.08) 50%, transparent 80%)"
      }
    }
  },
  plugins: []
};
