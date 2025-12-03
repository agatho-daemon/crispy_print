// vite.config.ts
import path from "node:path"
import vue from "@vitejs/plugin-vue"
import { defineConfig } from "vite"

const appName = "crispy_print"

export default defineConfig(({ command }) => {
	const isDev = command === "serve"

	return {
		plugins: [
			vue(),
		],

		resolve: {
			alias: {
				"@": path.resolve(__dirname, "src"),
			},
		},

		base: isDev ? "/" : `/assets/${appName}/js/`,

		esbuild: {
			jsxFactory: "h",
			jsxFragment: "Fragment",
			target: "esnext",
		},

		build: {
			target: "esnext",
			outDir: path.resolve(__dirname, `../${appName}/public/js`),
			emptyOutDir: true,
			sourcemap: isDev ? "inline" : true,
			chunkSizeWarningLimit: 1500,
			rollupOptions: {
				input: isDev
				? undefined
				: path.resolve(__dirname, "src/main.ts"),
				output: {
					entryFileNames: `crispy/${appName}.bundle.js`,
					chunkFileNames: `crispy/${appName}-[name].js`,
					assetFileNames: `crispy/${appName}-[name][extname]`,
					manualChunks(id) {
						if (id.includes("node_modules")) return "vendor"
						if (id.includes("/components/")) return "components"
						if (id.includes("/pages/")) return "pages"
					},
				},
			},
		},

		optimizeDeps: {
			include: [],
			exclude: ["@/workers/*"],
		},

		server: {
			host: "fdev.local",
			port: 8080,
			allowedHosts: true,
		},
	}
})
