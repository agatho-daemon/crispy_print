import { defineConfig } from "vitest/config"
import vue from "@vitejs/plugin-vue"

export default defineConfig({
	plugins: [vue()],
	test: {
		environment: "jsdom",
		include: ["crispy_print/public/js/tests/**/*.test.ts"],
	},
})
