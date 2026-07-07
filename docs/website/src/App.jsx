import { useEffect, useRef, useState } from "react";
import CytoscapeComponent from "react-cytoscapejs";
import EventLogList from "./EventLogList.jsx";
import SystemStatePanel from "./SystemStatePanel.jsx";
import { EventBus } from "./eventBus.js";
import { EventRunner } from "./EventRunner.js";
import { emitEvent } from "./eventLogger.js";
import { setActiveNode, setLastEvent } from "./stateManager.js";

const autoplayIntervalMs = 2600;
const autoplayCycleCount = 2;
const systemStateCollapseStorageKey = "biblion.website.systemStateCollapsed";

function delay(ms) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

const overviewSequence = [
  "biblion",
  "vision",
  "architecture",
  "development",
  "publications"
];

const overviewSequenceEdges = ["e1", "e2", "e3", "e4"];

const overviewNodes = [
  {
    data: {
      id: "biblion",
      label: "Biblion",
      category: "Platform",
      summary: "Digital Humanities platform centered on preservation, scholarship, and responsible AI."
    },
    position: { x: 120, y: 220 }
  },
  {
    data: {
      id: "vision",
      label: "Vision",
      category: "Document",
      summary: "Defines the long-term purpose and intellectual direction of the project."
    },
    position: { x: 380, y: 220 }
  },
  {
    data: {
      id: "architecture",
      label: "Architecture",
      category: "Document",
      summary: "Describes the system structure, module boundaries, and implementation shape."
    },
    position: { x: 640, y: 220 }
  },
  {
    data: {
      id: "development",
      label: "Development",
      category: "Workflow",
      summary: "Tracks active engineering notes, procedures, and ongoing implementation work."
    },
    position: { x: 900, y: 220 }
  },
  {
    data: {
      id: "publications",
      label: "Publications",
      category: "Outcome",
      summary: "Represents the scholarly outputs the platform is intended to support."
    },
    position: { x: 1160, y: 220 }
  }
];

const overviewEdges = [
  { data: { id: "e1", source: "biblion", target: "vision" } },
  { data: { id: "e2", source: "vision", target: "architecture" } },
  { data: { id: "e3", source: "architecture", target: "development" } },
  { data: { id: "e4", source: "development", target: "publications" } }
];

const principlesNodes = [
  {
    data: {
      id: "principles",
      label: "Guiding Principles",
      category: "Vision",
      summary: "Core commitments that govern how Biblion applies technology to historical materials."
    },
    position: { x: 640, y: 350 }
  },
  {
    data: {
      id: "preservation",
      label: "Preservation Before Convenience",
      category: "Principle",
      summary: "Source material should remain recoverable, traceable, and documented whenever possible."
    },
    position: { x: 640, y: 110 }
  },
  {
    data: {
      id: "scholarship",
      label: "Scholarship Before Automation",
      category: "Principle",
      summary: "Automation supports scholarship; human understanding remains central to every meaningful interpretation."
    },
    position: { x: 980, y: 260 }
  },
  {
    data: {
      id: "documentation",
      label: "Documentation Before Assumption",
      category: "Principle",
      summary: "Knowledge should not exist only in source code; decisions and context must be recorded."
    },
    position: { x: 860, y: 570 }
  },
  {
    data: {
      id: "community",
      label: "Community Before Individual",
      category: "Principle",
      summary: "Meaningful preservation depends on contributions from many disciplines."
    },
    position: { x: 420, y: 570 }
  },
  {
    data: {
      id: "stewardship",
      label: "Stewardship Before Ownership",
      category: "Principle",
      summary: "Historical texts are treated as shared human inheritance, not possessions."
    },
    position: { x: 300, y: 260 }
  }
];

const principlesEdges = [
  { data: { id: "p1", source: "principles", target: "preservation" } },
  { data: { id: "p2", source: "principles", target: "scholarship" } },
  { data: { id: "p3", source: "principles", target: "documentation" } },
  { data: { id: "p4", source: "principles", target: "community" } },
  { data: { id: "p5", source: "principles", target: "stewardship" } }
];

const principlesElements = [...principlesNodes, ...principlesEdges];

const overviewNodeDataById = Object.fromEntries(
  overviewNodes.map((node) => [
    node.data.id,
    {
      graphTitle: "Biblion Overview",
      ...node.data
    }
  ])
);

