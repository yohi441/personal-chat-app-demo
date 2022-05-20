const plugin = require('tailwindcss/plugin')

module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/js/**/*.js",
  ],
  theme: {
    extend: {},
  },
  plugins: [
    require('@tailwindcss/typography'),
    require('@tailwindcss/forms'),
    require('@tailwindcss/line-clamp'),
    require('@tailwindcss/aspect-ratio'),
    plugin(function({ addVariant }) {
      addVariant('htmx-settling', ['&.htmx-settling', '.htmx-settling &'])
      addVariant('htmx-request',  ['&.htmx-request',  '.htmx-request &'])
      addVariant('htmx-swapping', ['&.htmx-swapping', '.htmx-swapping &'])
      addVariant('htmx-added',    ['&.htmx-added',    '.htmx-added &'])
    }),
  ],
}
