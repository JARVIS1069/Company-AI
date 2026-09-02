import React from "react";

function Badge({ passed, pending }) {
  if (pending) return <span className="badge pending">Pending</span>;
  return <span className={`badge ${passed ? "pass" : "fail"}`}>{passed ? "Pass" : "Fail"}</span>;
}

function formatCheckName(key) {
  return key.replace(/_/g, " ");
}

function formatDetail(detail) {
  if (detail == null) return "";
  if (typeof detail === "string") return detail;
  if (typeof detail === "object") {
    // qa_checks nested object (Reviewer's all_qa_checks_passed) -> summarize
    return Object.entries(detail)
      .map(([k, v]) => `${k}:${v && v.passed ? "ok" : "x"}`)
      .join(" ");
  }
  return String(detail);
}

export default function QualityGates({ qaChecks, reviewChecks }) {
  const hasQA = qaChecks && Object.keys(qaChecks).length > 0;
  const hasReview = reviewChecks && Object.keys(reviewChecks).length > 0;

  return (
    <div className="panel">
      <div className="panel-title">
        Quality Gates
        <span className="eyebrow">QA &rarr; Reviewer</span>
      </div>

      <div className="gate-group-label">QA Validator</div>
      {!hasQA && <div className="empty-state" style={{ padding: "8px 0" }}>No run yet</div>}
      {hasQA &&
        Object.entries(qaChecks).map(([key, check]) => (
          <div className="check-row" key={key}>
            <span className="check-name">{formatCheckName(key)}</span>
            <span className="check-detail">{formatDetail(check.detail)}</span>
            <Badge passed={check.passed} />
          </div>
        ))}

      <div className="gate-group-label">Reviewer</div>
      {!hasReview && <div className="empty-state" style={{ padding: "8px 0" }}>No run yet</div>}
      {hasReview &&
        Object.entries(reviewChecks).map(([key, check]) => (
          <div className="check-row" key={key}>
            <span className="check-name">{formatCheckName(key)}</span>
            <span className="check-detail">{formatDetail(check.detail)}</span>
            <Badge passed={check.passed} />
          </div>
        ))}
    </div>
  );
}
