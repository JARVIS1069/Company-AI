# System Architecture

![Company AI System Architecture](architecture-diagram.svg)

The architecture shows:
- **Browser** connects to the **React + Vite frontend** via HTTP
- **FastAPI backend** exposes REST endpoints (`/org`, `/kickoff`, `/audit-log`, `/message`, `/history`)
- **Event Bus** enables async pub/sub messaging between agents
- **RBAC / Permissions** enforces role-based access control on all message sends
- **Audit Log** maintains an append-only trail of every send, receive, and denial
- **11 Agents** orchestrate the entire pipeline from planning to release
- **ML Layer** handles data preparation, model training, inventory optimization, and validation
- **Data Layer** stores CSV datasets and trained model artifacts

Notes
- Ensure `architecture-diagram.svg` is committed at the repository root (next to this README). If it's in a subfolder, update the image path accordingly (for example: `docs/architecture-diagram.svg`).
- If GitHub does not render your SVG (rare), convert it to PNG and reference the PNG instead.
