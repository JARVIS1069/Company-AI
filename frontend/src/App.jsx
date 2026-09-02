import React, { useState } from "react";
import Header from "./components/Header.jsx";
import OrgChart from "./components/OrgChart.jsx";
import PipelineTimeline from "./components/PipelineTimeline.jsx";
import QualityGates from "./components/QualityGates.jsx";
import InventoryTable from "./components/InventoryTable.jsx";
import AuditLog from "./components/AuditLog.jsx";
import { NODES } from "./orgLayout.js";
import { kickoffProject, fetchAuditLog } from "./api.js";

const STEP_STAGGER_MS = 380; // simulated pacing between each real handoff

function initialNodeStatus() {
  const s = {};
  NODES.forEach((n) => (s[n.id] = "idle"));
  return s;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Maps the audit log's RECEIVE events, in real order, to visual nodes.
 *
 * Note: this backend's event bus is synchronous, so agents don't
 * actually execute in parallel in wall-clock time even where the org
 * chart shows a branch (e.g. TeamLead's 3 specialists) -- each one
 * fully completes, including reporting back to TeamLead, before the
 * next starts. So this animates every real handoff as its own
 * sequential step in the order it actually happened, rather than
 * guessing at "simultaneous" bursts from timestamps (unreliable --
 * fast-but-sequential steps can land under any fixed threshold by
 * coincidence). TeamLead legitimately appears multiple times here
 * (initial assignment + one report-back per specialist) since it
 * really does receive that many messages. President appears twice
 * (project approval, then final release approval) so occurrence count
 * disambiguates which visual node a given RECEIVE maps to.
 */
function buildSteps(entries) {
  const receiveEntries = entries.filter((e) => e.event_type === "RECEIVE");
  const actorOccurrence = {};

  return receiveEntries
    .map((e) => {
      actorOccurrence[e.actor] = (actorOccurrence[e.actor] || 0) + 1;
      const occ = actorOccurrence[e.actor];
      const node = NODES.find((n) => n.actor === e.actor && n.occurrence === occ) || NODES.find((n) => n.actor === e.actor);
      return node ? node.id : null;
    })
    .filter(Boolean);
}

function findLastByActorAction(entries, actor, action) {
  for (let i = entries.length - 1; i >= 0; i--) {
    const e = entries[i];
    if (e.actor === actor && e.detail && e.detail.action === action) return e;
  }
  return null;
}

export default function App() {
  const [runPhase, setRunPhase] = useState("idle"); // idle | running | done | error
  const [nodeStatus, setNodeStatus] = useState(initialNodeStatus());
  const [auditEntries, setAuditEntries] = useState([]);
  const [qaChecks, setQaChecks] = useState(null);
  const [reviewChecks, setReviewChecks] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [errorMessage, setErrorMessage] = useState(null);

  async function handleKickoff(project) {
    setRunPhase("running");
    setErrorMessage(null);
    setNodeStatus(initialNodeStatus());
    setQaChecks(null);
    setReviewChecks(null);
    setRecommendations([]);

    try {
      await kickoffProject(project);
      const entries = await fetchAuditLog();
      setAuditEntries(entries);

      const steps = buildSteps(entries);
      await animateSteps(steps);

      // Parse final panel state from the audit log, checking the
      // pass path first and falling back to the fail path so the
      // dashboard reflects whichever actually happened.
      const qaPass = findLastByActorAction(entries, "QAValidator", "submit_for_inventory_optimization");
      const qaFail = findLastByActorAction(entries, "QAValidator", "flag_issue");
      if (qaPass) setQaChecks(qaPass.detail.payload.qa_checks);
      else if (qaFail) setQaChecks(qaFail.detail.payload.checks);

      const reviewPass = findLastByActorAction(entries, "Reviewer", "approve_for_president");
      const reviewFail = findLastByActorAction(entries, "Reviewer", "request_changes");
      if (reviewPass) {
        setReviewChecks(reviewPass.detail.payload.review_requirements);
        setRecommendations(reviewPass.detail.payload.inventory_recommendations || []);
      } else if (reviewFail) {
        setReviewChecks(reviewFail.detail.payload.requirements);
      }

      const releaseEntry = entries.find((e) => e.actor === "Release" && e.event_type === "RELEASE_TO_PRODUCTION");
      const releaseBlockedEntry = entries.find((e) => e.actor === "Release" && e.event_type === "RELEASE_BLOCKED");

      setRunPhase(releaseEntry ? "done" : releaseBlockedEntry ? "error" : "done");
    } catch (err) {
      console.error(err);
      setErrorMessage(err.message || String(err));
      setRunPhase("error");
    }
  }

  async function animateSteps(steps) {
    for (const nodeId of steps) {
      setNodeStatus((prev) => ({ ...prev, [nodeId]: "active" }));
      await sleep(STEP_STAGGER_MS);
      setNodeStatus((prev) => ({ ...prev, [nodeId]: "done" }));
    }
  }

  return (
    <div className="app">
      <Header runPhase={runPhase} onKickoff={handleKickoff} />

      {errorMessage && (
        <div className="error-banner">
          Could not reach the backend at http://127.0.0.1:8000 — is <code>uvicorn</code> running? ({errorMessage})
        </div>
      )}

      <div className="dashboard">
        <OrgChart nodeStatus={nodeStatus} />
        <div className="side-column">
          <PipelineTimeline nodeStatus={nodeStatus} />
          <QualityGates qaChecks={qaChecks} reviewChecks={reviewChecks} />
        </div>
        <InventoryTable recommendations={recommendations} />
        <AuditLog entries={auditEntries} />
      </div>
    </div>
  );
}