const overviewSequenceNodes = overviewSequence.map((nodeId) => overviewNodeDataById[nodeId]);
const initialOverviewNode = overviewSequenceNodes[0];

const stylesheet = [
  {
    selector: "node",
    style: {
      "background-color": "#143642",
      shape: "round-rectangle",
      label: "data(label)",
      color: "#f7f3e9",
      "text-valign": "center",
      "text-halign": "center",
      "text-wrap": "wrap",
      "text-max-width": 188,
      "font-size": "13px",
      width: 220,
      height: 124,
      "border-width": 2,
      "border-color": "#cda15c"
    }
  },
  {
    selector: "edge",
    style: {
      width: 2,
      "line-color": "#9cafb7",
      "target-arrow-color": "#9cafb7",
      "target-arrow-shape": "triangle",
      "curve-style": "bezier"
    }
  },
  {
    selector: ".active-node",
    style: {
      "background-color": "#f0e6c8",
      color: "#143642",
      "border-color": "#d46a1f",
      "border-width": 5,
      "overlay-opacity": 0
    }
  },
  {
    selector: ".sequence-edge",
    style: {
      width: 4,
      "line-color": "#cda15c",
      "target-arrow-color": "#cda15c"
    }
  }
];

const overviewLayout = { name: "preset", fit: true, padding: 24 };
const principlesLayout = { name: "preset", fit: true, padding: 30 };

function joinClasses(...values) {
  return values.filter(Boolean).join(" ");
}

function GraphView({ title, description, elements, layoutConfig, onNodeSelect, activeNode }) {
  const [cy, setCy] = useState(null);
  const zoomMultiplier = title === "Guiding Principles" ? 1.06 : 1.02;
  const activeNodeId = activeNode?.id ?? null;

  const renderedElements = elements.map((element) => {
    if (!element.data?.id || element.data.source) {
      return element;
    }

    return {
      ...element,
      classes: joinClasses(
        element.classes,
        element.data.id === activeNodeId ? "active-node" : ""
      )
    };
  });

  useEffect(() => {
    if (!cy || !onNodeSelect) {
      return undefined;
    }

    const handleNodeTap = (event) => {
      onNodeSelect({
        graphTitle: title,
        ...event.target.data()
      });
    };

    cy.on("tap", "node", handleNodeTap);

    return () => {
      cy.off("tap", "node", handleNodeTap);
    };
  }, [cy, onNodeSelect, title]);

  useEffect(() => {
    if (!cy) {
      return undefined;
    }

    cy.fit(cy.elements(), 18);
    cy.zoom(cy.zoom() * zoomMultiplier);
    cy.center();

    return undefined;
  }, [cy, elements, layoutConfig, zoomMultiplier]);

  return (
    <article className="graph-card">
      <header className="graph-card-header">
        <p className="eyebrow">Static Graph View</p>
        <h2>{title}</h2>
        <p>{description}</p>
      </header>

      <div className="graph-canvas" aria-label={title}>
        <CytoscapeComponent
          cy={setCy}
          elements={renderedElements}
          stylesheet={stylesheet}
          layout={layoutConfig}
          style={{ width: "100%", height: "100%" }}
        />
      </div>
    </article>
  );
}

