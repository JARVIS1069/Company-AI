import React from "react";

export default function InventoryTable({ recommendations }) {
  const hasData = recommendations && recommendations.length > 0;

  return (
    <div className="panel full-width">
      <div className="panel-title">
        Inventory Recommendations
        <span className="eyebrow">{hasData ? `${recommendations.length} SKUs` : "awaiting run"}</span>
      </div>

      {!hasData && <div className="empty-state">Run the pipeline to generate reorder recommendations.</div>}

      {hasData && (
        <table className="inv-table">
          <thead>
            <tr>
              <th>SKU</th>
              <th>Avg Daily Demand</th>
              <th>Lead Time</th>
              <th>Safety Stock</th>
              <th>Reorder Point</th>
              <th>Current Stock</th>
              <th>Status</th>
              <th>Recommended Action</th>
            </tr>
          </thead>
          <tbody>
            {recommendations.map((r) => (
              <tr key={r.sku}>
                <td>{r.sku}</td>
                <td>{r.avg_daily_demand_forecast}</td>
                <td>{r.lead_time_days}d</td>
                <td>{r.safety_stock}</td>
                <td>{r.reorder_point}</td>
                <td>{r.current_stock}</td>
                <td>
                  <span className={`risk-flag ${r.stockout_risk ? "at-risk" : "ok"}`}>
                    {r.stockout_risk ? "At Risk" : "OK"}
                  </span>
                </td>
                <td>{r.recommended_action}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
