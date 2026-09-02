import React, { useMemo, useState } from "react";

function eventTypeClass(eventType) {
  const t = eventType.toLowerCase();
  if (t === "send") return "send";
  if (t === "receive") return "receive";
  if (t.startsWith("release")) return "release";
  if (t.includes("denied") || t.includes("blocked")) return "denied";
  return "";
}

function shortTime(ts) {
  try {
    return ts.split("T")[1].split("+")[0];
  } catch {
    return ts;
  }
}

export default function AuditLog({ entries }) {
  const [actorFilter, setActorFilter] = useState("all");
  const [openIndex, setOpenIndex] = useState(null);

  const actors = useMemo(() => {
    const set = new Set(entries.map((e) => e.actor));
    return ["all", ...Array.from(set)];
  }, [entries]);

  const filtered = useMemo(() => {
    if (actorFilter === "all") return entries;
    return entries.filter((e) => e.actor === actorFilter);
  }, [entries, actorFilter]);

  return (
    <div className="panel full-width">
      <div className="panel-title">
        Audit Log
        <span className="eyebrow">{entries.length} entries</span>
      </div>

      <div className="audit-controls">
        <select value={actorFilter} onChange={(e) => setActorFilter(e.target.value)} aria-label="Filter by actor">
          {actors.map((a) => (
            <option key={a} value={a}>
              {a === "all" ? "All actors" : a}
            </option>
          ))}
        </select>
      </div>

      {filtered.length === 0 && <div className="empty-state">No audit entries yet — run the pipeline to populate this.</div>}

      <div className="audit-list">
        {filtered.map((entry, i) => {
          const action = entry.detail && entry.detail.action ? entry.detail.action : "";
          const isOpen = openIndex === i;
          return (
            <div className="audit-row" key={i}>
              <div className="audit-row-summary" onClick={() => setOpenIndex(isOpen ? null : i)}>
                <span className="ts">{shortTime(entry.timestamp)}</span>
                <span className="actor">{entry.actor}</span>
                <span className={`event-type ${eventTypeClass(entry.event_type)}`}>{entry.event_type}</span>
                <span>{action}</span>
                <span>{isOpen ? "▾" : "▸"}</span>
              </div>
              {isOpen && <div className="audit-row-detail">{JSON.stringify(entry.detail, null, 2)}</div>}
            </div>
          );
        })}
      </div>
    </div>
  );
}
