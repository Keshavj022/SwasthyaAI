"""
Lab Results Agent (Task 11).

Interprets structured laboratory results:
- Classifies each result as Normal / Low / High / Critical
- Provides a plain-language explanation of what each value means
- Detects clinically meaningful patterns across multiple results
- Flags critical values requiring immediate medical attention
- Suggests sensible follow-up tests
- Always attaches a medical disclaimer

This is a deterministic, rule-based interpreter built on hardcoded reference
ranges. It is decision SUPPORT only and never claims diagnostic authority.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from orchestrator.base import BaseAgent, AgentRequest, AgentResponse

try:  # Pydantic schemas are the canonical I/O contract.
    from schemas.lab_results import LabResultInput  # type: ignore
except Exception:  # pragma: no cover - schemas always present in app runtime
    LabResultInput = None  # type: ignore


# ---------------------------------------------------------------------------
# Reference ranges (hardcoded per spec)
# ---------------------------------------------------------------------------

REFERENCE_RANGES: Dict[str, Dict[str, Any]] = {
    "hemoglobin": {"unit": "g/dL", "adult_male": (13.5, 17.5), "adult_female": (12.0, 15.5)},
    "hba1c": {"unit": "%", "normal": (0, 5.6), "prediabetes": (5.7, 6.4), "diabetes": (6.5, 99)},
    "fasting_glucose": {"unit": "mg/dL", "normal": (70, 99), "prediabetes": (100, 125), "diabetes": (126, 9999)},
    "total_cholesterol": {"unit": "mg/dL", "desirable": (0, 199), "borderline": (200, 239), "high": (240, 9999)},
    "ldl": {"unit": "mg/dL", "optimal": (0, 99), "near_optimal": (100, 129), "borderline_high": (130, 159), "high": (160, 189), "very_high": (190, 9999)},
    "hdl": {"unit": "mg/dL", "low_risk": (60, 9999), "medium_risk": (40, 59), "high_risk": (0, 39)},
    "triglycerides": {"unit": "mg/dL", "normal": (0, 149), "borderline": (150, 199), "high": (200, 499), "very_high": (500, 9999)},
    "creatinine": {"unit": "mg/dL", "adult_male": (0.74, 1.35), "adult_female": (0.59, 1.04)},
    "urea": {"unit": "mg/dL", "normal": (7, 20)},
    "sgpt_alt": {"unit": "U/L", "adult_male": (7, 56), "adult_female": (7, 45)},
    "sgot_ast": {"unit": "U/L", "normal": (10, 40)},
    "tsh": {"unit": "mIU/L", "normal": (0.4, 4.0)},
    "wbc": {"unit": "10^3/μL", "normal": (4.5, 11.0)},
    "platelets": {"unit": "10^3/μL", "normal": (150, 400)},
    "sodium": {"unit": "mEq/L", "normal": (136, 145)},
    "potassium": {"unit": "mEq/L", "normal": (3.5, 5.0)},
}

# Common aliases mapped to canonical reference-range keys.
TEST_ALIASES: Dict[str, str] = {
    "a1c": "hba1c",
    "hemoglobin a1c": "hba1c",
    "glycated hemoglobin": "hba1c",
    "glucose": "fasting_glucose",
    "fasting blood sugar": "fasting_glucose",
    "fbs": "fasting_glucose",
    "blood glucose": "fasting_glucose",
    "cholesterol": "total_cholesterol",
    "ldl cholesterol": "ldl",
    "ldl-c": "ldl",
    "hdl cholesterol": "hdl",
    "hdl-c": "hdl",
    "trigs": "triglycerides",
    "tg": "triglycerides",
    "alt": "sgpt_alt",
    "sgpt": "sgpt_alt",
    "ast": "sgot_ast",
    "sgot": "sgot_ast",
    "thyroid stimulating hormone": "tsh",
    "white blood cells": "wbc",
    "white blood cell count": "wbc",
    "leukocytes": "wbc",
    "platelet count": "platelets",
    "plt": "platelets",
    "hb": "hemoglobin",
    "hgb": "hemoglobin",
    "k": "potassium",
    "k+": "potassium",
    "na": "sodium",
    "na+": "sodium",
    "bun": "urea",
    "creat": "creatinine",
}

# Critical thresholds — must trigger an immediate alert (spec §"Critical thresholds").
# Each entry: (low_critical, high_critical) on the canonical key's unit.
CRITICAL_THRESHOLDS: Dict[str, Tuple[Optional[float], Optional[float]]] = {
    "potassium": (2.5, 6.5),       # mEq/L
    "sodium": (120, 155),          # mEq/L
    "fasting_glucose": (50, 500),  # mg/dL
    "hemoglobin": (7.0, None),     # g/dL (critical low only)
    "platelets": (50, None),       # 10^3/μL  (50,000 cells)
}

# Plain-language one-liners describing what each test measures.
TEST_DESCRIPTIONS: Dict[str, str] = {
    "hemoglobin": "the protein in red blood cells that carries oxygen around your body",
    "hba1c": "your average blood sugar over the past 2–3 months",
    "fasting_glucose": "your blood sugar level after fasting",
    "total_cholesterol": "the total amount of cholesterol in your blood",
    "ldl": "\"bad\" cholesterol that can build up in your arteries",
    "hdl": "\"good\" cholesterol that helps clear fat from your arteries",
    "triglycerides": "a type of fat in your blood",
    "creatinine": "a waste product that reflects how well your kidneys are working",
    "urea": "a waste product (blood urea nitrogen) filtered by your kidneys",
    "sgpt_alt": "a liver enzyme (ALT) that rises when the liver is stressed",
    "sgot_ast": "a liver/muscle enzyme (AST) that rises with tissue injury",
    "tsh": "the hormone that controls your thyroid gland",
    "wbc": "white blood cells, part of your immune system",
    "platelets": "cells that help your blood clot",
    "sodium": "an electrolyte that balances fluid in your body",
    "potassium": "an electrolyte important for nerve and heart function",
}


class LabResultsAgent(BaseAgent):
    """
    Deterministic interpreter for common laboratory tests.
    Registered with the orchestrator under the name 'lab_results'.
    """

    REFERENCE_RANGES = REFERENCE_RANGES

    def __init__(self) -> None:
        super().__init__()
        self.name = "lab_results"

    # ------------------------------------------------------------------ #
    # Orchestrator entrypoint
    # ------------------------------------------------------------------ #

    async def process(self, request: AgentRequest) -> AgentResponse:
        """
        Interpret lab results passed via context.

        Expected context keys:
        - lab_results / results: list of {test_name, value, unit?}
        - patient_age / age: int
        - patient_sex / sex / gender: str
        """
        ctx = request.context or {}
        raw_results = ctx.get("lab_results") or ctx.get("results") or []
        age = ctx.get("patient_age", ctx.get("age"))
        sex = ctx.get("patient_sex", ctx.get("sex", ctx.get("gender")))

        parsed = self._coerce_inputs(raw_results)

        if not parsed:
            return AgentResponse(
                success=True,
                agent_name=self.name,
                data={
                    "message": (
                        "No structured lab values were provided. Send results as a "
                        "list of {test_name, value, unit} objects to interpret them."
                    ),
                    "results": [],
                    "summary": "",
                    "patterns_detected": [],
                    "critical_flags": [],
                    "follow_up_tests": [],
                    "disclaimer": self.get_disclaimer(),
                    "stub_mode": False,
                },
                confidence=0.4,
                reasoning="No lab values supplied; nothing to interpret.",
            )

        interpretation = self.interpret_results(parsed, age, sex)

        critical_flags = interpretation["critical_flags"]
        red_flags = list(critical_flags)
        requires_escalation = bool(critical_flags)

        return AgentResponse(
            success=True,
            agent_name=self.name,
            data=interpretation,
            confidence=0.82,
            reasoning=(
                "Rule-based interpretation against standard reference ranges "
                f"for {len(parsed)} result(s)."
            ),
            red_flags=red_flags,
            requires_escalation=requires_escalation,
            suggested_agents=["communication"] if not requires_escalation else ["triage"],
        )

    # ------------------------------------------------------------------ #
    # Core interpretation
    # ------------------------------------------------------------------ #

    def interpret_results(
        self,
        results: List[Any],
        patient_age: Optional[int] = None,
        patient_sex: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Interpret a list of LabResultInput-like objects into the response dict."""
        interpreted: List[Dict[str, Any]] = []

        for item in results:
            test_name, value, unit = self._unpack(item)
            canonical = self._canonical_key(test_name)
            status = self.get_result_status(test_name, value, patient_age, patient_sex)
            ref_range = self._reference_range_str(canonical, patient_sex)
            display_unit = unit or (REFERENCE_RANGES.get(canonical, {}).get("unit") if canonical else "") or ""
            explanation = self._explain(canonical, test_name, value, status, patient_sex)
            action_needed = status in ("high", "low", "critical")

            interpreted.append({
                "test_name": test_name,
                "value": value,
                "unit": display_unit,
                "status": status,
                "reference_range": ref_range,
                "explanation": explanation,
                "action_needed": action_needed,
            })

        return {
            "results": interpreted,
            "summary": self.generate_summary(results, patient_age, patient_sex),
            "patterns_detected": self.detect_patterns(results, patient_age, patient_sex),
            "critical_flags": self.get_critical_flags(results),
            "follow_up_tests": self._follow_up_tests(results, patient_age, patient_sex),
            "disclaimer": self.get_disclaimer(),
            "stub_mode": False,
        }

    def get_result_status(
        self,
        test_name: str,
        value: float,
        age: Optional[int] = None,
        sex: Optional[str] = None,
    ) -> str:
        """Return 'normal' | 'low' | 'high' | 'critical' for a single value."""
        canonical = self._canonical_key(test_name)

        # 1) Critical thresholds always win.
        if canonical in CRITICAL_THRESHOLDS:
            low_c, high_c = CRITICAL_THRESHOLDS[canonical]
            if low_c is not None and value < low_c:
                return "critical"
            if high_c is not None and value > high_c:
                return "critical"

        if not canonical or canonical not in REFERENCE_RANGES:
            return "normal"  # Unknown test — cannot classify, treat as informational.

        spec = REFERENCE_RANGES[canonical]

        # 2) Sex-specific simple ranges (hemoglobin, creatinine, sgpt_alt).
        sex_key = self._sex_key(sex)
        if sex_key in spec and isinstance(spec[sex_key], tuple):
            low, high = spec[sex_key]
            if value < low:
                return "low"
            if value > high:
                return "high"
            return "normal"

        # 3) Single 'normal' range tests.
        if "normal" in spec and isinstance(spec["normal"], tuple) and self._is_single_range(spec):
            low, high = spec["normal"]
            if value < low:
                return "low"
            if value > high:
                return "high"
            return "normal"

        # 4) Multi-band tests (hba1c, glucose, cholesterol, ldl, hdl, triglycerides).
        return self._banded_status(canonical, value, spec)

    def generate_summary(
        self,
        results: List[Any],
        patient_age: Optional[int] = None,
        patient_sex: Optional[str] = None,
    ) -> str:
        """Build a plain-language summary paragraph."""
        if not results:
            return "No lab values were provided to summarize."

        normal, abnormal, critical = [], [], []
        for item in results:
            test_name, value, _ = self._unpack(item)
            status = self.get_result_status(test_name, value, patient_age, patient_sex)
            label = self._friendly_name(test_name)
            if status == "critical":
                critical.append(label)
            elif status in ("high", "low"):
                abnormal.append(f"{label} ({status})")
            else:
                normal.append(label)

        parts: List[str] = []
        total = len(results)
        parts.append(f"You submitted {total} lab value{'s' if total != 1 else ''}.")

        if critical:
            parts.append(
                "Some values are in the critical range and need urgent attention: "
                + ", ".join(critical) + "."
            )
        if abnormal:
            parts.append(
                "The following are outside the typical reference range: "
                + ", ".join(abnormal) + "."
            )
        if normal and not abnormal and not critical:
            parts.append("All submitted values fall within their typical reference ranges.")
        elif normal:
            parts.append("Within the normal range: " + ", ".join(normal) + ".")

        parts.append(
            "These results are a snapshot in time and should be reviewed by a "
            "clinician alongside your symptoms and history."
        )
        return " ".join(parts)

    def detect_patterns(
        self,
        results: List[Any],
        patient_age: Optional[int] = None,
        patient_sex: Optional[str] = None,
    ) -> List[str]:
        """Identify clinically meaningful patterns across multiple results."""
        values: Dict[str, float] = {}
        statuses: Dict[str, str] = {}
        for item in results:
            test_name, value, _ = self._unpack(item)
            canonical = self._canonical_key(test_name)
            if canonical:
                values[canonical] = value
                statuses[canonical] = self.get_result_status(test_name, value, patient_age, patient_sex)

        patterns: List[str] = []

        # Diabetes risk: elevated glucose + elevated HbA1c.
        glucose_high = statuses.get("fasting_glucose") in ("high", "critical")
        a1c_high = statuses.get("hba1c") in ("high", "critical")
        if glucose_high and a1c_high:
            patterns.append(
                "Both fasting glucose and HbA1c are elevated, which together "
                "suggest impaired blood-sugar control (possible prediabetes or "
                "diabetes). Discuss this combination with your doctor."
            )
        elif a1c_high or glucose_high:
            if "hba1c" in values and values["hba1c"] >= 6.5:
                patterns.append(
                    "HbA1c is in the diabetes range — confirmatory testing and "
                    "a clinical review are recommended."
                )
            elif "hba1c" in values and 5.7 <= values["hba1c"] < 6.5:
                patterns.append(
                    "HbA1c is in the prediabetes range — lifestyle changes and "
                    "monitoring may help reduce future risk."
                )

        # Dyslipidemia: high LDL or total cholesterol or triglycerides, and/or low HDL.
        lipid_concern = (
            statuses.get("ldl") in ("high",)
            or statuses.get("total_cholesterol") in ("high",)
            or statuses.get("triglycerides") in ("high", "critical")
            or statuses.get("hdl") == "low"
        )
        if lipid_concern:
            patterns.append(
                "Your lipid panel shows a cardiovascular-risk pattern (such as "
                "high LDL/triglycerides or low HDL). A clinician can advise on "
                "diet, lifestyle, and whether treatment is needed."
            )

        # Liver: ALT and AST both elevated.
        if statuses.get("sgpt_alt") in ("high", "critical") and statuses.get("sgot_ast") in ("high", "critical"):
            patterns.append(
                "Both liver enzymes (ALT and AST) are elevated, which can reflect "
                "liver stress or injury. Further evaluation is advisable."
            )

        # Kidney: creatinine and/or urea elevated.
        if statuses.get("creatinine") in ("high", "critical") or statuses.get("urea") in ("high", "critical"):
            patterns.append(
                "A kidney-function marker (creatinine or urea/BUN) is elevated. "
                "Hydration status and kidney health should be reviewed by a clinician."
            )

        # Anemia: low hemoglobin.
        if statuses.get("hemoglobin") in ("low", "critical"):
            patterns.append(
                "Hemoglobin is below the typical range, which can indicate anemia. "
                "Causes range from iron deficiency to other conditions and warrant follow-up."
            )

        # Thyroid: TSH out of range.
        if statuses.get("tsh") == "high":
            patterns.append(
                "TSH is high, which may point toward an underactive thyroid "
                "(hypothyroidism). Confirmatory thyroid testing may be helpful."
            )
        elif statuses.get("tsh") == "low":
            patterns.append(
                "TSH is low, which may point toward an overactive thyroid "
                "(hyperthyroidism). Confirmatory thyroid testing may be helpful."
            )

        return patterns

    def get_critical_flags(self, results: List[Any]) -> List[str]:
        """Return urgent action messages for any critical values."""
        flags: List[str] = []
        for item in results:
            test_name, value, _ = self._unpack(item)
            canonical = self._canonical_key(test_name)
            if canonical not in CRITICAL_THRESHOLDS:
                continue
            low_c, high_c = CRITICAL_THRESHOLDS[canonical]
            friendly = self._friendly_name(test_name)
            unit = REFERENCE_RANGES.get(canonical, {}).get("unit", "")
            if low_c is not None and value < low_c:
                flags.append(
                    f"⚠️ Critically low {friendly}: {value} {unit} (critical below {low_c}). "
                    "Seek immediate medical attention."
                )
            elif high_c is not None and value > high_c:
                flags.append(
                    f"⚠️ Critically high {friendly}: {value} {unit} (critical above {high_c}). "
                    "Seek immediate medical attention."
                )
        return flags

    def get_disclaimer(self) -> str:
        """Mandatory medical disclaimer for all lab interpretations."""
        return (
            "⚠️ This lab-result interpretation is automated, educational guidance "
            "only and is NOT a medical diagnosis. Reference ranges vary between "
            "laboratories and individuals. Always review your results with a "
            "qualified healthcare professional, who will interpret them in the "
            "context of your full history. If you have critical values or feel "
            "unwell, seek medical care immediately."
        )

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _follow_up_tests(
        self,
        results: List[Any],
        patient_age: Optional[int],
        patient_sex: Optional[str],
    ) -> List[str]:
        """Suggest follow-up tests based on abnormal findings."""
        statuses: Dict[str, str] = {}
        present = set()
        for item in results:
            test_name, value, _ = self._unpack(item)
            canonical = self._canonical_key(test_name)
            if canonical:
                present.add(canonical)
                statuses[canonical] = self.get_result_status(test_name, value, patient_age, patient_sex)

        suggestions: List[str] = []

        if statuses.get("hba1c") in ("high", "critical") and "fasting_glucose" not in present:
            suggestions.append("Fasting blood glucose (to corroborate HbA1c)")
        if statuses.get("fasting_glucose") in ("high", "critical") and "hba1c" not in present:
            suggestions.append("HbA1c (to assess longer-term blood-sugar control)")
        if statuses.get("hemoglobin") in ("low", "critical"):
            suggestions.append("Iron studies / ferritin and a full blood count")
        if statuses.get("creatinine") in ("high", "critical") or statuses.get("urea") in ("high", "critical"):
            suggestions.append("Estimated GFR (eGFR) and a urine test for kidney function")
        if statuses.get("sgpt_alt") in ("high", "critical") or statuses.get("sgot_ast") in ("high", "critical"):
            suggestions.append("Complete liver function panel and a hepatitis screen")
        if (statuses.get("ldl") == "high" or statuses.get("total_cholesterol") == "high"
                or statuses.get("triglycerides") in ("high", "critical") or statuses.get("hdl") == "low"):
            suggestions.append("Repeat fasting lipid panel and cardiovascular risk assessment")
        if statuses.get("tsh") in ("high", "low"):
            suggestions.append("Free T4 (and Free T3) to clarify thyroid function")

        # Deduplicate while preserving order.
        seen = set()
        out = []
        for s in suggestions:
            if s not in seen:
                seen.add(s)
                out.append(s)
        return out

    def _explain(
        self,
        canonical: Optional[str],
        original_name: str,
        value: float,
        status: str,
        sex: Optional[str],
    ) -> str:
        """Build a plain-language explanation for a single result."""
        what = TEST_DESCRIPTIONS.get(canonical or "", None)
        friendly = self._friendly_name(original_name)
        lead = f"{friendly} measures {what}. " if what else ""

        # Special, more specific phrasing for banded tests.
        if canonical == "hba1c":
            band = self._band_label("hba1c", value)
            if band == "diabetes":
                return (lead + "A value of 6.5% or higher is in the diabetes range. "
                        "This indicates blood sugar has been high on average and should "
                        "be confirmed and managed with a clinician.")
            if band == "prediabetes":
                return (lead + "A value of 5.7–6.4% is in the prediabetes range, meaning "
                        "blood sugar is higher than ideal. Lifestyle changes can help.")
            return lead + "This value is within the normal range (below 5.7%)."

        if canonical == "fasting_glucose":
            band = self._band_label("fasting_glucose", value)
            if status == "critical":
                return lead + "This fasting glucose value is in a critical range and needs urgent care."
            if band == "diabetes":
                return lead + "A fasting glucose of 126 mg/dL or higher is in the diabetes range."
            if band == "prediabetes":
                return lead + "A fasting glucose of 100–125 mg/dL suggests prediabetes."
            return lead + "This fasting glucose value is within the normal range."

        if status == "critical":
            return (lead + f"A value of {value} is in the CRITICAL range and requires "
                    "immediate medical attention.")
        if status == "high":
            return lead + f"A value of {value} is higher than the typical reference range."
        if status == "low":
            return lead + f"A value of {value} is lower than the typical reference range."
        return lead + f"A value of {value} is within the typical reference range."

    def _banded_status(self, canonical: str, value: float, spec: Dict[str, Any]) -> str:
        """Classify multi-band tests into normal/high/low/critical."""
        band = self._band_label(canonical, value)

        if canonical in ("hba1c", "fasting_glucose"):
            if band in ("prediabetes", "diabetes"):
                return "high"
            return "normal"
        if canonical == "total_cholesterol":
            return "high" if band in ("borderline", "high") else "normal"
        if canonical == "ldl":
            return "high" if band in ("borderline_high", "high", "very_high") else "normal"
        if canonical == "triglycerides":
            if band == "very_high":
                return "high"
            return "high" if band in ("borderline", "high") else "normal"
        if canonical == "hdl":
            # For HDL, LOW is the risky direction.
            return "low" if band in ("medium_risk", "high_risk") else "normal"
        return "normal"

    def _band_label(self, canonical: str, value: float) -> str:
        """Return the named band a value falls into for a multi-band test."""
        spec = REFERENCE_RANGES.get(canonical, {})
        for band, rng in spec.items():
            if band == "unit" or not isinstance(rng, tuple):
                continue
            low, high = rng
            if low <= value <= high:
                return band
        return "out_of_range"

    def _reference_range_str(self, canonical: Optional[str], sex: Optional[str]) -> str:
        """Human-readable reference range string for display."""
        if not canonical or canonical not in REFERENCE_RANGES:
            return "Not established"
        spec = REFERENCE_RANGES[canonical]
        unit = spec.get("unit", "")
        sex_key = self._sex_key(sex)

        if sex_key in spec and isinstance(spec[sex_key], tuple):
            low, high = spec[sex_key]
            return f"{low}–{high} {unit}".strip()

        if "normal" in spec and isinstance(spec["normal"], tuple) and self._is_single_range(spec):
            low, high = spec["normal"]
            return f"{low}–{high} {unit}".strip()

        # Multi-band: show the optimal/desirable/normal band as the target.
        for target in ("normal", "optimal", "desirable", "low_risk"):
            if target in spec and isinstance(spec[target], tuple):
                low, high = spec[target]
                if target == "low_risk":  # HDL: higher is better.
                    return f"≥ {low} {unit}".strip()
                return f"{low}–{high} {unit}".strip()
        return f"See lab range ({unit})".strip()

    @staticmethod
    def _is_single_range(spec: Dict[str, Any]) -> bool:
        """True when 'normal' is the only band (besides unit / sex ranges)."""
        bands = [k for k, v in spec.items() if isinstance(v, tuple)]
        return bands == ["normal"]

    @staticmethod
    def _sex_key(sex: Optional[str]) -> Optional[str]:
        if not sex:
            return None
        s = str(sex).strip().lower()
        if s in ("m", "male", "man", "boy"):
            return "adult_male"
        if s in ("f", "female", "woman", "girl"):
            return "adult_female"
        return None

    @staticmethod
    def _canonical_key(test_name: str) -> Optional[str]:
        if not test_name:
            return None
        key = str(test_name).strip().lower().replace("-", "_").replace(" ", "_")
        if key in REFERENCE_RANGES:
            return key
        # Try alias table on the raw (space-form) name too.
        raw = str(test_name).strip().lower()
        if raw in TEST_ALIASES:
            return TEST_ALIASES[raw]
        if key in TEST_ALIASES:
            return TEST_ALIASES[key]
        # Underscore-normalized alias values.
        if key.replace("_", " ") in TEST_ALIASES:
            return TEST_ALIASES[key.replace("_", " ")]
        return None

    @staticmethod
    def _friendly_name(test_name: str) -> str:
        canonical = LabResultsAgent._canonical_key(test_name)
        pretty = {
            "hba1c": "HbA1c",
            "fasting_glucose": "Fasting glucose",
            "total_cholesterol": "Total cholesterol",
            "ldl": "LDL cholesterol",
            "hdl": "HDL cholesterol",
            "triglycerides": "Triglycerides",
            "creatinine": "Creatinine",
            "urea": "Urea (BUN)",
            "sgpt_alt": "ALT (SGPT)",
            "sgot_ast": "AST (SGOT)",
            "tsh": "TSH",
            "wbc": "White blood cells",
            "platelets": "Platelets",
            "sodium": "Sodium",
            "potassium": "Potassium",
            "hemoglobin": "Hemoglobin",
        }
        if canonical and canonical in pretty:
            return pretty[canonical]
        return str(test_name).strip().title()

    @staticmethod
    def _unpack(item: Any) -> Tuple[str, float, Optional[str]]:
        """Extract (test_name, value, unit) from a dict, pydantic model, or object."""
        if isinstance(item, dict):
            return (
                str(item.get("test_name", "")).strip(),
                float(item.get("value", 0)),
                item.get("unit"),
            )
        # Pydantic model / generic object with attributes.
        test_name = getattr(item, "test_name", "")
        value = getattr(item, "value", 0)
        unit = getattr(item, "unit", None)
        return str(test_name).strip(), float(value), unit

    def _coerce_inputs(self, raw: Any) -> List[Dict[str, Any]]:
        """Normalize arbitrary context input into a list of result dicts."""
        if not raw:
            return []
        if isinstance(raw, dict):
            raw = [raw]
        out: List[Dict[str, Any]] = []
        for item in raw:
            try:
                name, value, unit = self._unpack(item)
            except (TypeError, ValueError):
                continue
            if not name:
                continue
            out.append({"test_name": name, "value": value, "unit": unit})
        return out

    # ------------------------------------------------------------------ #
    # BaseAgent metadata
    # ------------------------------------------------------------------ #

    def get_capabilities(self) -> List[str]:
        return [
            "lab", "labs", "lab results", "blood test", "blood work",
            "cbc", "hba1c", "a1c", "cholesterol", "ldl", "hdl",
            "triglycerides", "creatinine", "hemoglobin", "glucose",
            "tsh", "potassium", "sodium", "platelets", "interpret results",
            "test results",
        ]

    def get_description(self) -> str:
        return (
            "Interprets laboratory results against standard reference ranges, "
            "classifies values, flags critical findings, and explains them in "
            "plain language (decision support only)."
        )

    def get_confidence_threshold(self) -> float:
        return 0.50
