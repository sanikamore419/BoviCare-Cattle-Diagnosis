import js from '@eslint/js'
import reactHooks from 'eslint-plugin-react-hooks'

const browserGlobals = Object.fromEntries(
  [
    'Blob', 'Event', 'FileReader', 'FormData', 'Image', 'URL', 'alert', 'confirm',
    'document', 'localStorage', 'navigator', 'setTimeout', 'clearTimeout', 'window',
  ].map(name => [name, 'readonly']),
)

export default [
  { ignores: ['dist/**', 'node_modules/**'] },
  js.configs.recommended,
  {
    files: ['src/**/*.{js,jsx}'],
    plugins: { 'react-hooks': reactHooks },
    rules: {
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',
    },
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      parserOptions: { ecmaFeatures: { jsx: true } },
      globals: browserGlobals,
    },
  },
]
