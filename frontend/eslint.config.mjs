import js from '@eslint/js'
import vue from 'eslint-plugin-vue'
import ts from 'typescript-eslint'
export default [
 { ignores: ['dist/**', 'node_modules/**', '.taste-skill/**', 'public/**', 'src/vendor/**'] },
 js.configs.recommended,
 ...ts.configs.recommended,
 ...vue.configs['flat/essential'],
 { files: ['**/*.vue'], languageOptions: { parserOptions: { parser: ts.parser } } },
 { languageOptions: { globals: { document:'readonly', window:'readonly', navigator:'readonly', fetch:'readonly', URL:'readonly', URLSearchParams:'readonly', AbortController:'readonly', setTimeout:'readonly', clearTimeout:'readonly', requestAnimationFrame:'readonly', ResizeObserver:'readonly', HTMLElement:'readonly', HTMLButtonElement:'readonly', KeyboardEvent:'readonly', console:'readonly', process:'readonly', Element:'readonly', Event:'readonly', HTMLInputElement:'readonly', HTMLSelectElement:'readonly', DOMException:'readonly' } }, rules: { '@typescript-eslint/no-explicit-any':'off', '@typescript-eslint/no-unused-vars':['error', {argsIgnorePattern:'^_', varsIgnorePattern:'^_'}], 'vue/multi-word-component-names':'off' } }
]
