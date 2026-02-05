"""
Voice Interaction Agent - Medical speech recognition using MedASR.

Responsibilities:
- Speech-to-text transcription with medical vocabulary
- Medical dictation (clinical notes, prescriptions)
- Voice-based symptom reporting
- Voice queries from patients
- Support for multiple languages and accents

Requirements:
- Offline processing (no internet required)
- Medical terminology recognition
- Low latency for real-time interaction
- Noise robustness

Current Implementation: Ready for MedASR integration (stub responses)
Production: Integrate MedASR for medical speech recognition
"""

from orchestrator.base import BaseAgent, AgentRequest, AgentResponse
from typing import List, Dict, Optional, Any
import base64
from pathlib import Path


class VoiceAgent(BaseAgent):
    """
    Medical speech recognition agent using MedASR.

    Supports multiple use cases:
    - Patient symptom reporting via voice
    - Medical dictation (clinical notes)
    - Voice-based queries
    - Hands-free operation
    """

    def __init__(self):
        super().__init__()
        self.name = "voice_interaction"

        # Supported audio formats
        self.supported_formats = [
            "wav", "mp3", "m4a", "ogg", "flac"
        ]

        # Supported languages
        self.supported_languages = {
            "en-US": "English (United States)",
            "en-GB": "English (United Kingdom)",
            "es-ES": "Spanish (Spain)",
            "fr-FR": "French (France)",
            "de-DE": "German (Germany)",
            "pt-BR": "Portuguese (Brazil)",
            "zh-CN": "Chinese (Mandarin)"
        }

        # Use case modes
        self.modes = {
            "symptom_reporting": "Patient describing symptoms",
            "medical_dictation": "Doctor dictating clinical notes",
            "voice_query": "Patient asking health questions",
            "general": "General transcription"
        }

    async def process(self, request: AgentRequest) -> AgentResponse:
        """
        Process voice input and transcribe to text.

        Expected context:
        - audio_path: Path to audio file
        - audio_data: Base64 encoded audio (alternative to path)
        - mode: Use case mode (symptom_reporting, medical_dictation, voice_query)
        - language: Language code (default: en-US)
        - speaker_context: Patient/doctor context (optional)
        """
        # Extract context
        audio_path = request.context.get("audio_path")
        audio_data = request.context.get("audio_data")
        mode = request.context.get("mode", "general")
        language = request.context.get("language", "en-US")
        speaker_context = request.context.get("speaker_context", {})

        # Validate audio input
        if not audio_path and not audio_data:
            return self._error_response(
                "No audio provided",
                "Please provide audio_path or audio_data"
            )

        # Validate mode
        if mode not in self.modes:
            return self._error_response(
                f"Unknown mode: {mode}",
                f"Supported modes: {', '.join(self.modes.keys())}"
            )

        # Validate language
        if language not in self.supported_languages:
            return self._error_response(
                f"Unsupported language: {language}",
                f"Supported languages: {', '.join(self.supported_languages.keys())}"
            )

        # Perform transcription
        transcription_result = await self._transcribe_audio(
            audio_path=audio_path,
            audio_data=audio_data,
            mode=mode,
            language=language,
            speaker_context=speaker_context
        )

        # Route transcribed text to appropriate agent
        suggested_agents = self._determine_routing(
            mode=mode,
            transcription=transcription_result["text"]
        )

        # Build response data
        data = {
            "mode": self.modes[mode],
            "language": self.supported_languages[language],
            "transcription": transcription_result["text"],
            "confidence": transcription_result["confidence"],
            "audio_duration_seconds": transcription_result.get("duration", 0),
            "words_detected": transcription_result.get("words", []),
            "medical_terms_identified": transcription_result.get("medical_terms", []),
            "alternative_transcriptions": transcription_result.get("alternatives", []),
            "next_action": self._get_next_action(mode, transcription_result["text"]),
            "disclaimer": self._get_voice_disclaimer()
        }

        return AgentResponse(
            success=True,
            agent_name=self.name,
            data=data,
            confidence=transcription_result["confidence"],
            reasoning=f"Speech transcribed using MedASR ({mode} mode, {language})",
            red_flags=[],
            requires_escalation=False,
            suggested_agents=suggested_agents
        )

    async def _transcribe_audio(
        self,
        audio_path: Optional[str],
        audio_data: Optional[str],
        mode: str,
        language: str,
        speaker_context: Dict
    ) -> Dict[str, Any]:
        """
        Transcribe audio using MedASR.

        STUB IMPLEMENTATION - Ready for production integration.

        Production Integration:
        1. Load audio file or decode base64 audio_data
        2. Preprocess audio (resample to 16kHz, mono)
        3. Pass through MedASR model
        4. Apply medical vocabulary boosting
        5. Return transcription with confidence scores

        Example with HuggingFace:
        ```python
        from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq
        import torch
        import torchaudio

        processor = AutoProcessor.from_pretrained("google/medASR")
        model = AutoModelForSpeechSeq2Seq.from_pretrained("google/medASR")

        # Load audio
        waveform, sample_rate = torchaudio.load(audio_path)

        # Resample if needed
        if sample_rate != 16000:
            resampler = torchaudio.transforms.Resample(sample_rate, 16000)
            waveform = resampler(waveform)

        # Transcribe
        inputs = processor(waveform.squeeze(), return_tensors="pt", sampling_rate=16000)
        with torch.no_grad():
            output_ids = model.generate(**inputs)

        transcription = processor.batch_decode(output_ids, skip_special_tokens=True)[0]
        ```

        See MEDASR_INTEGRATION_GUIDE.md for detailed instructions.
        """
        # TODO: Replace with actual MedASR call in production

        # STUB: Return mock transcriptions based on mode
        if mode == "symptom_reporting":
            return {
                "text": "I've been having a persistent cough and fever for the past 5 days. My temperature has been around 101 degrees Fahrenheit. I also feel very tired and have some shortness of breath when I walk up stairs.",
                "confidence": 0.88,
                "duration": 12.5,
                "words": [
                    {"word": "persistent", "confidence": 0.92, "start_time": 0.5, "end_time": 1.1},
                    {"word": "cough", "confidence": 0.95, "start_time": 1.2, "end_time": 1.5},
                    {"word": "fever", "confidence": 0.94, "start_time": 1.8, "end_time": 2.1}
                ],
                "medical_terms": [
                    "cough", "fever", "temperature", "shortness of breath"
                ],
                "alternatives": [
                    "I have been having a persistent cough and fever for the past 5 days",
                    "I've had a persistent cough and fever for about 5 days"
                ]
            }

        elif mode == "medical_dictation":
            return {
                "text": "Patient is a 58-year-old male presenting with acute onset chest pain radiating to the left arm. Pain is described as crushing and substernal. Associated symptoms include diaphoresis and nausea. Vital signs: blood pressure 145 over 92, heart rate 98, oxygen saturation 96% on room air. Physical exam reveals mild distress, lungs clear bilaterally, heart regular rate and rhythm. EKG shows ST elevations in leads V2 through V4 consistent with anterior STEMI. Cardiology consulted, patient transferred to cath lab for emergent PCI.",
                "confidence": 0.92,
                "duration": 28.3,
                "words": [],
                "medical_terms": [
                    "chest pain", "radiating", "substernal", "diaphoresis",
                    "blood pressure", "oxygen saturation", "EKG", "ST elevations",
                    "STEMI", "PCI", "cath lab"
                ],
                "alternatives": []
            }

        elif mode == "voice_query":
            return {
                "text": "What are the side effects of lisinopril?",
                "confidence": 0.90,
                "duration": 2.8,
                "words": [
                    {"word": "side", "confidence": 0.92},
                    {"word": "effects", "confidence": 0.91},
                    {"word": "lisinopril", "confidence": 0.88}
                ],
                "medical_terms": ["lisinopril", "side effects"],
                "alternatives": [
                    "What are the side effects of Lisinopril",
                    "What are the side affects of lisinopril"
                ]
            }

        else:  # general
            return {
                "text": "Hello, I would like to schedule an appointment with Dr. Smith for next week.",
                "confidence": 0.85,
                "duration": 4.2,
                "words": [],
                "medical_terms": [],
                "alternatives": []
            }

    def _determine_routing(self, mode: str, transcription: str) -> List[str]:
        """Determine which agents should process the transcribed text."""
        suggested_agents = []

        if mode == "symptom_reporting":
            # Route to triage for urgency, then diagnostic for differential
            suggested_agents = ["triage", "diagnostic_support"]

        elif mode == "medical_dictation":
            # Medical dictation doesn't need further routing
            suggested_agents = []

        elif mode == "voice_query":
            # Analyze the query to determine appropriate agent
            transcription_lower = transcription.lower()

            if any(word in transcription_lower for word in ["medication", "drug", "pill", "side effect"]):
                suggested_agents.append("drug_info")

            if any(word in transcription_lower for word in ["symptom", "pain", "fever", "cough"]):
                suggested_agents.append("communication")

            if "appointment" in transcription_lower or "schedule" in transcription_lower:
                # Would route to scheduling agent (not yet implemented)
                pass

        return suggested_agents

    def _get_next_action(self, mode: str, transcription: str) -> str:
        """Get recommended next action based on mode and transcription."""
        actions = {
            "symptom_reporting": "Transcription will be analyzed by triage agent to determine urgency level",
            "medical_dictation": "Dictation saved to clinical note. Review and sign when complete.",
            "voice_query": "Processing your question with appropriate medical knowledge agents",
            "general": "Transcription complete"
        }
        return actions.get(mode, "Transcription complete")

    def _get_voice_disclaimer(self) -> str:
        """Get mandatory voice transcription disclaimer."""
        return (
            "⚠️ VOICE TRANSCRIPTION DISCLAIMER: This transcription is generated using "
            "automated speech recognition and may contain errors. Always verify medical "
            "terminology and critical information. Transcription accuracy depends on audio "
            "quality, background noise, and speaker clarity. For medical dictation, review "
            "and edit transcription before finalizing clinical documentation."
        )

    def _error_response(self, error: str, details: str) -> AgentResponse:
        """Generate error response."""
        return AgentResponse(
            success=False,
            agent_name=self.name,
            data={
                "error": error,
                "details": details,
                "supported_formats": self.supported_formats,
                "supported_languages": list(self.supported_languages.keys()),
                "supported_modes": list(self.modes.keys())
            },
            confidence=0.0,
            reasoning=error,
            red_flags=[],
            requires_escalation=False
        )

    def get_capabilities(self) -> List[str]:
        """Return keywords that trigger this agent."""
        return [
            "voice", "speech", "audio", "transcribe", "dictate",
            "record", "voice message", "speak", "say"
        ]

    def get_description(self) -> str:
        """Return agent description."""
        return "Medical speech recognition using MedASR - transcribes voice to text with medical vocabulary support"

    def get_confidence_threshold(self) -> float:
        """Minimum confidence to activate this agent."""
        return 0.50
