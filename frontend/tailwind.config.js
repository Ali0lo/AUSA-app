module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#F4F1EA",
        paper: "#FFFDFC",
        ink: "#1F211E",
        muted: "#5F625D",
        line: "#8C8A82",
        quiet: "#D6D1C7",
        accent: "#A64F27",
        "accent-dark": "#8A3F20",
        success: "#3F6B55",
        warning: "#9A6A20",
        danger: "#A13D32"
      },
      fontFamily: {
        sans: ["IBM Plex Sans", "Arial", "sans-serif"],
        serif: ["IBM Plex Serif", "Georgia", "serif"]
      },
      maxWidth: {
        site: "76rem"
      },
      boxShadow: {
        restrained: "0 12px 30px rgba(31, 33, 30, 0.08)"
      }
    }
  },
  plugins: []
};
