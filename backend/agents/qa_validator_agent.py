"""
QAValidatorAgent — tests data quality, forecast accuracy, and API
correctness against the consolidated report from TeamLead (Data
Engineer + Data Scientist + ML Engineer results). First quality GATE:
passes work to InventoryAnalyst, or blocks it and flags TeamLead.

Phase 5: checks now do real inspection instead of trusting the report
dicts at face value --
    data_quality      -> re-reads the raw CSV and checks schema/nulls/
                         duplicates/date-gaps directly
    forecast_accuracy -> checks MAPE, RMSE, AND MAE against thresholds
                         (Phase 2 only checked MAPE)
    api_correctness   -> actually loads the saved model artifact from
                         disk and runs a real prediction on it
"""
from backend.agents.base_agent import BaseAgent, Message
from backend.ml.validation import check_raw_data_quality, check_model_artifact

MAPE_THRESHOLD = 0.15   # matches the KPI: forecast_MAPE_below_15pct
RMSE_THRESHOLD = 50.0
MAE_THRESHOLD = 40.0

# A representative feature row for exercising the saved model. Values
# are mid-range/typical so this checks "does the model run and return
# something sane", not "is this specific input realistic".
SAMPLE_FEATURE_ROW = {
    "day_of_week": 2,
    "month": 6,
    "is_weekend": 0,
    "lag_7": 50.0,
    "rolling_mean_7": 50.0,
    "rolling_mean_28": 48.0,
    "promotion_flag": 0,
    "sku_code": 0,
}


class QAValidatorAgent(BaseAgent):
    def __init__(self):
        super().__init__("QAValidator", "QAValidator", reports_to="TeamLead")
        self.last_verdict: dict | None = None

    def handle_task(self, message: Message) -> Message:
        if message.action == "submit_for_qa":
            results = message.payload.get("results", {})
            task_id = message.payload.get("task_id")
            checks, passed = self._run_checks(results)

            self.last_verdict = {"task_id": task_id, "checks": checks, "passed": passed}

            if passed:
                message.status = "QA Passed"
                self.send(
                    "InventoryAnalyst",
                    "submit_for_inventory_optimization",
                    {"task_id": task_id, "results": results, "qa_checks": checks},
                    priority="High",
                )
            else:
                message.status = "QA Failed"
                self.send(
                    "TeamLead",
                    "flag_issue",
                    {"task_id": task_id, "checks": checks, "reason": "One or more QA checks failed"},
                    priority="High",
                )
        else:
            message.status = "Acknowledged"

        self.memory.append(message.to_dict())
        return message

    def _run_checks(self, results: dict) -> tuple[dict, bool]:
        """Run each QA check and return (per-check results, overall pass/fail)."""
        checks = {
            "data_quality": self._check_data_quality(),
            "forecast_accuracy": self._check_forecast_accuracy(results.get("DataScientist", {})),
            "api_correctness": self._check_api_correctness(results.get("MLEngineer", {})),
        }
        passed = all(c["passed"] for c in checks.values())
        return checks, passed

    @staticmethod
    def _check_data_quality() -> dict:
        """Re-reads the raw CSV directly rather than trusting DataEngineer's self-report."""
        return check_raw_data_quality()

    @staticmethod
    def _check_forecast_accuracy(report: dict) -> dict:
        mape = report.get("MAPE")
        rmse = report.get("RMSE")
        mae = report.get("MAE")

        mape_ok = mape is not None and mape < MAPE_THRESHOLD
        rmse_ok = rmse is not None and rmse < RMSE_THRESHOLD
        mae_ok = mae is not None and mae < MAE_THRESHOLD
        ok = report.get("status") == "trained" and mape_ok and rmse_ok and mae_ok

        return {
            "passed": ok,
            "detail": (
                f"MAPE={mape} (< {MAPE_THRESHOLD}), "
                f"RMSE={rmse} (< {RMSE_THRESHOLD}), "
                f"MAE={mae} (< {MAE_THRESHOLD})"
            ),
        }

    @staticmethod
    def _check_api_correctness(report: dict) -> dict:
        if report.get("status") != "packaged" or not report.get("artifact_path"):
            return {"passed": False, "detail": f"status={report.get('status')}, no artifact_path"}
        return check_model_artifact(report["artifact_path"], SAMPLE_FEATURE_ROW)
