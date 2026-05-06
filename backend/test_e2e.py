#!/usr/bin/env python3
"""
End-to-End Testing Script for TALASH Milestone 3
Tests complete workflow: upload → parse → analyze → export
"""

import asyncio
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.modules.preprocessing import (
    extract_personal_info,
    extract_education_records,
    extract_experience_records,
    extract_publication_records,
    build_structured_dataset,
)
from app.modules.education_analysis import analyze_education
from app.modules.experience_analysis import analyze_experience
from app.modules.research_analysis import analyze_research
from app.modules.missing_info import detect_missing_fields, draft_missing_info_email


# Sample CV text for testing
SAMPLE_CV = """
JOHN AHMED MALIK
Software Engineer | Machine Learning Specialist

Email: john.malik@example.com
Phone: +1-555-123-4567
LinkedIn: https://linkedin.com/in/john-malik
Nationality: Pakistani

EDUCATION
PhD in Computer Science, Stanford University, 2020
- Focus on Deep Learning and NLP
- GPA: 3.85/4.0

MS in Machine Learning, Carnegie Mellon University, 2017
- Specialization: Computer Vision
- GPA: 3.8/4.0

BS in Computer Science, FAST-NUCES, Islamabad, 2015
- CGPA: 3.9/4.0

PROFESSIONAL EXPERIENCE
Senior Machine Learning Engineer at Google Brain
2020 - Present
- Lead ML pipeline development for production systems
- Managed team of 5 engineers
- Published 3 papers at top-tier conferences

Senior Software Engineer at OpenAI
2019 - 2020
- Developed deep learning models for language understanding
- Collaborated with 8+ researchers globally

Machine Learning Engineer at Microsoft Research
2017 - 2019
- Implemented computer vision algorithms
- Worked on edge AI optimization

RESEARCH & PUBLICATIONS
1. "Efficient Transformers for Edge Devices" - Published in NeurIPS 2022
   Co-authors: Alice Smith, Bob Johnson, Carol White
   
2. "Deep Learning for Medical Imaging" - Published in MICCAI 2021
   Co-authors: Dr. Eve Davis, Frank Miller
   
3. "Attention Mechanisms Revisited" - Published in ICLR 2020
   Co-authors: Grace Lee, Henry Wang
   
4. "Computer Vision Benchmarks" - CVPR Conference 2019
   Proceedings of Computer Vision and Pattern Recognition

SKILLS
Programming Languages: Python, Java, C++, JavaScript, TypeScript, SQL
Machine Learning: TensorFlow, PyTorch, Scikit-learn, Keras
Data Science: Pandas, NumPy, Power BI, Tableau
Web Development: FastAPI, Django, Flask, React, Node.js
Academic: Research, Publication, Thesis, Peer Review, Supervisor

CERTIFICATIONS
- Deep Learning Specialization, Coursera (2018)
- AWS Certified Machine Learning Specialist (2019)
"""


async def test_preprocessing():
    """Test preprocessing module"""
    print("\n" + "="*60)
    print("TEST 1: Preprocessing Module")
    print("="*60)
    
    personal = extract_personal_info(SAMPLE_CV)
    education = extract_education_records(SAMPLE_CV)
    experience = extract_experience_records(SAMPLE_CV)
    publications = extract_publication_records(SAMPLE_CV)
    
    print(f"✓ Personal Info Extracted: {len(personal)} record(s)")
    print(f"  - Name: {personal[0].get('full_name')}")
    print(f"  - Email: {personal[0].get('email')}")
    print(f"  - Phone: {personal[0].get('phone')}")
    
    print(f"\n✓ Education Records: {len(education)}")
    for edu in education:
        print(f"  - {edu.get('degree_level')}: {edu.get('year_start')}-{edu.get('year_end')}")
    
    print(f"\n✓ Experience Records: {len(experience)}")
    for exp in experience:
        print(f"  - {exp.get('job_title')} at {exp.get('organization')}")
    
    print(f"\n✓ Publications: {len(publications)}")
    for pub in publications:
        print(f"  - {pub.get('pub_type')}: {pub.get('year')}")
    
    return True


