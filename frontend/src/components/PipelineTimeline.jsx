import React from "react";
import { PIPELINE_PHASES } from "../orgLayout.js";

export default function PipelineTimeline({ nodeStatus }) {
  return (
    <div className="panel">
      <div className="panel-title">
        Pipeline
        <span className="eyebrow">{PIPELINE_PHASES.length} phases</span>
      </div>
      {PIPELINE_PHASES.map((phase, i) => {
        const status = nodeStatus[phase.doneWhenNode] || "idle";
        const stepState = status === "done" || status === "blocked" ? "done" : status === "active" ? "active" : "";
        return (
          <div key={phase.key} className={`timeline-step ${stepState}`}>
            <span className="num">{String(i + 1).padStart(2, "0")}</span>
            <span className="dot" />
            <span className="label">{phase.label}</span>
          </div>
        );
      })}
    </div>
  );
}
