import React from "react";
import { NODES, CONNECTORS, BOX_SIZE, CANVAS } from "../orgLayout.js";

const { w: BOX_W, h: BOX_H } = BOX_SIZE;

function nodeById(id) {
  return NODES.find((n) => n.id === id);
}

function connectorPath(from, to) {
  const x1 = from.x;
  const y1 = from.y + BOX_H / 2;
  const x2 = to.x;
  const y2 = to.y - BOX_H / 2;

  if (x1 === x2) {
    return `M ${x1} ${y1} L ${x2} ${y2}`;
  }
  // Elbow curve for fan-out / converge branches
  const midY = y1 + (y2 - y1) / 2;
  return `M ${x1} ${y1} C ${x1} ${midY}, ${x2} ${midY}, ${x2} ${y2}`;
}

export default function OrgChart({ nodeStatus }) {
  return (
    <div className="panel org-chart-panel">
      <div className="panel-title">
        Org Chart
        <span className="eyebrow">live pipeline trace</span>
      </div>
      <svg viewBox={`0 0 ${CANVAS.width} ${CANVAS.height}`} xmlns="http://www.w3.org/2000/svg">
        {CONNECTORS.map((c) => {
          const from = nodeById(c.from);
          const to = nodeById(c.to);
          const fromStatus = nodeStatus[c.from] || "idle";
          const toStatus = nodeStatus[c.to] || "idle";
          const active = fromStatus === "active" || toStatus === "active";
          const settled = fromStatus === "done" || toStatus === "done" || fromStatus === "blocked" || toStatus === "blocked";
          const cls = active ? "lit" : settled ? "done" : "";
          return (
            <path
              key={c.id}
              d={connectorPath(from, to)}
              className={`org-connector ${cls}`}
            />
          );
        })}

        {NODES.map((n) => {
          const status = nodeStatus[n.id] || "idle";
          return (
            <g key={n.id}>
              <rect
                x={n.x - BOX_W / 2}
                y={n.y - BOX_H / 2}
                width={BOX_W}
                height={BOX_H}
                rx={5}
                className={`org-node-box ${status}`}
              />
              <text x={n.x} y={n.y - 3} textAnchor="middle" className="org-node-label">
                {n.label}
              </text>
              <text x={n.x} y={n.y + 15} textAnchor="middle" className="org-node-sub">
                {n.sub}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
