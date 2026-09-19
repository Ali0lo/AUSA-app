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
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" }
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" }
        },
        slideDown: {
          "0%": { opacity: "0", transform: "translateY(-16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" }
        },
        scaleIn: {
          "0%": { opacity: "0", transform: "scale(0.96)" },
          "100%": { opacity: "1", transform: "scale(1)" }
        },
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-6px)" }
        },
        floatSlow: {
          "0%, 100%": { transform: "translate(0px, 0px) scale(1)" },
          "50%": { transform: "translate(12px, -12px) scale(1.05)" }
        },
        pulseGlow: {
          "0%, 100%": { opacity: "0.6", transform: "scale(1)" },
          "50%": { opacity: "1", transform: "scale(1.02)" }
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" }
        }
      },
      animation: {
        "fade-in": "fadeIn 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards",
        "slide-up": "slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards",
        "slide-down": "slideDown 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards",
        "scale-in": "scaleIn 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards",
        float: "float 4s ease-in-out infinite",
        "float-slow": "floatSlow 8s ease-in-out infinite",
        "pulse-glow": "pulseGlow 3s ease-in-out infinite",
        shimmer: "shimmer 3s ease-in-out infinite"
      }
    }
  },
  plugins: []
};
