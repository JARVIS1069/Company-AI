import React, { useState } from "react";

const STATUS_LABEL = {
  idle: "Idle",
  running: "Running",
  done: "Released",
  error: "Error",
};

export default function Header({ runPhase, onKickoff }) {
  const [project, setProject] = useState("Demand Forecasting & Inventory Optimization");

  function handleSubmit(e) {
    e.preventDefault();
    if (runPhase === "running") return;
    onKickoff(project.trim() || "Untitled Project");
  }

  return (
    <div className="header">
      <div className="wordmark">
        <h1>COMPANY&nbsp;AI</h1>
        <span className="tag">Multi-Agent Org &middot; Demand Forecasting</span>
      </div>

      <form className="kickoff-form" onSubmit={handleSubmit}>
        <input
          type="text"
          value={project}
          onChange={(e) => setProject(e.target.value)}
          placeholder="Project name"
          aria-label="Project name"
        />
        <button type="submit" className="btn-start" disabled={runPhase === "running"}>
          {runPhase === "running" ? "Running…" : "Start Project"}
        </button>
        <span className={`status-pill ${runPhase}`}>{STATUS_LABEL[runPhase] || "Idle"}</span>
      </form>
    </div>
  );
}
