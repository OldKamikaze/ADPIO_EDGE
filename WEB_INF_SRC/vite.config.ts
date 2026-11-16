//import adapter from '@sveltejs/adapter-auto';
import adapter from '@sveltejs/adapter-static';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	server: {
		host: true,
		port: 5173,

		proxy: {
			'/api': {
				target      : "http://127.0.0.1:8000",
				changeOrigin: false,
				secure      : false,
			}
		}
	},

	plugins: [
		sveltekit({
			//csrf:{
			//	trustedOrigins: [
			//		"http://192.168.1.16:8000",
			//		"http://127.0.0.1:8000",
			//	]
			//},

			compilerOptions: {
				// Force runes mode for the project, except for libraries. Can be removed in svelte 6.
				runes: ({ filename }) => filename.split(/[/\\]/).includes('node_modules') ? undefined : true
			},


			// adapter-auto only supports some environments, see https://svelte.dev/docs/kit/adapter-auto for a list.
			// If your environment is not supported, or you settled on a specific environment, switch out the adapter.
			// See https://svelte.dev/docs/kit/adapters for more information about adapters.
			//adapter: adapter() - Default adapter
			adapter: adapter({
				// default options are shown. On some platforms
				// these options are set automatically — see below
				pages: 'build',
				assets: 'build',
				fallback: undefined,
				precompress: false,
				strict: true
			})				


		})
	]
});
