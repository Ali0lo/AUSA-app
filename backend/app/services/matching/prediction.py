from pathlib import Path
from typing import Any, Dict, Optional
import joblib
import pandas as pd
from app.schemas.matching import ProgramRequirements, StudentProfile


class AdmissionPredictor:
    """
    Singleton Machine Learning Admission Predictor Service (ADR-0001 & ADR-0002).
    
    Loads serialized scikit-learn model weights on startup to ensure fast, 
    in-memory inference without reloading weights per request.
    """
    _instance: Optional["AdmissionPredictor"] = None
    _models: Dict[str, Any] = {}

    def __new__(cls) -> "AdmissionPredictor":
        if cls._instance is None:
            cls._instance = super(AdmissionPredictor, cls).__new__(cls)
            cls._instance._load_models()
        return cls._instance

    def _load_models(self) -> None:
        """Load trained .joblib model artifacts from backend/app/models/ml_weights/."""
        weights_dir = Path(__file__).parent.parent.parent / "models" / "ml_weights"
        turkey_path = weights_dir / "turkey_cutoff_model.joblib"
        usa_path = weights_dir / "usa_cutoff_model.joblib"

        if turkey_path.exists():
            try:
                self._models["TR"] = joblib.load(turkey_path)
            except Exception as e:
                print(f"[AdmissionPredictor Warning] Failed to load Turkey model: {e}")

        if usa_path.exists():
            try:
                self._models["US"] = joblib.load(usa_path)
            except Exception as e:
                print(f"[AdmissionPredictor Warning] Failed to load USA model: {e}")

    def calculate_admission_probability(
        self,
        student_profile: StudentProfile,
        program: ProgramRequirements
    ) -> float:
        """
        Calculate admission cutoff probability (0.0 to 1.0) using trained ML models.

        Args:
            student_profile: Student academic parameters.
            program: Target university program requirements.

        Returns:
            Float probability value between 0.0 and 1.0.
        """
        country = (program.country or "").upper().strip()

        if "TURKEY" in country or "TÜRKIYE" in country or country == "TR":
            target_country = "TR"
        elif "UNITED STATES" in country or "USA" in country or country == "US":
            target_country = "US"
        else:
            target_country = country

        # Extract features matching model training schema
        student_ielts = student_profile.ielts
        if student_ielts is None and student_profile.toefl is not None:
            from app.services.matching.scoring import convert_toefl_to_ielts_equivalent
            student_ielts = convert_toefl_to_ielts_equivalent(student_profile.toefl)
        if student_ielts is None:
            student_ielts = 6.0

        min_gpa = program.min_gpa if program.min_gpa is not None else 2.5
        min_ielts = program.min_ielts if program.min_ielts is not None else 6.0
        tuition = program.tuition_fee if program.tuition_fee is not None else 0.0

        features = pd.DataFrame([{
            "gpa": student_profile.gpa,
            "ielts": student_ielts,
            "min_gpa": min_gpa,
            "min_ielts": min_ielts,
            "tuition_fee": tuition,
        }])

        model = self._models.get(target_country)
        if model is not None:
            try:
                if hasattr(model, "predict_proba"):
                    proba = model.predict_proba(features)[0][1]
                else:
                    pred = model.predict(features)[0]
                    proba = max(0.0, min(1.0, float(pred)))
                return round(float(proba), 2)
            except Exception:
                pass

        # Heuristic fallback calculation if model weights not yet generated
        gpa_diff = student_profile.gpa - min_gpa
        ielts_diff = student_ielts - min_ielts

        base_score = 0.50 + (gpa_diff * 0.35) + (ielts_diff * 0.15)
        probability = max(0.05, min(0.98, round(base_score, 2)))
        return probability


# Export singleton predictor instance
admission_predictor = AdmissionPredictor()

