"""Startup-loaded Azerbaijan cutoff prediction service."""

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from joblib import load

try:
    from scripts.train_cutoff_models import prepare
except ModuleNotFoundError:
    from backend.scripts.train_cutoff_models import prepare

REPO_ROOT = Path(__file__).resolve().parents[4]
DATA_PATH = REPO_ROOT / "data" / "processed" / "azerbaijan_cutoff_history.csv"
METRICS_PATH = REPO_ROOT / "models" / "metrics.json"
ARTIFACT_PATH = REPO_ROOT / "models" / "cutoff_coldstart_AZ.joblib"


@dataclass
class AzerbaijanPredictionService:
    raw: pd.DataFrame | None
    prepared: pd.DataFrame | None
    artifact: dict | None
    metrics: dict
    unavailable_reason: str | None = None

    @classmethod
    def load(cls) -> "AzerbaijanPredictionService":
        metrics = {}
        if METRICS_PATH.exists():
            metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
        if not DATA_PATH.exists():
            return cls(None, None, None, metrics, "Azerbaijan cutoff history is not collected.")
        try:
            raw = pd.read_csv(DATA_PATH)
            raw["program_key"] = raw["source_program_code"].astype(str)
            prepared = prepare(raw.copy())
            artifact = load(ARTIFACT_PATH) if ARTIFACT_PATH.exists() else None
        except Exception as exc:
            return cls(None, None, None, metrics, f"Azerbaijan model data could not be loaded: {exc}")
        return cls(raw, prepared, artifact, metrics)

    @property
    def ready(self) -> bool:
        return self.raw is not None

    def _run_id(self) -> str | None:
        return self.metrics.get("per_country", {}).get("AZ", {}).get("trained_at")

    @staticmethod
    def _band(center: float, interval: dict | None) -> tuple[float, float]:
        interval = interval or {"lower_offset": -50, "upper_offset": 50}
        return max(0.0, center + float(interval["lower_offset"])), min(
            700.0, center + float(interval["upper_offset"])
        )

    def _prediction(self, program_code: str) -> dict:
        assert self.raw is not None
        history = self.raw[self.raw["program_key"].astype(str) == str(program_code)].sort_values("intake_year")
        if history.empty:
            return {
                "status": "predicted",
                "reason": "cutoff_not_indicated_fallback_to_full_scholarship_standard",
                "program_code": str(program_code),
                "scholarship_type": "dövlət sifarişli (full scholarship)",
                "prediction_type": "standard_threshold",
                "model": "Full scholarship benchmark (650+)",
                "predicted_cutoff": 650.0,
                "lower_cutoff": 650.0,
                "upper_cutoff": 700.0,
                "cutoff_note": "Cutoff for full scholarship is 650+ DİM score if not indicated",
            }

        latest = history.iloc[-1]
        scholarship_type = str(latest.get("scholarship_type") or "dövlət sifarişli (full scholarship)")
        common = {
            "program_code": str(program_code),
            "university_name": str(latest.get("university_name", "")),
            "department_name": str(latest.get("department_name", "")),
            "score_type": latest.get("score_type"),
            "scholarship_type": scholarship_type,
            "history_years": int(history["intake_year"].nunique()),
            "run_id": self._run_id(),
        }
        az_metrics = self.metrics.get("per_country", {}).get("AZ", {})
        if len(history) >= 1 and pd.notna(latest.get("cutoff_value")):
            center = float(latest["cutoff_value"])
            lower, upper = self._band(center, az_metrics.get("forecasting", {}).get("persistence_interval"))
            return {
                **common,
                "status": "predicted",
                "prediction_type": "forecast" if len(history) >= 2 else "latest_published",
                "model": "persistence" if len(history) >= 2 else "latest_intake",
                "target_year": int(latest["intake_year"]) + 1,
                "predicted_cutoff": center,
                "lower_cutoff": lower,
                "upper_cutoff": upper,
                "cutoff_note": (
                    "Indicated cutoff from DİM history (clears 650+ full scholarship benchmark)"
                    if center >= 650.0
                    else "Indicated cutoff from DİM history"
                ),
            }

        # If cold-start model or features are unavailable or cutoff not indicated, cutoff for full scholarship is 650+
        if self.artifact is None or self.prepared is None:
            return {
                **common,
                "status": "predicted",
                "prediction_type": "standard_threshold",
                "model": "Full scholarship benchmark (650+)",
                "target_year": int(latest.get("intake_year", 2025)) + 1,
                "predicted_cutoff": 650.0,
                "lower_cutoff": 650.0,
                "upper_cutoff": 700.0,
                "cutoff_note": "Cutoff for full scholarship is 650+ DİM score if not indicated",
            }
        prepared_row = self.prepared[self.prepared["program_key"].astype(str) == str(program_code)].tail(1)
        if prepared_row.empty:
            return {
                **common,
                "status": "predicted",
                "prediction_type": "standard_threshold",
                "model": "Full scholarship benchmark (650+)",
                "target_year": int(latest.get("intake_year", 2025)) + 1,
                "predicted_cutoff": 650.0,
                "lower_cutoff": 650.0,
                "upper_cutoff": 700.0,
                "cutoff_note": "Cutoff for full scholarship is 650+ DİM score if not indicated",
            }
        features = self.artifact["features"]
        model = self.artifact["model"]
        prediction = float(model.predict(prepared_row[features])[0])
        lower, upper = self._band(prediction, self.artifact.get("interval"))
        return {
            **common,
            "status": "predicted",
            "prediction_type": "cold_start",
            "model": self.artifact.get("name", "cold-start model"),
            "target_year": int(latest["intake_year"]) + 1,
            "predicted_cutoff": prediction,
            "lower_cutoff": lower,
            "upper_cutoff": upper,
            "cutoff_note": "Cold-start predicted cutoff",
        }

    def predict(self, program_code: str) -> dict:
        if not self.ready:
            return {"status": "absent", "reason": self.unavailable_reason}
        return self._prediction(program_code)

    def list_predictions(self, university: str | None = None, group: str | None = None) -> list[dict]:
        if not self.ready:
            return []
        assert self.raw is not None
        latest = self.raw.sort_values("intake_year").groupby("program_key", as_index=False).tail(1)
        if university:
            u_clean = university.strip().lower()
            bhos_aliases = [
                "banm", "bhos", "baku higher oil school", "bakı ali neft məktəbi",
                "baki ali neft mektebi", "neft məktəbi", "neft mektebi", "oil school"
            ]
            if any(alias in u_clean or u_clean in alias for alias in bhos_aliases):
                latest = latest[
                    latest["university_name"].str.contains(
                        "Baku Higher Oil School|BANM|BHOS|Neft", case=False, na=False
                    )
                ]
            else:
                latest = latest[latest["university_name"].str.contains(university, case=False, na=False)]
        if group:
            latest = latest[latest["score_type"].astype(str).str.contains(group, case=False, na=False)]
        return [self._prediction(str(code)) for code in latest["program_key"]]