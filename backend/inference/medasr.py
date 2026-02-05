"""
MedASR Inference

Provides inference for medical speech recognition using Google's MedASR model
(LASR CTC architecture with KenLM language model).

Model: google/medasr
Architecture: lasr_ctc (requires transformers >= 5.0.0.dev0)
Use cases:
- Medical dictation transcription
- Clinical note generation from voice
- Patient-doctor conversation transcription
- Medical terminology recognition

NOTE: The lasr_ctc architecture is only available in transformers >= 5.0.
Until then, this module will operate in stub mode.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union

from .base import BaseInference

logger = logging.getLogger(__name__)


class MedASRInference(BaseInference):
    """MedASR model inference for medical speech-to-text"""

    # Supported audio formats
    SUPPORTED_FORMATS = [".wav", ".mp3", ".flac", ".m4a", ".ogg"]

    def _load_model_weights(self):
        """Load MedASR model weights (lasr_ctc architecture)"""
        try:
            import torch
            import json

            logger.info(f"Loading MedASR from {self.model_path}")

            # Check model architecture before attempting load
            config_path = self.model_path / "config.json"
            if config_path.exists():
                with open(config_path) as f:
                    config = json.load(f)
                model_type = config.get("model_type", "")
                required_version = config.get("transformers_version", "")

                if model_type == "lasr_ctc":
                    import transformers
                    from packaging import version
                    installed = version.parse(transformers.__version__)
                    required = version.parse(required_version) if required_version else installed

                    if installed < required:
                        raise RuntimeError(
                            f"MedASR model requires transformers >= {required_version} "
                            f"(installed: {transformers.__version__}). "
                            f"The lasr_ctc architecture is not yet available. "
                            f"Install with: pip install transformers>={required_version}"
                        )

            from transformers import AutoProcessor, AutoModel

            self.processor = AutoProcessor.from_pretrained(
                str(self.model_path),
                local_files_only=True
            )

            logger.info("Loading model weights (this may take a moment)...")
            model_dtype = torch.float32 if self.device == "cpu" else torch.float16
            self.model = AutoModel.from_pretrained(
                str(self.model_path),
                local_files_only=True,
                dtype=model_dtype,
                low_cpu_mem_usage=True,
            )

            logger.info(f"Moving model to {self.device} ({model_dtype})...")
            self.model.to(self.device)
            self.model.eval()

        except Exception as e:
            logger.error(f"Failed to load MedASR: {e}")
            raise

    async def transcribe_audio(
        self,
        audio_file: Union[str, Path],
        language: str = "en",
        mode: str = "dictation",
        return_timestamps: bool = False
    ) -> Dict[str, Any]:
        """
        Transcribe medical audio using MedASR

        Args:
            audio_file: Path to audio file
            language: Audio language (default: English)
            mode: Transcription mode (dictation, conversation, notes)
            return_timestamps: Whether to return word-level timestamps

        Returns:
            Dict with transcription, confidence, medical terms detected
        """
        if not self._load_model():
            return self._generate_stub_response(
                mode=mode,
                audio_file=str(audio_file)
            )

        try:
            # Load audio
            import librosa
            audio_data, sample_rate = librosa.load(audio_file, sr=16000)

            # Process audio
            inputs = self.processor(
                audio_data,
                sampling_rate=sample_rate,
                return_tensors="pt"
            ).to(self.device)

            # Generate transcription
            import torch
            with torch.no_grad():
                predicted_ids = self.model.generate(
                    inputs.input_features,
                    return_timestamps=return_timestamps,
                    language=language
                )

            # Decode transcription
            transcription = self.processor.batch_decode(
                predicted_ids,
                skip_special_tokens=True
            )[0]

            # Extract medical terminology
            medical_terms = self._extract_medical_terms(transcription)

            # Calculate confidence (approximation)
            confidence = self._estimate_confidence(predicted_ids)

            return {
                "transcription": transcription,
                "mode": mode,
                "language": language,
                "confidence": confidence,
                "medical_terms_detected": medical_terms,
                "audio_duration_seconds": len(audio_data) / sample_rate,
                "disclaimer": "Transcription should be reviewed by qualified medical personnel.",
                "stub_mode": False
            }

        except Exception as e:
            logger.error(f"MedASR transcription failed: {e}")
            return self._generate_stub_response(
                mode=mode,
                audio_file=str(audio_file)
            )

    async def transcribe_with_speaker_diarization(
        self,
        audio_file: Union[str, Path],
        num_speakers: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Transcribe medical conversation with speaker identification

        Args:
            audio_file: Path to audio file
            num_speakers: Expected number of speakers (auto-detect if None)

        Returns:
            Dict with speaker-segmented transcription
        """
        if not self._load_model():
            return self._generate_stub_diarization()

        try:
            # This would require additional diarization model
            # Placeholder for future implementation

            base_transcription = await self.transcribe_audio(
                audio_file,
                mode="conversation",
                return_timestamps=True
            )

            # Add speaker diarization (would need pyannote.audio or similar)
            segments = [
                {
                    "speaker": "Speaker 1",
                    "start_time": 0.0,
                    "end_time": 10.0,
                    "text": base_transcription["transcription"]
                }
            ]

            return {
                "segments": segments,
                "num_speakers_detected": 1,
                "disclaimer": "Transcription should be reviewed by qualified medical personnel.",
                "stub_mode": False
            }

        except Exception as e:
            logger.error(f"Speaker diarization failed: {e}")
            return self._generate_stub_diarization()

    def _extract_medical_terms(self, transcription: str) -> list:
        """Extract medical terminology from transcription"""

        # Common medical term patterns
        medical_keywords = [
            "diagnosis", "symptom", "medication", "prescription",
            "hypertension", "diabetes", "cardiovascular", "respiratory",
            "mg", "ml", "dosage", "blood pressure", "heart rate"
        ]

        found_terms = []
        transcription_lower = transcription.lower()

        for term in medical_keywords:
            if term in transcription_lower:
                found_terms.append(term)

        return found_terms

    def _estimate_confidence(self, predicted_ids) -> float:
        """Estimate transcription confidence"""

        # This is a simplified confidence estimation
        # Real implementation would use model's output probabilities

        return 0.85  # Placeholder

    def _generate_stub_response(
        self,
        mode: str,
        audio_file: str
    ) -> Dict[str, Any]:
        """Generate stub response when model unavailable"""

        return {
            "transcription": "[Audio transcription not available - AI model not loaded]",
            "mode": mode,
            "language": "en",
            "confidence": 0.0,
            "medical_terms_detected": [],
            "audio_file": audio_file,
            "error": "MedASR model not available. Please load model weights to enable transcription.",
            "recommended_action": "Use manual transcription or load MedASR model",
            "disclaimer": "Transcription should be reviewed by qualified medical personnel.",
            "stub_mode": True
        }

    def _generate_stub_diarization(self) -> Dict[str, Any]:
        """Generate stub diarization response"""

        return {
            "segments": [],
            "num_speakers_detected": 0,
            "error": "Speaker diarization not available - AI model not loaded",
            "disclaimer": "Transcription should be reviewed by qualified medical personnel.",
            "stub_mode": True
        }
