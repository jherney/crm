export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        neon: '#5eead4',
        glow: '#22d3ee',
        panel: 'rgba(15, 23, 42, 0.72)'
      },
      boxShadow: {
        neon: '0 0 0 1px rgba(34,211,238,0.2), 0 0 40px rgba(34,211,238,0.16)'
      }
    }
  },
  plugins: []
};
