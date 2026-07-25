import { getLogger } from "../logger"

const logger = getLogger({ module: "TypstPreviewAutocomplete" })

export function createSampleDocAutocomplete(options: {
	previewPane: HTMLElement
	getInput: () => HTMLInputElement | null
	getCurrentDoctype: () => string | null
	setCurrentDoctype: (doctype: string | null) => void
	setCurrentDocname: (docname: string | null) => void
	clearSelectedDocument: () => void
	onSelect: (doctype: string, docname: string) => void
	setFetchingStatus: () => void
}) {
	let awesomplete: any = null
	let initialized = false
	let skipNextInput = false
	let boundInput: HTMLInputElement | null = null
	let cleanupInputListeners: (() => void) | null = null
	let cancelPendingSearch: (() => void) | null = null

	function debounceWithCancel(fn: () => void, delay: number) {
		let timeout: number | undefined
		const debounced = () => {
			if (timeout) window.clearTimeout(timeout)
			timeout = window.setTimeout(() => {
				timeout = undefined
				fn()
			}, delay)
		}
		debounced.cancel = () => {
			if (timeout) {
				window.clearTimeout(timeout)
				timeout = undefined
			}
		}
		return debounced
	}

	function destroyInstance() {
		cancelPendingSearch?.()
		cancelPendingSearch = null
		cleanupInputListeners?.()
		cleanupInputListeners = null
		if (awesomplete) {
			if (typeof awesomplete.destroy === "function") {
				awesomplete.destroy()
			} else if (boundInput?.parentNode) {
				const clonedInput = boundInput.cloneNode(true) as HTMLInputElement
				boundInput.parentNode.replaceChild(clonedInput, boundInput)
			}
			awesomplete = null
		}
		boundInput = null
	}

	function bindInput(input: HTMLInputElement, doctype: string) {
		options.setCurrentDoctype(doctype)
		options.setCurrentDocname(null)
		initialized = true
		skipNextInput = false

		input.placeholder = __("Search {0}...", [__(doctype)])
		input.setAttribute("data-doctype", doctype)
		input.value = ""
		options.clearSelectedDocument()

		awesomplete = new Awesomplete(input, {
			minChars: 0,
			maxItems: 20,
			autoFirst: true,
			filter: () => true,
		})
		const awesompleteInstance = awesomplete
		boundInput = input

		function searchDocs(txt: string) {
			frappe.call({
				method: "frappe.desk.search.search_link",
				args: {
					doctype,
					txt: txt || "",
					page_length: 20,
				},
				callback: (r: any) => {
					if (!awesomplete || awesomplete !== awesompleteInstance || !input?.isConnected) {
						return
					}
					if (r.message && r.message.length) {
						awesomplete.list = r.message.slice(0, 20).map((d: any) => ({
							label: d.value + (d.description ? " - " + __(d.description) : ""),
							value: d.value,
						}))
					} else {
						awesomplete.list = []
					}
				},
			})
		}

		const handleFocus = () => {
			searchDocs(input.value)
		}
		input.addEventListener("focus", handleFocus)

		const handleDebouncedInput = debounceWithCancel(() => {
			if (skipNextInput) {
				skipNextInput = false
				return
			}
			options.clearSelectedDocument()
			searchDocs(input.value)
		}, 300)
		cancelPendingSearch = handleDebouncedInput.cancel
		input.addEventListener("input", handleDebouncedInput)

		const handleSelectComplete = () => {
			skipNextInput = true
			const selectedDoc = input.value
			options.setCurrentDocname(selectedDoc)
			options.clearSelectedDocument()

			const currentDoctype = options.getCurrentDoctype()
			if (!selectedDoc || !currentDoctype) {
				logger.debug("No document or doctype selected")
				return
			}

			options.setFetchingStatus()
			options.onSelect(currentDoctype, selectedDoc)
		}
		input.addEventListener("awesomplete-selectcomplete", handleSelectComplete)
		cleanupInputListeners = () => {
			input.removeEventListener("focus", handleFocus)
			input.removeEventListener("input", handleDebouncedInput)
			input.removeEventListener("awesomplete-selectcomplete", handleSelectComplete)
		}
	}

	function setup(doctype: string) {
		if (!doctype) {
			logger.warn("Cannot setup autocomplete - missing doctype")
			return
		}

		const sampleDocInput = options.getInput()
		if (!sampleDocInput) {
			return
		}

		if (typeof Awesomplete === "undefined") {
			return
		}

		if (options.getCurrentDoctype() === doctype && initialized) {
			return
		}

		destroyInstance()

		if (initialized && sampleDocInput.parentNode) {
			const newInput = sampleDocInput.cloneNode(true) as HTMLInputElement
			sampleDocInput.parentNode.replaceChild(newInput, sampleDocInput)
			const refreshedInput = options.previewPane.querySelector<HTMLInputElement>(
				"#typst-sample-doc-input"
			)
			if (!refreshedInput) {
				logger.error("Autocomplete failed to get refreshed input element")
				return
			}
			bindInput(refreshedInput, doctype)
			return
		}

		bindInput(sampleDocInput, doctype)
	}

	function reset() {
		initialized = false
	}

	function cleanup() {
		destroyInstance()
		options.setCurrentDoctype(null)
		options.setCurrentDocname(null)
		initialized = false
		skipNextInput = false
		options.clearSelectedDocument()
	}

	return {
		setup,
		reset,
		cleanup,
	}
}