export default function App() {
  const [selectedNode, setSelectedNode] = useState(initialOverviewNode);
  const [sequenceStep, setSequenceStep] = useState(0);
  const [isAutoplaying, setIsAutoplaying] = useState(false);
  const [isSystemStateCollapsed, setIsSystemStateCollapsed] = useState(() => {
    if (typeof window === "undefined") {
      return true;
    }

    const storedValue = window.localStorage.getItem(systemStateCollapseStorageKey);

    if (storedValue === null) {
      return true;
    }

    return storedValue === "true";
  });
  const sequenceStepRef = useRef(0);
  const eventBusRef = useRef(null);
  const eventRunnerRef = useRef(null);

  const applySequenceStep = (index, nodeData) => {
    sequenceStepRef.current = index;
    setSequenceStep(index);
    setSelectedNode(nodeData);
    setActiveNode(nodeData);
  };

  if (!eventBusRef.current) {
    eventBusRef.current = new EventBus();
  }

  if (!eventRunnerRef.current) {
    eventRunnerRef.current = new EventRunner({
      eventBus: eventBusRef.current,
      executor: async (_startEvent, context) => {
        const {
          delayMs,
          isCurrentRun,
          payload = {},
          traceId
        } = context;
        const { startIndex = 0 } = payload;
        const trail = [];
        const autoplayStepCount = overviewSequenceNodes.length * autoplayCycleCount - 1;

        for (let advanceOffset = 0; advanceOffset < autoplayStepCount; advanceOffset += 1) {
          if (!isCurrentRun()) {
            break;
          }

          const index = (startIndex + advanceOffset) % overviewSequenceNodes.length;
          const nodeData = overviewSequenceNodes[index];
          applySequenceStep(index, nodeData);
          const previousStep =
            index === 0 ? overviewSequenceNodes.length - 1 : index - 1;

          const entry = emitEvent(
            "sequence_step_advanced",
            {
              source: "autoplay",
              previousStep,
              nextStep: index,
              nodeId: nodeData.id
            },
            { traceId }
          );

          setLastEvent(entry);
          eventBusRef.current.emit("sequence_step", {
            index,
            node: nodeData,
            source: "autoplay",
            traceId,
            logEntry: entry
          });
          trail.push(entry);

          if (advanceOffset < autoplayStepCount - 1) {
            await delay(delayMs);
          }
        }

        return trail;
      },
      delayMs: autoplayIntervalMs
    });
  }

  useEffect(() => {
    sequenceStepRef.current = sequenceStep;
  }, [sequenceStep]);

  useEffect(() => {
    setActiveNode(initialOverviewNode);
  }, []);

  useEffect(() => {
    window.localStorage.setItem(
      systemStateCollapseStorageKey,
      String(isSystemStateCollapsed)
    );
  }, [isSystemStateCollapsed]);

  useEffect(() => {
    const eventBus = eventBusRef.current;

    const unsubscribeStep = eventBus.on("sequence_step", ({ index, node }) => {
      sequenceStepRef.current = index;
      setSequenceStep(index);
      setSelectedNode(node);
    });

    const unsubscribeCompleted = eventBus.on("sequence_completed", () => {
      setIsAutoplaying(false);
    });

    const unsubscribeStopped = eventBus.on("sequence_stopped", () => {
      setIsAutoplaying(false);
    });

    return () => {
      unsubscribeStep();
      unsubscribeCompleted();
      unsubscribeStopped();
      eventRunnerRef.current?.stop({ reason: "app_unmounted" });
    };
  }, []);

  const overviewElements = [
    ...overviewNodes,
    ...overviewEdges
  ];

  const handleNodeSelect = (nodeData) => {
    setSelectedNode(nodeData);
    setActiveNode(nodeData);

    const entry = emitEvent("node_selected", {
      graphTitle: nodeData.graphTitle,
      nodeId: nodeData.id,
      label: nodeData.label,
      category: nodeData.category ?? null
    });

    setLastEvent(entry);
    eventBusRef.current.emit("node_selected", {
      node: nodeData,
      logEntry: entry
    });
  };

  const handleAdvanceSequence = () => {
    eventRunnerRef.current?.stop({ reason: "manual_advance" });

    const previousStep = sequenceStepRef.current;
    const nextStep = (previousStep + 1) % overviewSequenceNodes.length;
    const nodeData = overviewSequenceNodes[nextStep];

    applySequenceStep(nextStep, nodeData);

    const entry = emitEvent("sequence_step_advanced", {
      source: "manual",
      previousStep,
      nextStep,
      nodeId: nodeData.id
    });

    setLastEvent(entry);
    eventBusRef.current.emit("sequence_step", {
      index: nextStep,
      node: nodeData,
      source: "manual",
      logEntry: entry
    });
  };

  const handleResetSequence = () => {
    eventRunnerRef.current?.stop({ reason: "sequence_reset" });

    const previousStep = sequenceStepRef.current;
    const nodeData = overviewSequenceNodes[0];

    applySequenceStep(0, nodeData);

    const entry = emitEvent("sequence_reset", {
      previousStep,
      nextStep: 0,
      nodeId: nodeData.id
    });

    setLastEvent(entry);
    eventBusRef.current.emit("sequence_step", {
      index: 0,
      node: nodeData,
      source: "reset",
      logEntry: entry
    });
  };

  const handleToggleAutoplay = () => {
    if (isAutoplaying) {
      eventRunnerRef.current?.stop({ reason: "manual_toggle" });

      const stopEntry = emitEvent("autoplay_toggled", {
        previousState: true,
        nextState: false,
        intervalMs: autoplayIntervalMs
      });

      setLastEvent(stopEntry);
      eventBusRef.current.emit("autoplay_toggled", {
        nextState: false,
        intervalMs: autoplayIntervalMs,
        logEntry: stopEntry
      });
      return;
    }

    const startIndex =
      sequenceStepRef.current >= overviewSequenceNodes.length - 1
        ? 0
        : sequenceStepRef.current + 1;

    const startEntry = emitEvent("autoplay_toggled", {
      previousState: false,
      nextState: true,
      intervalMs: autoplayIntervalMs,
      startIndex
    });

    setIsAutoplaying(true);
    setLastEvent(startEntry);
    eventBusRef.current.emit("autoplay_toggled", {
      nextState: true,
      intervalMs: autoplayIntervalMs,
      startIndex,
      logEntry: startEntry
    });

    eventRunnerRef.current
      ?.run("autoplay_toggled", {
        payload: {
          previousState: false,
          nextState: true,
          intervalMs: autoplayIntervalMs,
          startIndex
        }
      })
      .catch(() => {
        setIsAutoplaying(false);
      });
  };

  return (
    <main className={`page-shell ${isAutoplaying ? "page-shell-autoplay" : ""}`}>
      <section className={`intro-panel ${isAutoplaying ? "intro-panel-autoplay" : ""}`}>
        <p className="eyebrow">Biblion Website Prototype</p>
        <h1>Minimal Cytoscape Graph</h1>
        <p>
          Static React example using predefined node and edge arrays. The
          delayed overview sequence now runs through an EventBus-backed runner.
        </p>

        <div className="sequence-controls">
          <button className="sequence-button" type="button" onClick={handleAdvanceSequence}>
            Advance Overview Sequence
          </button>
          <button
            className="sequence-button sequence-button-secondary"
            type="button"
            onClick={handleResetSequence}
          >
            Reset Sequence
          </button>
          <button
            className={`sequence-button ${isAutoplaying ? "sequence-button-active" : ""}`}
            type="button"
            onClick={handleToggleAutoplay}
          >
            {isAutoplaying ? "Stop Autoplay" : "Start Autoplay"}
          </button>
        </div>

        <p className="sequence-status">
          Autoplay is {isAutoplaying ? "running" : "stopped"} at {autoplayIntervalMs} ms per step.
        </p>

        <section className="selected-node-panel" aria-label="Selected node details">
          <p className="eyebrow">Selected Node Function</p>
          {selectedNode ? (
            <>
              <h2>{selectedNode.label}</h2>
              <p className="selected-node-meta">
                {selectedNode.graphTitle} · {selectedNode.category}
              </p>
              <p>{selectedNode.summary}</p>
            </>
          ) : (
            <p>Click a node or run the sequence to inspect its data in parent state.</p>
          )}
        </section>

        {isAutoplaying ? null : (
          <div className="system-state-controls">
            <button
              className="system-state-toggle"
              type="button"
              onClick={() => setIsSystemStateCollapsed((currentValue) => !currentValue)}
              aria-expanded={!isSystemStateCollapsed}
              aria-controls="webmaster-widgets"
            >
              {isSystemStateCollapsed ? "Expand webmaster widgets" : "Collapse webmaster widgets"}
            </button>
          </div>
        )}
        {isAutoplaying || isSystemStateCollapsed ? null : (
          <div id="webmaster-widgets">
            <SystemStatePanel isCollapsed={false} />
            <EventLogList />
          </div>
        )}
      </section>

      <section
        className={`graph-panel ${isAutoplaying ? "graph-panel-autoplay" : ""}`}
        aria-label="Biblion graph previews"
      >
        <GraphView
          title="Biblion Overview"
          description={`A minimal relationship map for the current documentation-facing website prototype. Sequence step ${sequenceStep + 1} of ${overviewSequence.length}.`}
          elements={overviewElements}
          layoutConfig={overviewLayout}
          onNodeSelect={handleNodeSelect}
          activeNode={selectedNode}
        />

        <GraphView
          title="Guiding Principles"
          description="A static graph derived from the principles outlined in THE_BIBLION_PROJECT.md."
          elements={principlesElements}
          layoutConfig={principlesLayout}
          onNodeSelect={handleNodeSelect}
          activeNode={selectedNode}
        />
      </section>
    </main>
  );
}