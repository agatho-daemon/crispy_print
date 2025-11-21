# Crispy Print - AI Coding Instructions

## Project Overview

**Crispy Print** is a Frappe v15+ custom app that provides a modern print format builder using **Typst CLI** as the backend print engine and **Vue 3** as the frontend visualization layer. It integrates into Frappe Desk as an SPA and offers live preview capabilities for creating print formats with Typst markup.

**Core Architecture:**
- **Backend:** Python-based Frappe app (v15+) with minimal backend logic
- **Frontend:** Vue 3 SPA with Vite build system
- **Print Engine:** Typst CLI integration via Web Workers (non-blocking UI)
- **Integration:** Dual-mount architecture (Vite dev mode + Frappe Desk integration)
- **Inspiration:** Draws patterns from Frappe's `Print Format` DocType, `print-format-builder-beta`, and sibling `apps/crispy` implementations

**Key DocType:**
- **Crispy Print:** Stores print format data (doctype, template name, module, language)
  - `typst_preamble` - Editable Typst header code
  - `typst_layout` - Generated Typst markup (hidden)
  - `layout_json` - Internal JSON representation (hidden, similar to Print Format Builder Beta)

**Key Pages:**
- `/app/crispy-print-builder` - 4-column print format builder
- `/app/crispy-print` - Landing page for templates and formats

## Critical Integration Patterns

### 1. Dual-Mount Vue Architecture

**Two modes for development:**

```bash
# Vite dev mode (hot reload, faster iteration)
cd apps/crispy_print/frontend
yarn dev  # Accessible at http://fdev.local:8080/crispy

# Frappe integration (full context, Socket.io, auth)
bench start  # Test full integration
```

**Build for production:**
```bash
bench build --app crispy_print  # Outputs to crispy_print/public/frontend/
```

### 2. Four-Column Builder Layout

**Reference:** `apps/crispy/public/js/preview/previewPane.js` for layout patterns.

```vue
<!-- App.vue or Builder.vue -->
<template>
  <div class="crispy-builder-grid">
    <!-- Column 1: DocType Fields Palette -->
    <FieldsPane :doctype="currentDoctype" />
    
    <!-- Column 2: Layout Builder (drag-drop sections/fields) -->
    <BuilderPane v-model:layout="layout" />
    
    <!-- Column 3: Live Typst SVG Preview -->
    <PreviewPane 
      :layout="layout" 
      :settings="pageSettings"
      @pdf-ready="handlePdfReady" />
    
    <!-- Column 4: Page Settings (margins, fonts, etc.) -->
    <SettingsPane v-model:settings="pageSettings" />
  </div>
</template>

<style scoped>
.crispy-builder-grid {
  display: grid;
  grid-template-columns: 200px 1fr 1fr 250px;
  gap: 12px;
  height: calc(100vh - 100px);
}
</style>
```

**Column responsibilities:**
1. **Fields:** Available doctype fields from `frappe.get_meta(doctype).fields`
2. **Builder:** Sections/columns/fields structure (Beta builder JSON format)
3. **Preview:** Embed SVG output from Typst worker
4. **Settings:** Page size, margins, fonts, letterhead selection

### 3. Typst Worker Integration

**Reference:** `apps/crispy/public/js/worker/` directory.

Typst compilation runs in a **Web Worker** to prevent UI blocking:

```javascript
// Example: PreviewPanel.vue composable
import { ref, watch } from 'vue';

const worker = new Worker('/assets/crispy_print/typst-worker.js');
const svgOutput = ref(null);
const isCompiling = ref(false);

watch(() => props.layout, (newLayout) => {
  isCompiling.value = true;
  worker.postMessage({
    type: 'compile',
    layout: newLayout,
    settings: props.settings
  });
});

worker.onmessage = (e) => {
  if (e.data.type === 'svg') {
    svgOutput.value = e.data.svg;
    isCompiling.value = false;
  }
};
```

