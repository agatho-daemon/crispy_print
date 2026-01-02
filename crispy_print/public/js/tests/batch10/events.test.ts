import { describe, expect, it, vi } from "vitest"
import {
	CrispyPreviewEvents,
	dispatchCrispyPreviewSource,
	dispatchCrispyPreviewStatus,
} from "../../utils/events"

describe("preview events", () => {
	it("dispatches status event", () => {
		const handler = vi.fn()
		window.addEventListener(CrispyPreviewEvents.Status, handler)

		dispatchCrispyPreviewStatus({ status: "ready", message: "ok" })

		expect(handler).toHaveBeenCalledTimes(1)
		const detail = handler.mock.calls[0][0].detail
		expect(detail.status).toBe("ready")
		window.removeEventListener(CrispyPreviewEvents.Status, handler)
	})

	it("dispatches source event", () => {
		const handler = vi.fn()
		window.addEventListener(CrispyPreviewEvents.Source, handler)

		dispatchCrispyPreviewSource({ source: "#set page" })

		expect(handler).toHaveBeenCalledTimes(1)
		const detail = handler.mock.calls[0][0].detail
		expect(detail.source).toBe("#set page")
		window.removeEventListener(CrispyPreviewEvents.Source, handler)
	})
})
