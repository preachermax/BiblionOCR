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
* no backend integration

Files:

* `package.json` defines the Vite-based demo dependencies and scripts.
* `index.html` provides the root document.
* `src/main.jsx` mounts the React application.
* `src/App.jsx` defines both static graphs, the node click handler, the parent selection state, and the sequence controls including autoplay.
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

The graphs remain intentionally small so they can serve as clean integration points for later website architecture work. The second view is derived from the guiding principles in `docs/vision/THE_BIBLION_PROJECT.md`, node clicks now surface the selected node's data in the parent component, and the overview graph includes advance, reset, and autoplay controls for a linear highlight sequence.