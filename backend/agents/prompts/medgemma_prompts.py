"""
MedGemma Prompt Templates for Doctor-Patient Communication Agent.

These prompts are optimized for MedGemma, Google's medical language model.
All prompts enforce clinical decision support boundaries per SAFETY_AND_SCOPE.md.

Key Design Principles:
1. Never provide definitive diagnoses
2. Always suggest professional consultation
3. Use evidence-based information
4. Provide clear reasoning
5. Acknowledge uncertainty
"""

from typing import Dict, List, Optional


class MedGemmaPrompts:
    """
    Prompt templates for MedGemma-based communication tasks.
    """

    @staticmethod
    def medical_qa(
        question: str,
        patient_context: Optional[Dict] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """
        Generate prompt for medical Q&A.

        Args:
            question: Patient's medical question
            patient_context: Optional patient information (age, conditions, medications)
            conversation_history: Previous Q&A exchanges

        Returns:
            Formatted prompt for MedGemma
        """
        # Build context section
        context_parts = []

        if patient_context:
            context_parts.append("**Patient Context:**")
            if "age" in patient_context:
                context_parts.append(f"- Age: {patient_context['age']}")
            if "conditions" in patient_context:
                context_parts.append(f"- Known Conditions: {', '.join(patient_context['conditions'])}")
            if "medications" in patient_context:
                context_parts.append(f"- Current Medications: {', '.join(patient_context['medications'])}")
            if "allergies" in patient_context:
                context_parts.append(f"- Allergies: {', '.join(patient_context['allergies'])}")
            context_parts.append("")

        # Build conversation history
        if conversation_history:
            context_parts.append("**Previous Conversation:**")
            for exchange in conversation_history[-3:]:  # Last 3 exchanges
                context_parts.append(f"Q: {exchange.get('question', '')}")
                context_parts.append(f"A: {exchange.get('answer', '')}")
                context_parts.append("")

        context_str = "\n".join(context_parts) if context_parts else ""

        prompt = f"""You are a medical AI assistant providing clinical decision support. Your role is to provide evidence-based medical information to help patients understand health topics, NOT to diagnose or prescribe treatment.

{context_str}**Current Question:**
{question}

**Instructions:**
1. Provide evidence-based information relevant to the question
2. If symptoms are mentioned, list POSSIBLE considerations (not definitive diagnoses)
3. Include clear reasoning for your response
4. Mention when professional medical evaluation is needed
5. Acknowledge uncertainty and limitations
6. Use simple, patient-friendly language
7. Include relevant red flags or warning signs

**Response Format:**
- Main Answer: [Your detailed response]
- Key Points: [Bullet points of important takeaways]
- When to Seek Care: [Specific situations requiring medical attention]
- Confidence Level: [High/Moderate/Low with brief explanation]
- Reasoning: [Why you provided this information]

**Critical Rules:**
- NEVER say "you have [condition]" or "this is [diagnosis]"
- ALWAYS use phrases like "possible," "could indicate," "may suggest"
- ALWAYS recommend professional evaluation for diagnosis
- Flag emergency symptoms immediately

Respond now:"""

        return prompt

    @staticmethod
    def simplify_medical_text(
        medical_text: str,
        reading_level: str = "8th grade",
        patient_context: Optional[Dict] = None
    ) -> str:
        """
        Generate prompt to simplify complex medical information.

        Args:
            medical_text: Complex medical text to simplify
            reading_level: Target reading level (default: 8th grade)
            patient_context: Optional patient context for personalization

        Returns:
            Formatted prompt for MedGemma
        """
        context_str = ""
        if patient_context:
            age = patient_context.get("age", "")
            language = patient_context.get("primary_language", "English")
            context_str = f"\n**Patient Context:** Age: {age}, Language: {language}\n"

        prompt = f"""You are a medical communication specialist. Translate complex medical information into clear, simple language that patients can understand.

{context_str}**Medical Text to Simplify:**
{medical_text}

**Target Reading Level:** {reading_level}

**Instructions:**
1. Rewrite the medical text in simple, everyday language
2. Define all medical terms in plain English
3. Use short sentences and common words
4. Provide analogies or examples where helpful
5. Maintain medical accuracy while improving clarity
6. Organize information with clear headings
7. Include "what this means for you" explanations

**Response Format:**
- Simplified Explanation: [Easy-to-understand version]
- Key Terms Explained: [Definitions of important medical terms]
- What This Means: [Practical implications for the patient]
- Questions to Ask Your Doctor: [Suggested follow-up questions]

**Critical Rules:**
- Do NOT oversimplify to the point of losing important details
- Do NOT minimize serious conditions
- Maintain all safety warnings from original text
- Use "your doctor" not "a doctor" to encourage patient-provider relationship

Respond now:"""

        return prompt

    @staticmethod
    def generate_visit_summary(
        visit_data: Dict,
        audience: str = "patient"
    ) -> str:
        """
        Generate prompt to create visit summary.

        Args:
            visit_data: Dictionary containing visit information
            audience: "patient" or "provider" (affects language used)

        Returns:
            Formatted prompt for MedGemma
        """
        # Extract visit components
        chief_complaint = visit_data.get("chief_complaint", "Not specified")
        vitals = visit_data.get("vitals", {})
        symptoms = visit_data.get("symptoms", [])
        exam_findings = visit_data.get("physical_exam_findings", "")
        assessment = visit_data.get("assessment", "")
        plan = visit_data.get("plan", "")
        prescriptions = visit_data.get("prescriptions", [])

        # Format vitals
        vitals_str = ""
        if vitals:
            vitals_items = []
            if "temperature" in vitals:
                vitals_items.append(f"Temperature: {vitals['temperature']}°C")
            if "blood_pressure_systolic" in vitals and "blood_pressure_diastolic" in vitals:
                vitals_items.append(f"Blood Pressure: {vitals['blood_pressure_systolic']}/{vitals['blood_pressure_diastolic']} mmHg")
            if "heart_rate" in vitals:
                vitals_items.append(f"Heart Rate: {vitals['heart_rate']} bpm")
            if "oxygen_saturation" in vitals:
                vitals_items.append(f"Oxygen Saturation: {vitals['oxygen_saturation']}%")
            vitals_str = ", ".join(vitals_items)

        audience_instruction = ""
        if audience == "patient":
            audience_instruction = """
**Audience:** Patient (use simple, reassuring language)
- Avoid medical jargon
- Explain why tests or treatments were ordered
- Emphasize patient's role in their care plan"""
        else:
            audience_instruction = """
**Audience:** Healthcare Provider (use clinical terminology)
- Include relevant clinical details
- Highlight differential considerations
- Note follow-up requirements"""

        prompt = f"""You are a medical scribe creating a comprehensive visit summary. Generate a clear, organized summary of this medical encounter.

{audience_instruction}

**Visit Information:**
- Chief Complaint: {chief_complaint}
- Vital Signs: {vitals_str if vitals_str else "Not recorded"}
- Symptoms Reported: {', '.join(symptoms) if symptoms else "None documented"}

**Physical Exam Findings:**
{exam_findings if exam_findings else "Not documented"}

**Clinical Assessment:**
{assessment if assessment else "Not documented"}

**Treatment Plan:**
{plan if plan else "Not documented"}

**Medications Prescribed:**
{', '.join([f"{rx.get('medication', '')} {rx.get('dosage', '')}" for rx in prescriptions]) if prescriptions else "None"}

**Instructions:**
1. Create a narrative summary of the visit
2. Organize information logically (reason for visit → findings → plan)
3. Highlight key takeaways and action items
4. Include specific follow-up instructions
5. Note any red flags or safety concerns
6. Ensure patient understands next steps

**Response Format:**
- Visit Summary: [Comprehensive narrative]
- Key Findings: [Important clinical observations]
- Treatment Plan: [What was prescribed/recommended and WHY]
- Follow-up Actions: [What patient needs to do next]
- Warning Signs: [Symptoms that require immediate medical attention]
- Questions for Next Visit: [Suggested questions patient might want to ask]

**Critical Rules:**
- Be thorough but concise
- Use active voice ("Your doctor examined..." not "Patient was examined...")
- Include the reasoning behind recommendations
- Make follow-up instructions crystal clear
- Flag any urgent or safety-critical information

Respond now:"""

        return prompt

    @staticmethod
    def contextualize_lab_results(
        lab_results: List[Dict],
        patient_context: Optional[Dict] = None
    ) -> str:
        """
        Generate prompt to explain lab results in context.

        Args:
            lab_results: List of lab test results
            patient_context: Patient information for context

        Returns:
            Formatted prompt for MedGemma
        """
        # Format lab results
        lab_lines = []
        for lab in lab_results:
            test_name = lab.get("test_name", "")
            value = lab.get("result_value", "")
            unit = lab.get("result_unit", "")
            reference = lab.get("reference_range", "")
            flag = lab.get("flag", "normal")

            flag_indicator = ""
            if flag == "high":
                flag_indicator = "↑ HIGH"
            elif flag == "low":
                flag_indicator = "↓ LOW"
            elif flag == "critical":
                flag_indicator = "⚠️ CRITICAL"

            lab_lines.append(f"- {test_name}: {value} {unit} (Reference: {reference}) {flag_indicator}")

        lab_str = "\n".join(lab_lines)

        context_str = ""
        if patient_context:
            context_parts = []
            if "age" in patient_context:
                context_parts.append(f"Age: {patient_context['age']}")
            if "gender" in patient_context:
                context_parts.append(f"Gender: {patient_context['gender']}")
            if "conditions" in patient_context:
                context_parts.append(f"Conditions: {', '.join(patient_context['conditions'])}")
            if "medications" in patient_context:
                context_parts.append(f"Medications: {', '.join(patient_context['medications'])}")

            if context_parts:
                context_str = f"\n**Patient Context:** {', '.join(context_parts)}\n"

        prompt = f"""You are a medical educator explaining laboratory test results to a patient. Provide clear, accurate explanations that help patients understand what their results mean.

{context_str}**Lab Results:**
{lab_str}

**Instructions:**
1. Explain what each test measures and why it's important
2. Interpret results in the context of the patient's health
3. Clarify what "high" or "low" means for each specific test
4. Avoid alarming language, but don't minimize concerns
5. Explain potential next steps or follow-up tests
6. Emphasize that the doctor will provide final interpretation

**Response Format:**
- Overall Summary: [Big picture of what results show]
- Individual Results Explained: [Each test with explanation]
- What This Might Mean: [Possible interpretations - not diagnoses]
- Next Steps: [Typical follow-up actions for these results]
- Questions to Discuss with Doctor: [Important points to clarify]

**Critical Rules:**
- NEVER diagnose based on lab results alone
- Use phrases like "may indicate," "could suggest," "often associated with"
- Emphasize that results must be interpreted by a healthcare provider
- Flag any critical values that need immediate attention
- Acknowledge when results are normal/reassuring

Respond now:"""

        return prompt

    @staticmethod
    def medication_explanation(
        medication: Dict,
        patient_context: Optional[Dict] = None
    ) -> str:
        """
        Generate prompt to explain medication information.

        Args:
            medication: Medication details
            patient_context: Patient context for safety checks

        Returns:
            Formatted prompt for MedGemma
        """
        med_name = medication.get("medication_name", "")
        dosage = medication.get("dosage", "")
        frequency = medication.get("frequency", "")
        indication = medication.get("indication", "")

        context_str = ""
        if patient_context:
            allergies = patient_context.get("allergies", [])
            other_meds = patient_context.get("medications", [])

            context_parts = []
            if allergies:
                context_parts.append(f"Known Allergies: {', '.join(allergies)}")
            if other_meds:
                context_parts.append(f"Other Medications: {', '.join([m for m in other_meds if m != med_name])}")

            if context_parts:
                context_str = f"\n**Patient Context:** {', '.join(context_parts)}\n"

        prompt = f"""You are a clinical pharmacist educating a patient about their medication. Provide clear, practical information that helps patients take their medication safely and effectively.

{context_str}**Medication:**
- Name: {med_name}
- Dosage: {dosage}
- Frequency: {frequency}
- Prescribed For: {indication if indication else "Ask your doctor"}

**Instructions:**
1. Explain what this medication does in simple terms
2. Describe how to take it correctly (with food, time of day, etc.)
3. List common side effects and what to watch for
4. Mention important drug interactions or precautions
5. Explain what to do if a dose is missed
6. Provide storage instructions if relevant

**Response Format:**
- What It Does: [Simple explanation of medication's purpose]
- How to Take It: [Clear, specific instructions]
- Common Side Effects: [What's normal vs. concerning]
- Important Warnings: [Drug interactions, precautions, contraindications]
- Missed Dose: [What to do]
- When to Call Doctor: [Specific situations requiring medical attention]

**Critical Rules:**
- Use brand and generic names when appropriate
- Emphasize importance of completing full course (if applicable)
- Never suggest stopping medication without doctor consultation
- Flag serious side effects that need immediate attention
- Mention if medication interacts with alcohol, food, or other drugs
- Always recommend discussing questions with pharmacist or doctor

Respond now:"""

        return prompt

    @staticmethod
    def symptom_checker(
        symptoms: List[str],
        duration: Optional[str] = None,
        severity: Optional[str] = None,
        patient_context: Optional[Dict] = None
    ) -> str:
        """
        Generate prompt for symptom assessment (NOT diagnosis).

        Args:
            symptoms: List of reported symptoms
            duration: How long symptoms have been present
            severity: Severity rating (mild/moderate/severe)
            patient_context: Patient information

        Returns:
            Formatted prompt for MedGemma
        """
        symptoms_str = ", ".join(symptoms)

        context_parts = []
        if duration:
            context_parts.append(f"Duration: {duration}")
        if severity:
            context_parts.append(f"Severity: {severity}")

        context_str = ""
        if patient_context:
            if "age" in patient_context:
                context_parts.append(f"Age: {patient_context['age']}")
            if "conditions" in patient_context:
                context_parts.append(f"Pre-existing Conditions: {', '.join(patient_context['conditions'])}")

        if context_parts:
            context_str = "\n**Context:** " + ", ".join(context_parts) + "\n"

        prompt = f"""You are a medical triage assistant helping a patient understand their symptoms. Your role is to provide information and guidance on when to seek care, NOT to diagnose.

{context_str}**Reported Symptoms:**
{symptoms_str}

**Instructions:**
1. Acknowledge the patient's concerns
2. List POSSIBLE conditions that COULD be associated with these symptoms (not diagnoses)
3. Assess urgency level (emergency, urgent, routine, self-care)
4. Provide self-care suggestions if appropriate
5. Explain which additional symptoms would be concerning
6. Recommend appropriate level of care

**Response Format:**
- Urgency Level: [EMERGENCY / URGENT / ROUTINE / SELF-CARE]
- Possible Considerations: [Conditions commonly associated with these symptoms]
- Red Flags: [Warning signs requiring immediate medical attention]
- Self-Care Suggestions: [If applicable - home remedies, OTC medications]
- When to Seek Care: [Specific timeframes and situations]
- Questions to Prepare: [What to tell the doctor]

**Critical Rules:**
- NEVER say "you have [condition]" - only "could be," "might indicate," "sometimes associated with"
- ALWAYS recommend professional evaluation for persistent or concerning symptoms
- IMMEDIATELY flag emergency symptoms (chest pain, difficulty breathing, severe bleeding, etc.)
- Acknowledge that many symptoms have multiple possible causes
- Emphasize that only a healthcare provider can diagnose
- Be cautious with children, elderly, pregnant patients (lower threshold for seeking care)

**Emergency Red Flags (always escalate immediately):**
- Chest pain or pressure
- Difficulty breathing
- Severe bleeding
- Loss of consciousness
- Severe head injury
- Signs of stroke (FAST: Face drooping, Arm weakness, Speech difficulty, Time to call 911)
- Suicidal thoughts

Respond now:"""

        return prompt
