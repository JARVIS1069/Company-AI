// Fixed layout for the org chart wallboard. Each node maps to a real
// actor name from the backend's audit log. "President" appears twice
// (project approval, then final release approval) so it's split into
// two visual nodes disambiguated by `occurrence`.

const CX = 450; // center x
const BOX_W = 176;
const BOX_H = 56;

export const NODES = [
  { id: "president-1", actor: "President", occurrence: 1, label: "President", sub: "Approves Project", x: CX, y: 40 },
  { id: "vp", actor: "VP", occurrence: 1, label: "VP", sub: "Sets Company KPIs", x: CX, y: 128 },
  { id: "manager", actor: "Manager", occurrence: 1, label: "Manager", sub: "Plans & Assigns", x: CX, y: 216 },
  { id: "teamlead", actor: "TeamLead", occurrence: 1, label: "Team Lead", sub: "Picks Approach", x: CX, y: 304 },

  { id: "data-engineer", actor: "DataEngineer", occurrence: 1, label: "Data Engineer", sub: "Cleans Data", x: CX - 230, y: 404 },
  { id: "data-scientist", actor: "DataScientist", occurrence: 1, label: "Data Scientist", sub: "Trains Model", x: CX, y: 404 },
  { id: "ml-engineer", actor: "MLEngineer", occurrence: 1, label: "ML Engineer", sub: "Packages Model", x: CX + 230, y: 404 },

  { id: "qa", actor: "QAValidator", occurrence: 1, label: "QA Validator", sub: "Runs Quality Gate", x: CX, y: 504 },
  { id: "inventory", actor: "InventoryAnalyst", occurrence: 1, label: "Inventory Analyst", sub: "Reorder Recs", x: CX, y: 592 },
  { id: "reviewer", actor: "Reviewer", occurrence: 1, label: "Reviewer", sub: "Checks Evidence", x: CX, y: 680 },
  { id: "president-2", actor: "President", occurrence: 2, label: "President", sub: "Final Approval", x: CX, y: 768 },
  { id: "release", actor: "Release", occurrence: 1, label: "Release", sub: "Ships to Production", x: CX, y: 856 },
];

export const CONNECTORS = [
  { id: "c1", from: "president-1", to: "vp" },
  { id: "c2", from: "vp", to: "manager" },
  { id: "c3", from: "manager", to: "teamlead" },
  // TeamLead <-> specialists is a two-way edge in reality: TeamLead
  // dispatches out, then each specialist reports back to TeamLead on
  // the SAME edge. OrgChart lights these edges when either endpoint
  // is active, so both directions register visually.
  { id: "c4a", from: "teamlead", to: "data-engineer" },
  { id: "c4b", from: "teamlead", to: "data-scientist" },
  { id: "c4c", from: "teamlead", to: "ml-engineer" },
  { id: "c5", from: "teamlead", to: "qa" }, // consolidated submit_for_qa, after all 3 report in
  { id: "c6", from: "qa", to: "inventory" },
  { id: "c7", from: "inventory", to: "reviewer" },
  { id: "c8", from: "reviewer", to: "president-2" },
  { id: "c9", from: "president-2", to: "release" },
];

export const BOX_SIZE = { w: BOX_W, h: BOX_H };
export const CANVAS = { width: 900, height: 924 };

// Pipeline phases per your roadmap, mapped to which node completing
// means that phase is done.
export const PIPELINE_PHASES = [
  { key: "plan", label: "Plan", doneWhenNode: "manager" },
  { key: "prepare", label: "Prepare Data", doneWhenNode: "data-engineer" },
  { key: "forecast", label: "Forecast Demand", doneWhenNode: "data-scientist" },
  { key: "optimize", label: "Optimize Inventory", doneWhenNode: "inventory" },
  { key: "validate", label: "Validate", doneWhenNode: "qa" },
  { key: "review", label: "Review", doneWhenNode: "reviewer" },
  { key: "approve", label: "Approve", doneWhenNode: "president-2" },
  { key: "release", label: "Release", doneWhenNode: "release" },
];
