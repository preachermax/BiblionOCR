# Website Graph Demo

This directory contains a minimal React and Cytoscape prototype for Biblion's future website-facing graph views.

Live deployment:

* `https://biblionocr.onrender.com/`

Current scope:

* static node array
* static edge array
* two static views: overview and guiding principles
* node click handler wired from Cytoscape to parent React state
* selected node details rendered from parent state
* button-driven linear sequence highlight for the overview graph
* reset action for returning the sequence highlight to the first node
* optional autoplay for advancing the overview sequence automatically
* interaction events now emit timestamped entries through `src/eventLogger.js`
* a React event log panel now renders logged events and timestamps from the logger module
* a React system-state panel now renders `activeNode`, `lastEvent`, and `isRunning` from the state manager
* autoplay sequence steps now flow through `src/EventRunner.js` and `src/eventBus.js`
* a simple exported event graph now maps each event name to its possible next events
* an event graph executor can recursively traverse that graph through the EventBus while logging and updating state
* execution-run logger entries now share a `traceId` so one run can be grouped end-to-end
* no backend integration

Files:

* `package.json` defines the Vite-based demo dependencies and scripts.
* `index.html` provides the root document.
* `src/main.jsx` mounts the React application.
* `src/App.jsx` defines both static graphs, subscribes to the EventBus, and renders the sequence controls.
* `src/EventLogList.jsx` renders logger entries and timestamps from the in-memory event logger.
* `src/EventGraphExecutor.js` recursively executes event graph edges through the EventBus while updating logger and state.
* `src/EventRunner.js` emits delayed sequence steps through the EventBus while updating state and logger entries.
* `src/SystemStatePanel.jsx` renders the current state manager snapshot in React.
* `src/eventBus.js` provides a small publish/subscribe channel for demo events.
* `src/eventGraph.js` exports the event-to-next-events mapping as `eventGraph`.
* `src/eventLogger.js` stores emitted events in memory with timestamps and `traceId` values, and exposes retrieval and subscription helpers.
* `src/stateManager.js` stores `activeNode`, `lastEvent`, and `isRunning` with getter, setter, and subscription helpers.
* `src/styles.css` provides the page layout and visual treatment.
* `preview.html` mirrors the demo in a no-build browser-friendly form for environments without Node.js.

To run locally once Node.js and npm are installed:

```powershell
Set-Location "c:\Users\Max\Projects\BiblionOCR\docs\website"
npm install
npm run dev
```

To produce a production build:

```powershell
Set-Location "c:\Users\Max\Projects\BiblionOCR\docs\website"
npm install
npm run build
```

## Static Launch Path

The quickest public deployment path is the built Vite site, not the raw repository HTML and not the standalone CDN-served `preview.html` workaround.

The repository root now includes `render.yaml` with a minimal Render Static Site blueprint for this directory.

Render settings:

* Root directory: `docs/website`
* Build command: `npm install && npm run build`
* Publish directory: `dist`

Recommended first-launch checklist:

1. Connect the repository to Render.
2. Confirm the service name `biblion-website-static` or rename it before first deploy.
3. Verify Render detects `docs/website` as the root directory from `render.yaml`.
4. Deploy once and confirm the graph demo loads from the hosted URL rather than from a GitHub code view.
5. Replace patron-facing preview links with the hosted site URL after the first successful deploy.

Current deployment status:

* the site is now live at `https://biblionocr.onrender.com/`
* Patreon post rendering now targets the hosted site URL rather than the earlier preview workaround

## Static Now, Django Later

Keep the current website prototype as a static front-end surface and treat it as the public entry point.

Recommended split:

* Static site now: landing page, graph prototype, public documentation links, public video links.
* Django later: authenticated workflows, dynamic content, server-side project data, forms, and any future account-aware features.

When the Django service is introduced, keep it as a separate deployment target rather than folding the static prototype into the Django runtime immediately. That preserves a fast low-risk homepage while leaving room for a Python-backed application later.

The graphs remain intentionally small so they can serve as clean integration points for later website architecture work. The second view is derived from the guiding principles in `docs/vision/THE_BIBLION_PROJECT.md`, node clicks now surface the selected node's data in the parent component, and the overview graph includes advance, reset, and autoplay controls for a linear highlight sequence driven by an EventBus-backed EventRunner.