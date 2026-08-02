import { useEffect, useState } from "react";
import { getState, subscribeToState } from "./stateManager.js";

function renderValue(value) {
  if (value === null) {
    return "null";
  }

  if (value === undefined) {
    return "undefined";
  }

  if (typeof value === "boolean") {
    return value ? "true" : "false";
  }

  if (typeof value === "string") {
    return value;
  }

  return JSON.stringify(value, null, 2);
}

export default function SystemStatePanel({ isCollapsed }) {
  const [systemState, setSystemState] = useState(() => getState());

  useEffect(() => {
    return subscribeToState(setSystemState);
  }, []);

  return (
    <section className="system-state-panel" aria-label="System state">
      <p className="eyebrow">System State</p>

      {isCollapsed ? null : (
        <dl className="system-state-list" id="system-state-list">
          <div className="system-state-item">
            <dt>activeNode</dt>
            <dd>
              <pre className="system-state-value">{renderValue(systemState.activeNode)}</pre>
            </dd>
          </div>
          <div className="system-state-item">
            <dt>lastEvent</dt>
            <dd>
              <pre className="system-state-value">{renderValue(systemState.lastEvent)}</pre>
            </dd>
          </div>
          <div className="system-state-item">
            <dt>isRunning</dt>
            <dd>
              <pre className="system-state-value">{renderValue(systemState.isRunning)}</pre>
            </dd>
          </div>
        </dl>
      )}
    </section>
  );
}