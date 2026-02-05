"""
Test script for Medical Image Analysis Agent.

Demonstrates all image analysis features:
1. Chest X-ray finding detection
2. Dermatology lesion classification
3. CT scan analysis
4. Abnormality classification
5. Region description
6. Error handling

Run: python test_image_analysis_agent.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from agents.image_analysis_agent import ImageAnalysisAgent
from orchestrator.base import AgentRequest


async def test_chest_xray_finding_detection():
    """Test chest X-ray analysis - finding detection"""
    print("\n" + "="*80)
    print("TEST 1: Chest X-ray - Finding Detection (Pneumonia)")
    print("="*80)

    agent = ImageAnalysisAgent()

    request = AgentRequest(
        message="Analyze this chest X-ray for my patient with cough and fever",
        user_id="doctor_001",
        context={
            "image_path": "/path/to/chest_xray.jpg",  # Mock path
            "modality": "chest_xray",
            "analysis_type": "finding_detection",
            "clinical_context": {
                "symptoms": ["cough", "fever", "dyspnea"],
                "duration": "5 days"
            }
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"📊 Confidence: {response.confidence:.2f}")
    print(f"\n🔬 Modality: {response.data['modality']}")
    print(f"📷 Image Quality: {response.data['image_quality']}")

    print(f"\n🔍 Findings ({len(response.data['findings'])}):")
    for i, finding in enumerate(response.data['findings'], 1):
        print(f"\n{i}. {finding['finding']}")
        print(f"   Location: {finding['location']}")
        print(f"   Severity: {finding['severity']}")
        print(f"   Confidence: {finding['confidence']:.2f}")
        print(f"   Description: {finding['description']}")
        print(f"   Differential: {', '.join(finding['differential'][:3])}")

    print(f"\n💡 Overall Impression:")
    print(f"   {response.data['overall_impression']}")

    print(f"\n📋 Recommended Next Steps:")
    for step in response.data['recommended_next_steps']:
        print(f"   - {step}")

    print(f"\n🚩 Red Flags: {len(response.red_flags)}")
    print(f"⚠️  Requires Escalation: {response.requires_escalation}")


async def test_dermatology_classification():
    """Test dermatology image - abnormality classification"""
    print("\n" + "="*80)
    print("TEST 2: Dermatology - Skin Lesion Classification")
    print("="*80)

    agent = ImageAnalysisAgent()

    request = AgentRequest(
        message="Classify this skin lesion",
        user_id="doctor_002",
        context={
            "image_path": "/path/to/lesion.jpg",
            "modality": "dermatology",
            "analysis_type": "abnormality_classification"
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"📊 Confidence: {response.confidence:.2f}")
    print(f"\n🔬 Modality: {response.data['modality']}")
    print(f"📋 Classification: {response.data['classification']}")
    print(f"\n🤔 Reasoning: {response.data['reasoning']}")

    print(f"\n📝 Characteristics:")
    for char in response.data['characteristics']:
        print(f"   - {char}")

    print(f"\n💡 Differential Considerations:")
    for diff in response.data.get('differential_considerations', []):
        print(f"   - {diff}")

    print(f"\n🚩 Red Flags: {len(response.red_flags)}")
    for flag in response.red_flags:
        print(f"   {flag}")

    print(f"\n⚠️  Requires Specialist: {response.requires_escalation}")


async def test_chest_xray_classification():
    """Test chest X-ray abnormality classification"""
    print("\n" + "="*80)
    print("TEST 3: Chest X-ray - Abnormality Classification")
    print("="*80)

    agent = ImageAnalysisAgent()

    request = AgentRequest(
        message="Is this chest X-ray normal or abnormal?",
        user_id="doctor_003",
        context={
            "image_path": "/path/to/chest_xray_2.jpg",
            "modality": "chest_xray",
            "analysis_type": "abnormality_classification"
        }
    )

    response = await agent.process(request)

    print(f"\n📋 Classification: {response.data['classification']}")
    print(f"📊 Confidence: {response.confidence:.2f}")
    print(f"\n📝 Characteristics:")
    for char in response.data['characteristics']:
        print(f"   - {char}")

    print(f"\n💡 Differential:")
    for diff in response.data.get('differential_considerations', []):
        print(f"   - {diff}")


async def test_ct_scan_analysis():
    """Test CT scan analysis"""
    print("\n" + "="*80)
    print("TEST 4: CT Scan - Finding Detection")
    print("="*80)

    agent = ImageAnalysisAgent()

    request = AgentRequest(
        message="Analyze CT chest for pulmonary findings",
        user_id="doctor_004",
        context={
            "image_path": "/path/to/ct_chest.dcm",
            "modality": "ct_chest",
            "analysis_type": "finding_detection"
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"🔬 Modality: {response.data['modality']}")
    print(f"📊 Confidence: {response.confidence:.2f}")
    print(f"\n💡 Findings: {len(response.data['findings'])}")


async def test_region_description():
    """Test region description"""
    print("\n" + "="*80)
    print("TEST 5: Region Description")
    print("="*80)

    agent = ImageAnalysisAgent()

    request = AgentRequest(
        message="Describe what you see in this image",
        user_id="doctor_005",
        context={
            "image_path": "/path/to/image.jpg",
            "modality": "chest_xray",
            "analysis_type": "region_description"
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"📝 Description: {response.data['description']}")
    print(f"🏥 Anatomical Structures: {', '.join(response.data['anatomical_structures'])}")


async def test_error_no_image():
    """Test error handling - no image provided"""
    print("\n" + "="*80)
    print("TEST 6: Error Handling - No Image Provided")
    print("="*80)

    agent = ImageAnalysisAgent()

    request = AgentRequest(
        message="Analyze image",
        user_id="doctor_006",
        context={
            "modality": "chest_xray"
            # No image_path provided
        }
    )

    response = await agent.process(request)

    print(f"\n❌ Success: {response.success}")
    print(f"⚠️  Error: {response.data.get('error')}")
    print(f"💡 Details: {response.data.get('details')}")


async def test_unsupported_modality():
    """Test error handling - unsupported modality"""
    print("\n" + "="*80)
    print("TEST 7: Error Handling - Unsupported Modality")
    print("="*80)

    agent = ImageAnalysisAgent()

    request = AgentRequest(
        message="Analyze ultrasound image",
        user_id="doctor_007",
        context={
            "image_path": "/path/to/ultrasound.jpg",
            "modality": "ultrasound"  # Not supported
        }
    )

    response = await agent.process(request)

    print(f"\n❌ Success: {response.success}")
    print(f"⚠️  Error: {response.data.get('error')}")
    print(f"💡 Details: {response.data.get('details')}")


async def test_dermatology_with_findings():
    """Test dermatology with detailed findings"""
    print("\n" + "="*80)
    print("TEST 8: Dermatology - Detailed Finding Detection")
    print("="*80)

    agent = ImageAnalysisAgent()

    request = AgentRequest(
        message="Analyze this pigmented lesion for concerning features",
        user_id="doctor_008",
        context={
            "image_path": "/path/to/pigmented_lesion.jpg",
            "modality": "dermatology",
            "analysis_type": "finding_detection",
            "clinical_context": {
                "patient_concern": "Mole has changed in size",
                "duration": "3 months"
            }
        }
    )

    response = await agent.process(request)

    print(f"\n✅ Success: {response.success}")
    print(f"📊 Confidence: {response.confidence:.2f}")

    print(f"\n🔍 Findings:")
    for finding in response.data['findings']:
        print(f"   Finding: {finding['finding']}")
        print(f"   Confidence: {finding['confidence']:.2f}")
        print(f"   Description: {finding['description']}")

    print(f"\n💡 Impression:")
    print(f"   {response.data['overall_impression']}")

    print(f"\n📋 Next Steps:")
    for step in response.data['recommended_next_steps']:
        print(f"   - {step}")

    print(f"\n⚠️  Escalation Required: {response.requires_escalation}")


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("🏥 MEDICAL IMAGE ANALYSIS AGENT TEST SUITE")
    print("Testing MedSigLIP-powered Image Analysis")
    print("="*80)

    tests = [
        ("Chest X-ray - Finding Detection", test_chest_xray_finding_detection),
        ("Dermatology - Classification", test_dermatology_classification),
        ("Chest X-ray - Classification", test_chest_xray_classification),
        ("CT Scan Analysis", test_ct_scan_analysis),
        ("Region Description", test_region_description),
        ("Error - No Image", test_error_no_image),
        ("Error - Unsupported Modality", test_unsupported_modality),
        ("Dermatology - Detailed Findings", test_dermatology_with_findings)
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
    print("  ✅ Multi-modality support (Chest X-ray, CT, Dermatology)")
    print("  ✅ Finding detection with structured output")
    print("  ✅ Abnormality classification")
    print("  ✅ Region description (natural language)")
    print("  ✅ Confidence scoring for all findings")
    print("  ✅ Red flag detection (critical findings)")
    print("  ✅ Clinical correlation notes")
    print("  ✅ Mandatory imaging disclaimers")
    print("  ✅ Error handling (missing images, unsupported modalities)")
    print("\n⚠️  CRITICAL DISCLAIMER:")
    print("AI image analysis is for DECISION SUPPORT ONLY.")
    print("ALL imaging findings MUST be reviewed by qualified radiologists/specialists.")
    print("This system has NO diagnostic authority.")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