**Translation Pipeline:**
1. Vue layout data → JSON format (Beta builder compatible)
2. JSON → Typst markup (see `apps/crispy/public/js/translator/betaJSONToTypst.js`)
3. Typst CLI compilation → SVG output
4. Display SVG in preview pane

### 4. Socket.io Integration

Socket connection configuration from `sites/common_site_config.json`:

```javascript
// socket.js
import { socketio_port } from "../../../../sites/common_site_config.json";

const protocol = window.location.protocol === "https:" ? "https" : "http";
const host = window.location.hostname;
const port = socketio_port ? `:${socketio_port}` : "";
const siteName = window.frappe?.boot?.sitename || "default";

const url = `${protocol}://${host}${port}/${siteName}`;
socket = io(url, { withCredentials: true });
```

Make available globally: `app.config.globalProperties.$socket`

### 5. Frappe API Integration Patterns

**Backend whitelisted API:**
```python
# crispy_print/api.py
import frappe

@frappe.whitelist()
def generate_typst_pdf(doc_type, doc_name, template_name):
    """Generate PDF using Typst CLI."""
    doc = frappe.get_doc(doc_type, doc_name)
    template = frappe.get_doc("Crispy Print", template_name)
    
    # Your Typst compilation logic
    return {"pdf_url": "/files/output.pdf", "status": "success"}
```

**Frontend resource pattern (preferred):**
```vue
<script setup>
import { createResource } from "frappe-ui";

const generatePDF = createResource({
  url: "crispy_print.api.generate_typst_pdf",
  params: {
    doc_type: "Sales Invoice",
    doc_name: "SI-2024-001",
    template_name: "Standard Invoice"
  },
  onSuccess(data) {
    console.log("PDF generated:", data.pdf_url);
  },
  onError(error) {
    console.error("PDF generation failed:", error);
  }
});

// Trigger the call
generatePDF.fetch();
</script>
```

## Code Conventions & Linting

### Python (Backend)
- **Framework:** Frappe v15+ only - use modern APIs (`frappe.qb`, `frappe.get_doc()`)
- **Line length:** 110 characters (configured in `pyproject.toml`)
- **Linter:** Ruff with imports sorted (`ruff --select=I`)
- **Whitelist APIs:** Always use `@frappe.whitelist()` decorator for frontend-callable methods
- **Type hints:** Use Python 3.10+ type hints where applicable

### JavaScript/Vue (Frontend)
- **Vue API:** Composition API only - `<script setup>` syntax required
- **Components:** Prefer `frappe-ui` components (`Button`, `Dialog`, `FormControl`)
- **API calls:** Use `createResource()` pattern, avoid raw `fetch()`
- **Linter:** Biome (tabs, double quotes, semicolons only when necessary)
- **Formatting:** Auto-format via pre-commit (Prettier)

### File Organization
```
crispy_print/
├── crispy_print/          # Backend Python modules
│   ├── api.py             # Whitelisted API methods
│   ├── hooks.py           # App hooks and configuration
│   └── crispy_print/      # DocType definitions
├── frontend/              # Vue 3 application
│   └── src/
│       ├── components/    # Reusable Vue components
│       ├── pages/         # Route pages
│       └── router.js      # Vue Router config
└── public/                # Build outputs and static assets
    └── frontend/          # Vite build output
```

## Development Workflows

### Setup and Build

```bash
# Install app in bench
cd /path/to/bench
bench get-app /path/to/crispy_print
bench install-app crispy_print

# Setup pre-commit hooks
cd apps/crispy_print
pre-commit install

# Frontend development
cd frontend
yarn install
yarn dev  # Hot reload mode

# Build for production
bench build --app crispy_print
```

### Running the Development Server

```bash
# Full Frappe bench (recommended for integration testing)
bench start

# Or with Procfile processes
bench start web socketio watch  # Core services
```

### Testing and Linting

```bash
# Python linting and fixes
cd apps/crispy_print
ruff check .
ruff check --fix .  # Auto-fix issues

