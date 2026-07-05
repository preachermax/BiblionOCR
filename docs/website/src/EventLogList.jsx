import { useEffect, useState } from "react";
import { getEventLogs, subscribeToEventLogs } from "./eventLogger.js";

function formatTimestamp(timestamp) {
  const date = new Date(timestamp);

  if (Number.isNaN(date.getTime())) {
    return timestamp;
  }

  return date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit"
  });
}

export default function EventLogList() {
  const [events, setEvents] = useState(() => getEventLogs());

  useEffect(() => {
    return subscribeToEventLogs(setEvents);
  }, []);

  return (
    <section className="event-log-panel" aria-label="Event log">
      <p className="eyebrow">Event Log</p>
      {events.length === 0 ? (
        <p>No events logged yet.</p>
      ) : (
        <ol className="event-log-list">
          {events
            .slice()
            .reverse()
            .map((entry, index) => (
              <li className="event-log-item" key={`${entry.timestamp}-${entry.event}-${index}`}>
                <div className="event-log-row">
                  <strong>{entry.event}</strong>
                  <time dateTime={entry.timestamp}>{formatTimestamp(entry.timestamp)}</time>
                </div>
                <pre className="event-log-payload">{JSON.stringify(entry.payload, null, 2)}</pre>
              </li>
            ))}
        </ol>
      )}
    </section>
  );
}