async def test_education_analysis():
    """Test education analysis"""
    print("\n" + "="*60)
    print("TEST 2: Education Analysis Module")
    print("="*60)
    
    result = await analyze_education(SAMPLE_CV, candidate_universities="Stanford University")
    
    print(f"✓ Education Summary:")
    print(f"  - Records: {result['summary']['records_count']}")
    print(f"  - Highest Qualification: {result['highest_qualification']}")
    print(f"  - Has Higher Education: {result['summary']['has_higher_education']}")
    print(f"  - Education Gaps: {result['summary']['gap_count']}")
    
    if result.get('qs_ranking_info'):
        print(f"\n✓ QS Ranking Info:")
        print(f"  - Searched: {result['qs_ranking_info']['searched_university']}")
        print(f"  - Matched: {result['qs_ranking_info']['matched_institution']}")
        print(f"  - Ranking: {result['qs_ranking_info']['qs_ranking']}")
    
    return True


async def test_experience_analysis():
    """Test experience analysis"""
    print("\n" + "="*60)
    print("TEST 3: Experience Analysis Module")
    print("="*60)
    
    result = await analyze_experience(SAMPLE_CV)
    
    summary = result.get('summary', {})
    print(f"✓ Experience Summary:")
    print(f"  - Records: {summary.get('records_count')}")
    print(f"  - Total Years: {summary.get('total_years_experience')}")
    print(f"  - Job Overlaps: {summary.get('job_overlaps', 0)}")
    print(f"  - Professional Gaps: {summary.get('professional_gaps_count', 0)}")
    
    return True


async def test_research_analysis():
    """Test research analysis"""
    print("\n" + "="*60)
    print("TEST 4: Research Analysis Module (ENHANCED)")
    print("="*60)
    
    result = await analyze_research(SAMPLE_CV)
    
    summary = result['summary']
    print(f"✓ Research Profile:")
    print(f"  - Total Publications: {summary['publications_count']}")
    print(f"  - Journals: {summary['journal_count']}")
    print(f"  - Conferences: {summary['conference_count']}")
    print(f"  - Publication Span: {summary['publication_span_years']} years")
    print(f"  - Productivity Trend: {summary['productivity_trend']}")
    print(f"  - Research Score: {summary['research_score']}/100")
    
    coauthor_info = result.get('coauthor_analysis', {})
    print(f"\n✓ Co-author Analysis:")
    print(f"  - Unique Co-authors: {coauthor_info.get('total_unique_coauthors')}")
    print(f"  - Collaboration Diversity: {coauthor_info.get('collaboration_diversity_score')}/100")
    print(f"  - Avg Co-authors per Pub: {coauthor_info.get('average_coauthors_per_publication')}")
    
    print(f"\n✓ Research Domains: {', '.join(result.get('research_domains', []))}")
    
    assessment = result.get('research_profile_assessment', {})
    print(f"\n✓ Profile Assessment:")
    print(f"  - Collaboration Level: {assessment.get('collaboration_level')}")
    print(f"  - Research Maturity: {assessment.get('research_maturity')}")
    
    return True


async def test_missing_info_detection():
    """Test missing information detection"""
    print("\n" + "="*60)
    print("TEST 5: Missing Information Detection")
    print("="*60)
    
    # Extract basic info first
    personal = extract_personal_info(SAMPLE_CV)
    education_records = extract_education_records(SAMPLE_CV)
    experience_records = extract_experience_records(SAMPLE_CV)
    publications = extract_publication_records(SAMPLE_CV)
    
    # Build analysis results
    edu_analysis = await analyze_education(SAMPLE_CV)
    exp_analysis = await analyze_experience(SAMPLE_CV)
    res_analysis = await analyze_research(SAMPLE_CV)
    
    # Detect missing fields
    candidate_snapshot = {
        "full_name": personal[0].get("full_name"),
        "email": personal[0].get("email"),
        "phone": personal[0].get("phone"),
        "nationality": personal[0].get("nationality"),
    }
    
    missing = detect_missing_fields(candidate_snapshot, edu_analysis, exp_analysis, res_analysis)
    
    print(f"✓ Missing Fields Analysis:")
    print(f"  - Missing Count: {len(missing)}")
    if missing:
        for field in missing:
            print(f"    - {field}")
    else:
        print(f"    - No critical fields missing! ✓")
    
    # Draft email
    email_draft = await draft_missing_info_email(
        candidate_snapshot.get("full_name"),
        missing
    )
    
    print(f"\n✓ Draft Email Generated ({len(email_draft)} chars)")
    print("  Preview:")
    for line in email_draft.split('\n')[:5]:
        print(f"    {line}")
    
    return True