# Frontend linting
cd frontend
yarn lint
yarn lint:fix

# Run pre-commit on all files
pre-commit run --all-files
```

## Common Patterns & Examples

### Adding a New Vue Route

```javascript
// frontend/src/router.js
const routes = [
  {
    path: "/builder/:template_id",
    name: "TemplateBuilder",
    component: () => import("@/pages/TemplateBuilder.vue"),
    props: true
  },
];
```

### Global Component Registration

```javascript
// frontend/src/main.js
import { Button, Dialog, Input } from "frappe-ui";

app.component("Button", Button);
app.component("Dialog", Dialog);
app.component("Input", Input);
```

### Accessing Frappe Context in Vue

```vue
<script setup>
import { computed } from "vue";

const currentUser = computed(() => window.frappe?.boot?.user?.name);
const siteName = computed(() => window.frappe?.boot?.sitename);
</script>
```

## Troubleshooting

### Vue App Not Mounting in Frappe Desk
1. Check browser console for `window.mountCrispyPrintBuilder is not defined`
2. Rebuild bundle: `bench build --app crispy_print`
3. Hard refresh: `Cmd+Shift+R` (macOS) or `Ctrl+Shift+R` (Linux/Windows)
4. Check if build outputs exist in `crispy_print/public/frontend/`

### Socket.io Connection Fails
1. Verify `socketio_port` (9000) in `sites/common_site_config.json`
2. Check `bench start` logs for SocketIO server status
3. Ensure `node apps/frappe/socketio.js` process is running

### Pre-commit Hook Failures
```bash
# Auto-fix most issues
ruff --fix .
cd frontend && yarn lint:fix

# Skip hooks temporarily (not recommended)
git commit --no-verify
```

### Build Errors
```bash
# Clear caches and rebuild
rm -rf node_modules/.cache
bench clear-cache
bench build --app crispy_print --force
```

## Related Apps & Reference Implementations

### `apps/crispy` (Sibling App)
The **primary reference implementation** for Typst integration patterns.

**Core Preview System:**
- `public/js/crispyPreview.js` - Entry point, exports `window.crispy.preview.initPreview()`
- `public/js/preview/previewPane.js` - 2-column grid (builder + preview), worker initialization
- `public/js/worker/setupWorker.js` - Worker lifecycle management
- `public/js/worker/typstWorker.js` - Web Worker code (Typst CLI wrapper)

**Layout Translation:**
- `public/js/adapters/beta.js` - Extract layout from Print Format Builder Beta Vue store
- `public/js/translator/betaJSONToTypst.js` - Convert Beta JSON → Typst markup (~400 lines)
- `public/js/translator/htmlToTypst.js` - HTML → Typst conversion

**Full Page Implementation:**
- `public/js/pages/typst_print.js` - Complete Typst print page (~850 lines)
  - Document loading, format selection with letterhead
  - PDF generation/download, sample document switching

**Use these files as blueprints** when building Vue 3 equivalents.

### `apps/frappe` (Core Framework)
- Use Frappe v15+ APIs: `frappe.qb`, `frappe.call()`, `@frappe.whitelist()`
- Study `frappe/printing/` for print format patterns
- Reference `frappe/public/js/frappe/` for UI components

## Project-Specific Notes

- **Developer mode:** Enabled in `sites/common_site_config.json` (`developer_mode: 1`)
- **Live reload:** Enabled (`live_reload: true`) with file watcher on port 6787
- **Redis ports:** Cache (13000), Queue (11000), SocketIO (13000)
- **Webserver port:** 8000 (configurable in `common_site_config.json`)
- **Bench commands:** All `bench` commands run from workspace root (`/Users/ismail/frappe/fdev15`)

## Key Dependencies

- **Python:** 3.10+ required
- **Frappe:** v15+ (managed by bench)
- **Vue:** 3.x (Composition API)
- **Vite:** Build tool for frontend
- **Typst CLI:** External print engine (must be installed separately)
- **Node.js:** Required for Socket.io and frontend build
