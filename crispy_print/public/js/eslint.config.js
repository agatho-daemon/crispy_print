const vue = require("eslint-plugin-vue")
const tsPlugin = require("@typescript-eslint/eslint-plugin")
const tsParser = require("@typescript-eslint/parser")
const vueParser = require("vue-eslint-parser")
const prettier = require("eslint-config-prettier")

/** @type {import("eslint").Linter.FlatConfig[]} */
module.exports = [
	{
		ignores: ["node_modules/**", "dist/**", "../dist/**", "**/*.min.js"],
	},

	// Vue recommended (flat config)
	...((vue.configs && (vue.configs["flat/vue3-recommended"] || vue.configs["flat/recommended"])) ||
		[]),

	// App source (JS/TS/Vue)
	{
		files: ["**/*.{js,ts,vue}"],
		languageOptions: {
			ecmaVersion: "latest",
			sourceType: "module",
			parser: vueParser,
			parserOptions: {
				parser: tsParser,
				extraFileExtensions: [".vue"],
			},
			globals: {
				frappe: "readonly",
				__: "readonly",
				Awesomplete: "readonly",
			},
		},
		plugins: {
			vue,
			"@typescript-eslint": tsPlugin,
		},
		rules: {
			...(prettier.rules || {}),
			"@typescript-eslint/no-explicit-any": "off",
			"@typescript-eslint/ban-ts-comment": "off",
			// This app intentionally mutates settings objects passed down from the store.
			"vue/no-mutating-props": "off",
			// Keep lint focused on correctness, not template attribute cosmetics.
			"vue/attributes-order": "off",
			"vue/first-attribute-linebreak": "off",
			"vue/v-on-event-hyphenation": "off",
			"vue/multi-word-component-names": "off",
			"vue/no-v-html": "off",
		},
	},
]
