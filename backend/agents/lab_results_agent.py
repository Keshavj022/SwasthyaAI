"""
Lab Results Agent — interprets structured lab results using hardcoded reference ranges.
"""

from typing import Literal
from schemas.lab_results import LabResultInput, InterpretedResult, LabResultsResponse

REFERENCE_RANGES = {
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

# Critical thresholds — checked first, return "critical" immediately
CRITICAL_THRESHOLDS = {
    "potassium": {"low": 2.5, "high": 6.5},
    "sodium": {"low": 120, "high": 155},
    "fasting_glucose": {"low": 50, "high": 500},
    "hemoglobin": {"low": 7.0},
    "platelets": {"low": 50.0},
}


class LabResultsAgent:
    """Interprets structured lab results using hardcoded reference ranges."""

    def _normalize_name(self, test_name: str) -> str:
        """Normalize test name: lowercase, replace spaces and hyphens with underscores."""
        return test_name.lower().replace(" ", "_").replace("-", "_")

    def get_result_status(
        self,
        test_name: str,
        value: float,
        age: int,
        sex: str,
    ) -> Literal["normal", "low", "high", "critical"]:
        """Determine status for a lab result."""
        normalized = self._normalize_name(test_name)

        # Step 1: Check critical thresholds first
        if normalized in CRITICAL_THRESHOLDS:
            thresholds = CRITICAL_THRESHOLDS[normalized]
            if "low" in thresholds and value <= thresholds["low"]:
                return "critical"
            if "high" in thresholds and value >= thresholds["high"]:
                return "critical"

        # Step 2: Look up reference ranges
        if normalized not in REFERENCE_RANGES:
            return "normal"

        ranges = REFERENCE_RANGES[normalized]

        # Sex-specific ranges
        if normalized in ("hemoglobin", "creatinine", "sgpt_alt"):
            if normalized == "sgpt_alt":
                # sgpt_alt has sex-specific adult ranges
                key = "adult_female" if sex == "female" else "adult_male"
                low, high = ranges[key]
                if value < low:
                    return "low"
                elif value > high:
                    return "high"
                return "normal"
            else:
                key = "adult_female" if sex == "female" else "adult_male"
                low, high = ranges[key]
                if value < low:
                    return "low"
                elif value > high:
                    return "high"
                return "normal"

        # Multi-category tests
        if normalized == "hba1c":
            if value <= 5.6:
                return "normal"
            elif value <= 6.4:
                return "high"  # prediabetes
            else:
                return "critical"  # diabetes

        if normalized == "fasting_glucose":
            # Critical thresholds already checked above (< 50 or > 500)
            if value <= 99:
                return "normal"
            elif value <= 125:
                return "high"  # prediabetes
            else:
                return "high"  # diabetes (126–500); CRITICAL_THRESHOLDS handles true emergencies

        if normalized == "total_cholesterol":
            if value <= 199:
                return "normal"  # desirable
            elif value <= 239:
                return "high"  # borderline
            else:
                return "high"  # high — treat as high, not critical per spec

        if normalized == "ldl":
            if value <= 129:
                return "normal"  # optimal or near_optimal
            elif value <= 159:
                return "high"  # borderline_high
            elif value <= 189:
                return "high"  # high
            else:
                return "critical"  # very_high

        if normalized == "hdl":
            # Lower HDL is worse
            if value >= 60:
                return "normal"  # low_risk
            elif value >= 40:
                return "high"  # medium_risk (elevated risk)
            else:
                return "critical"  # high_risk (worst category)

        if normalized == "triglycerides":
            if value <= 149:
                return "normal"
            elif value <= 199:
                return "high"  # borderline
            elif value <= 499:
                return "high"  # high
            else:
                return "critical"  # very_high

        # Simple range tests: urea, sgot_ast, tsh, wbc, platelets, sodium, potassium
        if "normal" in ranges:
            low, high = ranges["normal"]
            if value < low:
                return "low"
            elif value > high:
                return "high"
            return "normal"

        return "normal"

    def get_reference_range_str(self, test_name: str, age: int, sex: str) -> str:
        """Return human-readable reference range string."""
        normalized = self._normalize_name(test_name)

        if normalized not in REFERENCE_RANGES:
            return "No reference range available"

        ranges = REFERENCE_RANGES[normalized]
        unit = ranges.get("unit", "")

        if normalized == "hemoglobin":
            key = "adult_female" if sex == "female" else "adult_male"
            low, high = ranges[key]
            return f"{low}–{high} {unit}"

        if normalized == "creatinine":
            key = "adult_female" if sex == "female" else "adult_male"
            low, high = ranges[key]
            return f"{low}–{high} {unit}"

        if normalized == "sgpt_alt":
            key = "adult_female" if sex == "female" else "adult_male"
            low, high = ranges[key]
            return f"{low}–{high} {unit}"

        if normalized == "hba1c":
            return f"< 5.7% normal; 5.7–6.4% prediabetes; ≥ 6.5% diabetes"

        if normalized == "fasting_glucose":
            return f"70–99 {unit} normal; 100–125 prediabetes; ≥ 126 diabetes"

        if normalized == "total_cholesterol":
            return f"< 200 {unit} desirable; 200–239 borderline; ≥ 240 high"

        if normalized == "ldl":
            return f"< 100 {unit} optimal; 100–129 near optimal; 130–159 borderline high; 160–189 high; ≥ 190 very high"

        if normalized == "hdl":
            return f"≥ 60 {unit} low risk; 40–59 moderate risk; < 40 high risk"

        if normalized == "triglycerides":
            return f"< 150 {unit} normal; 150–199 borderline; 200–499 high; ≥ 500 very high"

        if "normal" in ranges:
            low, high = ranges["normal"]
            return f"{low}–{high} {unit}"

        return "No reference range available"

    def get_explanation(
        self,
        test_name: str,
        value: float,
        status: str,
        sex: str,
        unit: str = "",
    ) -> str:
        """Return plain-language explanation of the result."""
        normalized = self._normalize_name(test_name)

        if normalized == "hemoglobin":
            implications = {
                "normal": "This is within the healthy range.",
                "low": "This may indicate anemia, which can cause fatigue and weakness.",
                "high": "This may indicate polycythemia or dehydration.",
                "critical": "This critically low level requires immediate medical attention — urgent anemia management needed.",
            }
            return f"Hemoglobin carries oxygen in your blood. Your level of {value} {unit} is {status} — {implications.get(status, 'please consult your doctor.')}"

        if normalized == "hba1c":
            implications = {
                "normal": "Your blood sugar control over the past 2–3 months has been good.",
                "high": "This suggests prediabetes. Lifestyle changes may help prevent progression.",
                "critical": "This indicates diabetes. Medical management is needed to control blood sugar.",
            }
            return f"HbA1c reflects your average blood sugar over the past 2–3 months. A level of {value}% indicates {implications.get(status, 'an abnormal result — consult your doctor.')}"

        if normalized == "fasting_glucose":
            implications = {
                "normal": "Your fasting blood sugar is within the normal range.",
                "low": "Low blood sugar (hypoglycemia) detected — this requires prompt attention.",
                "high": "Elevated blood sugar suggests prediabetes. Dietary changes are advisable.",
                "critical": "Severely abnormal blood glucose — immediate medical evaluation needed.",
            }
            return f"Fasting blood glucose measures your blood sugar after not eating. {implications.get(status, 'Please consult your doctor.')}"

        if normalized == "total_cholesterol":
            implications = {
                "normal": "Your cholesterol is in the desirable range, indicating good cardiovascular health.",
                "high": "Elevated cholesterol increases risk of heart disease. Dietary and lifestyle changes are recommended.",
                "critical": "Very high cholesterol significantly increases cardiovascular risk. Medical evaluation is needed.",
            }
            return f"Total cholesterol measures fat in the blood. {implications.get(status, 'Please consult your doctor.')}"

        if normalized == "ldl":
            implications = {
                "normal": "Your LDL (bad cholesterol) is in an acceptable range.",
                "high": "Elevated LDL increases the risk of plaque buildup in arteries.",
                "critical": "Very high LDL significantly raises the risk of heart attack and stroke. Medical treatment is recommended.",
            }
            return f"LDL (low-density lipoprotein) is the 'bad' cholesterol that can build up in arteries. {implications.get(status, 'Please consult your doctor.')}"

        if normalized == "hdl":
            implications = {
                "normal": "Your HDL (good cholesterol) is at a protective level — this is beneficial for heart health.",
                "high": "Moderate HDL level — working on lifestyle improvement can help raise it.",
                "critical": "Very low HDL significantly increases heart disease risk. Medical guidance is recommended.",
            }
            return f"HDL (high-density lipoprotein) is the 'good' cholesterol that helps remove other forms of cholesterol. {implications.get(status, 'Please consult your doctor.')}"

        if normalized == "triglycerides":
            implications = {
                "normal": "Your triglyceride levels are normal.",
                "high": "Elevated triglycerides can increase cardiovascular risk. Dietary changes are advisable.",
                "critical": "Very high triglycerides can cause pancreatitis and serious cardiovascular risk. Seek medical attention.",
            }
            return f"Triglycerides are fats stored in the blood. {implications.get(status, 'Please consult your doctor.')}"

        if normalized == "creatinine":
            implications = {
                "normal": "Your kidney filtration appears normal.",
                "low": "Low creatinine may indicate reduced muscle mass.",
                "high": "Elevated creatinine may indicate reduced kidney function.",
                "critical": "Critically elevated creatinine suggests significant kidney impairment. Immediate medical evaluation needed.",
            }
            return f"Creatinine is a waste product filtered by the kidneys. {implications.get(status, 'Please consult your doctor.')}"

        if normalized == "urea":
            implications = {
                "normal": "Blood urea nitrogen is within the normal range.",
                "low": "Low urea may be associated with liver disease or poor protein intake.",
                "high": "Elevated urea may indicate kidney dysfunction, dehydration, or high protein intake.",
            }
            return f"Blood urea nitrogen (BUN) measures kidney function and protein metabolism. {implications.get(status, 'Please consult your doctor.')}"

        if normalized == "sgpt_alt":
            implications = {
                "normal": "Your liver enzyme (ALT) is within the normal range.",
                "high": "Elevated ALT may indicate liver inflammation or damage.",
                "critical": "Significantly elevated ALT suggests possible liver disease. Immediate evaluation is needed.",
            }
            return f"ALT (SGPT) is a liver enzyme that indicates liver cell health. {implications.get(status, 'Please consult your doctor.')}"

        if normalized == "sgot_ast":
            implications = {
                "normal": "Your liver enzyme (AST) is within the normal range.",
                "high": "Elevated AST may indicate liver, heart, or muscle damage.",
                "critical": "Significantly elevated AST requires urgent medical evaluation.",
            }
            return f"AST (SGOT) is an enzyme found in the liver and other tissues. {implications.get(status, 'Please consult your doctor.')}"

        if normalized == "tsh":
            implications = {
                "normal": "Your thyroid function appears normal.",
                "low": "Low TSH may indicate hyperthyroidism (overactive thyroid).",
                "high": "Elevated TSH may indicate hypothyroidism (underactive thyroid).",
                "critical": "Severely abnormal TSH requires prompt thyroid evaluation.",
            }
            return f"TSH (thyroid-stimulating hormone) regulates thyroid function. {implications.get(status, 'Please consult your doctor.')}"

        if normalized == "wbc":
            implications = {
                "normal": "Your white blood cell count is within the normal range.",
                "low": "Low WBC (leukopenia) may indicate immune suppression or bone marrow issues.",
                "high": "Elevated WBC may indicate infection, inflammation, or other conditions.",
                "critical": "Critically abnormal WBC count requires urgent medical evaluation.",
            }
            return f"White blood cells (WBC) are the body's immune defenders. {implications.get(status, 'Please consult your doctor.')}"

        if normalized == "platelets":
            implications = {
                "normal": "Your platelet count is within the normal range.",
                "low": "Low platelets (thrombocytopenia) increases the risk of bleeding.",
                "high": "Elevated platelets may increase the risk of blood clots.",
                "critical": "Critically low platelets pose a serious bleeding risk. Immediate medical attention is needed.",
            }
            return f"Platelets are cells that help your blood clot. {implications.get(status, 'Please consult your doctor.')}"

        if normalized == "sodium":
            implications = {
                "normal": "Your sodium level is within the normal range.",
                "low": "Low sodium (hyponatremia) can cause neurological symptoms.",
                "high": "High sodium (hypernatremia) may indicate dehydration.",
                "critical": "Critically abnormal sodium level — this is a medical emergency.",
            }
            return f"Sodium is an electrolyte essential for fluid balance and nerve function. {implications.get(status, 'Please consult your doctor.')}"

        if normalized == "potassium":
            implications = {
                "normal": "Your potassium level is within the normal range.",
                "low": "Low potassium (hypokalemia) can cause muscle weakness and heart rhythm issues.",
                "high": "High potassium (hyperkalemia) can cause dangerous heart rhythm disturbances.",
                "critical": "Critically abnormal potassium — risk of cardiac arrhythmia. Seek immediate medical care.",
            }
            return f"Potassium is an electrolyte critical for heart and muscle function. {implications.get(status, 'Please consult your doctor.')}"

        # Unknown test fallback
        return f"Your {test_name} result is {value} {unit}. Please consult your doctor for interpretation."

    def detect_patterns(self, results: list[InterpretedResult]) -> list[str]:
        """Detect clinically meaningful combinations among results."""
        patterns = []

        def norm(name: str) -> str:
            return name.lower().replace(" ", "_").replace("-", "_")

        normalized_map = {norm(r.test_name): r.status for r in results}

        # Diabetes pattern
        hba1c_status = normalized_map.get("hba1c")
        glucose_status = normalized_map.get("fasting_glucose")
        if hba1c_status in ("high", "critical") and glucose_status in ("high", "critical"):
            patterns.append(
                "Elevated HbA1c and fasting glucose suggest possible diabetes or poor glycemic control. Endocrinology consultation recommended."
            )

        # High cholesterol + LDL pattern
        chol_status = normalized_map.get("total_cholesterol")
        ldl_status = normalized_map.get("ldl")
        if chol_status in ("high", "critical") and ldl_status in ("high", "critical"):
            patterns.append(
                "Combined high cholesterol and LDL indicate elevated cardiovascular risk."
            )

        # Low HDL + High LDL pattern
        hdl_status = normalized_map.get("hdl")
        if hdl_status == "critical" and ldl_status in ("high", "critical"):
            patterns.append(
                "Low HDL with high LDL significantly increases heart disease risk."
            )

        # Liver enzyme pattern
        alt_status = normalized_map.get("sgpt_alt")
        ast_status = normalized_map.get("sgot_ast")
        if alt_status in ("high", "critical") and ast_status in ("high", "critical"):
            patterns.append(
                "Elevated liver enzymes (ALT and AST) may indicate liver inflammation or damage."
            )

        # Anemia pattern
        hgb_status = normalized_map.get("hemoglobin")
        if hgb_status in ("low", "critical"):
            patterns.append(
                "Low hemoglobin indicates anemia. Further evaluation of iron, B12, and folate may be needed."
            )

        # WBC patterns
        wbc_status = normalized_map.get("wbc")
        if wbc_status in ("high", "critical"):
            patterns.append(
                "Elevated white blood cell count may suggest infection or inflammation."
            )
        elif wbc_status == "low":
            patterns.append(
                "Low white blood cell count (leukopenia) may indicate immune suppression."
            )

        # Kidney function pattern
        creatinine_status = normalized_map.get("creatinine")
        urea_status = normalized_map.get("urea")
        if creatinine_status in ("high", "critical") and urea_status in ("high", "critical"):
            patterns.append(
                "Elevated creatinine and urea together suggest possible kidney dysfunction."
            )

        # Thyroid patterns
        tsh_status = normalized_map.get("tsh")
        if tsh_status in ("high", "critical"):
            patterns.append("Elevated TSH may indicate hypothyroidism.")
        elif tsh_status == "low":
            patterns.append("Low TSH may indicate hyperthyroidism.")

        return patterns

    def get_critical_flags(self, results: list[InterpretedResult]) -> list[str]:
        """Generate specific flag messages for critical results."""
        flags = []
        for r in results:
            if r.status != "critical":
                continue
            normalized = self._normalize_name(r.test_name)

            if normalized == "potassium":
                if r.value >= 6.5:
                    flags.append(
                        f"CRITICAL: Potassium {r.value} {r.unit} (dangerously high) — risk of cardiac arrhythmia. Seek immediate medical care."
                    )
                else:
                    flags.append(
                        f"CRITICAL: Potassium {r.value} {r.unit} (dangerously low) — risk of cardiac arrhythmia. Seek immediate medical care."
                    )

            elif normalized == "sodium":
                if r.value >= 155:
                    flags.append(
                        f"CRITICAL: Sodium {r.value} {r.unit} (severely high) — risk of neurological damage. Seek immediate medical care."
                    )
                else:
                    flags.append(
                        f"CRITICAL: Sodium {r.value} {r.unit} (severely low) — risk of neurological complications. Seek immediate medical care."
                    )

            elif normalized == "fasting_glucose":
                if r.value >= 500:
                    flags.append(
                        f"CRITICAL: Fasting glucose {r.value} {r.unit} (dangerously high) — risk of diabetic emergency. Seek immediate medical care."
                    )
                elif r.value <= 50:
                    flags.append(
                        f"CRITICAL: Fasting glucose {r.value} {r.unit} (severely low) — risk of hypoglycemic emergency. Seek immediate medical care."
                    )

            elif normalized == "hemoglobin":
                flags.append(
                    f"CRITICAL: Hemoglobin {r.value} {r.unit} (critically low) — severe anemia. Urgent medical evaluation required."
                )

            elif normalized == "platelets":
                flags.append(
                    f"CRITICAL: Platelets {r.value} {r.unit} (critically low) — high risk of serious bleeding. Urgent medical evaluation required."
                )

            elif normalized == "hba1c":
                flags.append(
                    f"CRITICAL: HbA1c {r.value}% (diabetes range) — urgent glycemic management needed. Consult your doctor immediately."
                )

            elif normalized == "ldl":
                flags.append(
                    f"CRITICAL: LDL {r.value} {r.unit} (very high) — significantly elevated cardiovascular risk. Medical treatment recommended."
                )

            elif normalized == "hdl":
                flags.append(
                    f"CRITICAL: HDL {r.value} {r.unit} (very low) — severely reduced cardiovascular protection. Consult your doctor."
                )

            elif normalized == "triglycerides":
                flags.append(
                    f"CRITICAL: Triglycerides {r.value} {r.unit} (very high) — risk of pancreatitis and cardiovascular disease. Seek medical attention."
                )

            else:
                flags.append(
                    f"CRITICAL: {r.test_name} {r.value} {r.unit} is critically abnormal. Seek prompt medical evaluation."
                )

        return flags

    def get_follow_up_tests(self, results: list[InterpretedResult]) -> list[str]:
        """Suggest follow-up tests based on abnormal findings."""
        follow_ups = []
        seen = set()

        def add(suggestion: str):
            if suggestion not in seen:
                seen.add(suggestion)
                follow_ups.append(suggestion)

        normalized_map = {
            self._normalize_name(r.test_name): r.status for r in results
        }

        hgb_status = normalized_map.get("hemoglobin")
        if hgb_status in ("low", "critical"):
            add("Serum ferritin, iron studies, vitamin B12, folate")

        hba1c_status = normalized_map.get("hba1c")
        glucose_status = normalized_map.get("fasting_glucose")
        if hba1c_status in ("high", "critical") or glucose_status in ("high", "critical"):
            add("Oral glucose tolerance test (OGTT), fasting insulin, HbA1c (repeat in 3 months)")

        chol_status = normalized_map.get("total_cholesterol")
        ldl_status = normalized_map.get("ldl")
        if chol_status in ("high", "critical") or ldl_status in ("high", "critical"):
            add("LDL (if not tested), HDL (if not tested), lipoprotein(a), ApoB")

        creatinine_status = normalized_map.get("creatinine")
        urea_status = normalized_map.get("urea")
        if creatinine_status in ("high", "critical") or urea_status in ("high", "critical"):
            add("eGFR calculation, urine albumin-to-creatinine ratio, renal ultrasound")

        alt_status = normalized_map.get("sgpt_alt")
        ast_status = normalized_map.get("sgot_ast")
        if alt_status in ("high", "critical") or ast_status in ("high", "critical"):
            add("Hepatitis B & C serology, GGT, alkaline phosphatase, abdominal ultrasound")

        tsh_status = normalized_map.get("tsh")
        if tsh_status in ("low", "high", "critical"):
            add("Free T4 (FT4), Free T3 (FT3), thyroid antibodies")

        wbc_status = normalized_map.get("wbc")
        if wbc_status in ("low", "high", "critical"):
            add("Peripheral blood smear, CRP, ESR")

        platelets_status = normalized_map.get("platelets")
        if platelets_status in ("low", "critical"):
            add("Peripheral smear, coagulation panel (PT/INR, aPTT)")

        return follow_ups

    def generate_summary(self, results: list[InterpretedResult]) -> str:
        """Generate a one-paragraph summary of results."""
        normal_count = sum(1 for r in results if r.status == "normal")
        low_count = sum(1 for r in results if r.status == "low")
        high_count = sum(1 for r in results if r.status == "high")
        critical_count = sum(1 for r in results if r.status == "critical")

        abnormal = low_count + high_count
        total = len(results)

        critical_names = [r.test_name for r in results if r.status == "critical"]
        abnormal_names = [r.test_name for r in results if r.status in ("low", "high")]

        parts = [f"Your lab panel shows {total} test(s) in total:"]

        if normal_count:
            parts.append(f"{normal_count} normal result(s)")
        if abnormal:
            abnormal_str = ", ".join(abnormal_names)
            parts.append(f"{abnormal} abnormal value(s) ({abnormal_str})")
        if critical_count:
            critical_str = ", ".join(critical_names)
            parts.append(f"{critical_count} critical result(s) ({critical_str})")

        summary = ". ".join(parts) + "."

        if critical_count > 0:
            summary += " The critical value(s) require immediate medical attention."
        elif abnormal > 0:
            summary += " Please discuss the abnormal results with your healthcare provider."
        else:
            summary += " All results are within normal limits. Maintain a healthy lifestyle."

        return summary

    def interpret_results(
        self,
        results: list[LabResultInput],
        patient_age: int,
        patient_sex: str,
    ) -> LabResultsResponse:
        """Interpret a list of lab results and return a full response."""
        interpreted: list[InterpretedResult] = []

        for r in results:
            status = self.get_result_status(r.test_name, r.value, patient_age, patient_sex)
            explanation = self.get_explanation(r.test_name, r.value, status, patient_sex, r.unit)
            ref_range = self.get_reference_range_str(r.test_name, patient_age, patient_sex)
            action_needed = status in ("high", "low", "critical")

            interpreted.append(
                InterpretedResult(
                    test_name=r.test_name,
                    value=r.value,
                    unit=r.unit,
                    status=status,
                    reference_range=ref_range,
                    explanation=explanation,
                    action_needed=action_needed,
                )
            )

        patterns = self.detect_patterns(interpreted)
        critical_flags = self.get_critical_flags(interpreted)
        follow_up_tests = self.get_follow_up_tests(interpreted)
        summary = self.generate_summary(interpreted)

        disclaimer = (
            "DISCLAIMER: This interpretation is for informational purposes only and does not constitute "
            "medical advice. Reference ranges may vary by laboratory and individual factors. Always consult "
            "a qualified healthcare professional for diagnosis and treatment decisions."
        )

        return LabResultsResponse(
            results=interpreted,
            summary=summary,
            patterns_detected=patterns,
            critical_flags=critical_flags,
            follow_up_tests=follow_up_tests,
            disclaimer=disclaimer,
        )