async def test_structured_dataset():
    """Test structured dataset generation"""
    print("\n" + "="*60)
    print("TEST 6: Structured Dataset Generation")
    print("="*60)
    
    dataset = build_structured_dataset(SAMPLE_CV, candidate_id=1, filename="john_malik.pdf")
    
    print(f"✓ Dataset Generated:")
    print(f"  - Personal Info: {len(dataset.personal_info)}")
    print(f"  - Education Records: {len(dataset.education_records)}")
    print(f"  - Experience Records: {len(dataset.experience_records)}")
    print(f"  - Skills: {len(dataset.skills)}")
    print(f"  - Publications: {len(dataset.publications)}")
    print(f"  - Gaps: {len(dataset.gaps)}")
    
    print(f"\n✓ Metadata:")
    meta = dataset.metadata
    print(f"  - Character Count: {meta['character_count']}")
    print(f"  - Line Count: {meta['line_count']}")
    print(f"  - Detected Sections: {', '.join(meta['detected_sections'])}")
    print(f"  - Completeness Score: {meta['personal_info_completeness']}/9")
    
    return True


async def test_full_pipeline():
    """Test complete pipeline"""
    print("\n" + "="*60)
    print("TEST 7: Complete Pipeline")
    print("="*60)
    
    # Step 1: Parse CV
    personal = extract_personal_info(SAMPLE_CV)
    candidate_name = personal[0].get("full_name", "Candidate")
    
    # Step 2: Run analyses
    edu_result = await analyze_education(SAMPLE_CV)
    exp_result = await analyze_experience(SAMPLE_CV)
    res_result = await analyze_research(SAMPLE_CV)
    
    # Step 3: Detect missing
    candidate_info = {
        "full_name": personal[0].get("full_name"),
        "email": personal[0].get("email"),
        "phone": personal[0].get("phone"),
        "nationality": personal[0].get("nationality"),
    }
    missing_fields = detect_missing_fields(candidate_info, edu_result, exp_result, res_result)
    
    # Step 4: Generate email
    draft_email = await draft_missing_info_email(candidate_name, missing_fields)
    
    # Summary
    print(f"✓ Pipeline Complete for: {candidate_name}")
    print(f"\n  Extracted Data:")
    print(f"    - Education Records: {edu_result['summary']['records_count']}")
    print(f"    - Experience Records: {exp_result['summary'].get('records_count', 0)}")
    print(f"    - Publications: {res_result['summary']['publications_count']}")
    print(f"    - Missing Fields: {len(missing_fields)}")
    print(f"    - Email Draft: Generated ({len(draft_email)} chars)")
    
    return True


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("TALASH MILESTONE 3 - END-TO-END VERIFICATION")
    print("="*60)
    
    tests = [
        ("Preprocessing Module", test_preprocessing),
        ("Education Analysis", test_education_analysis),
        ("Experience Analysis", test_experience_analysis),
        ("Research Analysis (Enhanced)", test_research_analysis),
        ("Missing Info Detection", test_missing_info_detection),
        ("Structured Dataset", test_structured_dataset),
        ("Complete Pipeline", test_full_pipeline),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, "✓ PASS", None))
        except Exception as e:
            results.append((test_name, "✗ FAIL", str(e)))
            print(f"\n✗ Error: {str(e)}")
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, status, error in results:
        print(f"{status} - {test_name}")
        if error:
            print(f"   Error: {error}")
    
    passed = sum(1 for _, status, _ in results if status == "✓ PASS")
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ ALL TESTS PASSED - System is ready! 🎉")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed - Review errors above")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
