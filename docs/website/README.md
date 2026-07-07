# Website Graph Demo

This directory contains a minimal React and Cytoscape prototype for Biblion's future website-facing graph views.

Current scope:

* static node array
* static edge array
* two static views: overview and guiding principles
* node click handler wired from Cytoscape to parent React state
* selected node details rendered from parent state
* button-driven linear sequence highlight for the overview graph
* reset action for returning the sequence highlight to the first node
* optional autoplay for advancing the overview sequence automatically
* autoplay mode now favors the graph surface by collapsing diagnostic side panels while the sequence runs
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

Autoplay behavior notes:

* the live autoplay path now emits concrete `sequence_step` updates rather than only abstract event-graph entries
* while autoplay is active, the system-state and event-log panels are hidden so the graph animation has more visual room
* the active-node highlight now relies on border and fill treatment without the earlier invalid shadow style warnings

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

The graphs remain intentionally small so they can serve as clean integration points for later website architecture work. The second view is derived from the guiding principles in `docs/vision/THE_BIBLION_PROJECT.md`, node clicks now surface the selected node's data in the parent component, and the overview graph includes advance, reset, and autoplay controls for a linear highlight sequence driven by an EventBus-backed EventRunner.