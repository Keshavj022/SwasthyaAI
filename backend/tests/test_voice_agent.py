"""
Test script for Voice Interaction Agent.

Demonstrates all voice recognition features:
1. Symptom reporting via voice
2. Medical dictation (clinical notes)
3. Voice-based queries
4. Multiple languages
5. Error handling

Run: python test_voice_agent.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.voice_agent import VoiceAgent
from orchestrator.base import AgentRequest


async def test_symptom_reporting():
    """Test voice-based symptom reporting"""
    print("\n" + "="*80)
    print("TEST 1: Symptom Reporting - Patient Voice Input")
    print("="*80)

    agent = VoiceAgent()

    request = AgentRequest(
        message="Process patient voice recording",
        user_id="patient_001",
        context={
            "audio_path": "/path/to/patient_symptoms.wav",
            "mode": "symptom_reporting",
            "language": "en-US",
            "speaker_context": {
                "age": 45,
                "gender": "female"
            }
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"📊 Confidence: {response.confidence:.2f}")
    print(f"\n🎤 Mode: {response.data['mode']}")
    print(f"🌍 Language: {response.data['language']}")
    print(f"⏱️  Duration: {response.data['audio_duration_seconds']}s")

    print(f"\n📝 Transcription:")
    print(f"   \"{response.data['transcription']}\"")

    print(f"\n💊 Medical Terms Identified ({len(response.data['medical_terms_identified'])}):")
    for term in response.data['medical_terms_identified']:
        print(f"   - {term}")

    if response.data.get('alternative_transcriptions'):
        print(f"\n🔄 Alternative Transcriptions:")
        for alt in response.data['alternative_transcriptions'][:2]:
            print(f"   - {alt}")

    print(f"\n➡️  Next Action:")
    print(f"   {response.data['next_action']}")

    print(f"\n🔄 Suggested Agents: {', '.join(response.suggested_agents)}")


async def test_medical_dictation():
    """Test medical dictation mode"""
    print("\n" + "="*80)
    print("TEST 2: Medical Dictation - Clinical Note")
    print("="*80)

    agent = VoiceAgent()

    request = AgentRequest(
        message="Transcribe clinical dictation",
        user_id="doctor_001",
        context={
            "audio_path": "/path/to/clinical_note.mp3",
            "mode": "medical_dictation",
            "language": "en-US",
            "speaker_context": {
                "role": "physician",
                "specialty": "cardiology"
            }
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"📊 Confidence: {response.confidence:.2f}")
    print(f"⏱️  Duration: {response.data['audio_duration_seconds']}s")

    print(f"\n📝 Transcription:")
    print(f"   {response.data['transcription'][:200]}...")

    print(f"\n💊 Medical Terms Identified ({len(response.data['medical_terms_identified'])}):")
    for term in response.data['medical_terms_identified'][:5]:
        print(f"   - {term}")

    print(f"\n➡️  Next Action:")
    print(f"   {response.data['next_action']}")


async def test_voice_query():
    """Test voice-based question"""
    print("\n" + "="*80)
    print("TEST 3: Voice Query - Medication Question")
    print("="*80)

    agent = VoiceAgent()

    request = AgentRequest(
        message="Process patient voice question",
        user_id="patient_002",
        context={
            "audio_path": "/path/to/question.wav",
            "mode": "voice_query",
            "language": "en-US"
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"📊 Confidence: {response.confidence:.2f}")

    print(f"\n📝 Transcription:")
    print(f"   \"{response.data['transcription']}\"")

    print(f"\n💊 Medical Terms: {', '.join(response.data['medical_terms_identified'])}")

    print(f"\n🔄 Suggested Agents: {', '.join(response.suggested_agents)}")
    print(f"➡️  Next Action: {response.data['next_action']}")


async def test_general_mode():
    """Test general transcription mode"""
    print("\n" + "="*80)
    print("TEST 4: General Mode - Appointment Scheduling")
    print("="*80)

    agent = VoiceAgent()

    request = AgentRequest(
        message="Transcribe general audio",
        user_id="patient_003",
        context={
            "audio_path": "/path/to/general.wav",
            "mode": "general",
            "language": "en-US"
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"📊 Confidence: {response.confidence:.2f}")

    print(f"\n📝 Transcription:")
    print(f"   \"{response.data['transcription']}\"")


async def test_spanish_language():
    """Test Spanish language support"""
    print("\n" + "="*80)
    print("TEST 5: Spanish Language - Symptom Reporting")
    print("="*80)

    agent = VoiceAgent()

    request = AgentRequest(
        message="Transcribir audio en español",
        user_id="patient_004",
        context={
            "audio_path": "/path/to/spanish_symptoms.wav",
            "mode": "symptom_reporting",
            "language": "es-ES"
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"🌍 Language: {response.data['language']}")
    print(f"📊 Confidence: {response.confidence:.2f}")


async def test_error_no_audio():
    """Test error handling - no audio provided"""
    print("\n" + "="*80)
    print("TEST 6: Error Handling - No Audio Provided")
    print("="*80)

    agent = VoiceAgent()

    request = AgentRequest(
        message="Transcribe audio",
        user_id="patient_005",
        context={
            "mode": "symptom_reporting"
            # No audio_path or audio_data
        }
    )

    response = await agent.process(request)

    print(f"\n❌ Success: {response.success}")
    print(f"⚠️  Error: {response.data.get('error')}")
    print(f"💡 Details: {response.data.get('details')}")

    print(f"\n📋 Supported Formats:")
    for fmt in response.data['supported_formats']:
        print(f"   - {fmt}")


async def test_unsupported_mode():
    """Test error handling - unsupported mode"""
    print("\n" + "="*80)
    print("TEST 7: Error Handling - Unsupported Mode")
    print("="*80)

    agent = VoiceAgent()

    request = AgentRequest(
        message="Process audio",
        user_id="patient_006",
        context={
            "audio_path": "/path/to/audio.wav",
            "mode": "real_time_translation"  # Not supported
        }
    )

    response = await agent.process(request)

    print(f"\n❌ Success: {response.success}")
    print(f"⚠️  Error: {response.data.get('error')}")

    print(f"\n📋 Supported Modes:")
    for mode in response.data['supported_modes']:
        print(f"   - {mode}")


async def test_word_level_timestamps():
    """Test word-level timestamp details"""
    print("\n" + "="*80)
    print("TEST 8: Word-Level Timestamps - Detailed Analysis")
    print("="*80)

    agent = VoiceAgent()

    request = AgentRequest(
        message="Transcribe with detailed timestamps",
        user_id="patient_007",
        context={
            "audio_path": "/path/to/detailed_audio.wav",
            "mode": "symptom_reporting",
            "language": "en-US"
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")

    if response.data.get('words_detected'):
        print(f"\n🔤 Word-Level Details (first 3 words):")
        for word_info in response.data['words_detected'][:3]:
            print(f"\n   Word: \"{word_info['word']}\"")
            print(f"   Confidence: {word_info['confidence']:.2f}")
            if 'start_time' in word_info:
                print(f"   Time: {word_info['start_time']:.1f}s - {word_info['end_time']:.1f}s")


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("🏥 VOICE INTERACTION AGENT TEST SUITE")
    print("Testing MedASR-powered Speech Recognition")
    print("="*80)

    tests = [
        ("Symptom Reporting", test_symptom_reporting),
        ("Medical Dictation", test_medical_dictation),
        ("Voice Query", test_voice_query),
        ("General Mode", test_general_mode),
        ("Spanish Language", test_spanish_language),
        ("Error - No Audio", test_error_no_audio),
        ("Error - Unsupported Mode", test_unsupported_mode),
        ("Word-Level Timestamps", test_word_level_timestamps)
    ]

    for test_name, test_func in tests:
        try:
            await test_func()
        except Exception as e:
            print(f"\n❌ Test '{test_name}' failed with error: {str(e)}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*80)
    print("✅ TEST SUITE COMPLETE")
    print("="*80)
    print("\nKey Features Demonstrated:")
    print("  ✅ Multi-mode support (symptom reporting, dictation, queries)")
    print("  ✅ Medical terminology recognition")
    print("  ✅ Multi-language support (English, Spanish, etc.)")
    print("  ✅ Word-level timestamps and confidence scores")
    print("  ✅ Alternative transcriptions")
    print("  ✅ Intelligent routing to appropriate agents")
    print("  ✅ Error handling (missing audio, unsupported modes)")
    print("\n⚠️  IMPORTANT NOTES:")
    print("Voice transcription is automated and may contain errors.")
    print("Always verify medical terminology and critical information.")
    print("Transcription accuracy depends on audio quality and speaker clarity.")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
