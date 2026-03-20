#!/usr/bin/env python3
"""
Skill Gap Recommender

This script compares resume skills with job requirements and calculates
skill match percentages for each job listing.
"""

import json
import os
from typing import List, Dict, Tuple
from core.guides import get_guide, generate_ai_guide
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment and configure Gemini
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Sample data - in a real implementation, these would be loaded from JSON files
SAMPLE_RESUME_SKILLS = [
    "Python",
    "HTML",
    "CSS", 
    "JavaScript",
    "SQL",
    "Git",
    "Problem Solving",
    "Team Collaboration"
]

SAMPLE_JOB_LISTINGS = [
    {
        "title": "Frontend Developer",
        "required_skills": ["HTML", "CSS", "JavaScript", "React", "TypeScript"]
    },
    {
        "title": "Backend Developer", 
        "required_skills": ["Python", "Django", "PostgreSQL", "Docker", "AWS"]
    },
    {
        "title": "Full Stack Developer",
        "required_skills": ["Python", "JavaScript", "HTML", "CSS", "React", "Node.js", "MongoDB"]
    },
    {
        "title": "Data Analyst",
        "required_skills": ["Python", "SQL", "Excel", "Tableau", "Statistics", "Machine Learning"]
    },
    {
        "title": "DevOps Engineer",
        "required_skills": ["Docker", "Kubernetes", "AWS", "CI/CD", "Linux", "Monitoring"]
    }
]


def load_data(resume_file: str = None, jobs_file: str = None) -> Tuple[List[str], List[Dict]]:
    """
    Load resume skills and job listings from JSON files.
    
    Args:
        resume_file: Path to resume skills JSON file
        jobs_file: Path to job listings JSON file
        
    Returns:
        Tuple of (resume_skills, job_listings)
    """
    try:
        if resume_file:
            with open(resume_file, 'r') as f:
                resume_data = json.load(f)
                resume_skills = resume_data.get('skills', resume_data) if isinstance(resume_data, dict) else resume_data
        else:
            resume_skills = SAMPLE_RESUME_SKILLS
            
        if jobs_file:
            with open(jobs_file, 'r') as f:
                job_listings = json.load(f)
        else:
            job_listings = SAMPLE_JOB_LISTINGS
            
        return resume_skills, job_listings
        
    except FileNotFoundError:
        print(f"Warning: Could not find specified JSON files. Using sample data.")
        return SAMPLE_RESUME_SKILLS, SAMPLE_JOB_LISTINGS
    except json.JSONDecodeError:
        print(f"Warning: Invalid JSON format. Using sample data.")
        return SAMPLE_RESUME_SKILLS, SAMPLE_JOB_LISTINGS


def compare_skills(user_skills: List[str], job_skills: List[str]) -> Dict:
    """
    Compare user skills with job requirements and calculate match metrics.
    
    Args:
        user_skills: List of skills from resume
        job_skills: List of required skills for a job
        
    Returns:
        Dictionary with matched_skills, missing_skills, and match_percentage
    """
    # Convert to lowercase sets for case-insensitive comparison
    user_skills_set = {skill.lower().strip() for skill in user_skills}
    job_skills_set = {skill.lower().strip() for skill in job_skills}
    
    # Find matches and differences
    matched_skills_set = user_skills_set.intersection(job_skills_set)
    missing_skills_set = job_skills_set - user_skills_set
    
    # Convert back to original case from job_skills for display
    matched_skills = [skill for skill in job_skills 
                     if skill.lower().strip() in matched_skills_set]
    missing_skills = [skill for skill in job_skills 
                     if skill.lower().strip() in missing_skills_set]
    
    # Calculate match percentage
    total_required = len(job_skills)
    match_percentage = (len(matched_skills) / total_required * 100) if total_required > 0 else 0
    
    return {
        'matched_skills': matched_skills,
        'missing_skills': missing_skills,
        'match_percentage': match_percentage
    }


def get_recommendations(user_skills: list[str], job_listings: list[dict]) -> list[dict]:
    """
    Filter job listings to those where match_percentage is between 60–90%.
    Add learning guides for missing skills.
    """
    results = []
    for job in job_listings:
        comparison = compare_skills(user_skills, job["required_skills"])
        match_pct = comparison["match_percentage"]
        
        if 60 <= match_pct <= 90:
            missing = comparison["missing_skills"]
            guides = [(skill, generate_ai_guide(skill, user_skills, job["title"])) for skill in missing]
            
            results.append({
                "job_title": job["title"],
                "match_percentage": round(match_pct, 1),
                "matched_skills": comparison["matched_skills"],
                "missing_skills": missing,
                "missing_guides": guides
            })
    return results


def ai_compare_resume_to_jobs(resume_text: str) -> List[Dict]:
    """
    Optimized: single Gemini call for all jobs
    """
    try:
        if not os.getenv("GEMINI_API_KEY"):
            print("[AI Compare] No API key → fallback")
            return []

        path = os.path.join(os.path.dirname(__file__), "../data/job_listings.json")
        with open(path) as f:
            job_data = json.load(f)

        model = genai.GenerativeModel("models/gemini-2.5-flash")

        prompt = f"""
        You are an AI career assistant.

        Jobs and required skills:
        {job_data}

        Resume:
        {resume_text[:3000]}

        For each job return JSON list:
        [
          {{
            "title": "...",
            "match_percent": number,
            "matched_skills": [...],
            "missing_skills": [...]
          }}
        ]
        """

        response = model.generate_content(prompt)
        text = (response.text or "").strip()

        if not text:
            raise ValueError("Empty response")

        # extract JSON array
        start = text.find("[")
        end = text.rfind("]") + 1
        if start == -1 or end <= start:
            raise ValueError("No JSON array found")

        data = json.loads(text[start:end])

        results = []
        for item in data:
            results.append({
                "title": item.get("title", "Unknown"),
                "match_percent": float(item.get("match_percent", 0)),
                "matched": item.get("matched_skills", []),
                "missing": item.get("missing_skills", [])
            })

        results.sort(key=lambda x: x.get("match_percent", 0), reverse=True)
        return results

    except Exception as e:
        print(f"[AI Compare Error] {e}")
        return []


def analyze_resume(resume_text: str) -> List[Dict]:
    """
    Compare extracted resume text with multiple job roles
    and return ranked match results using AI when available.
    Handles no matches and weak matches with appropriate messages.
    
    Args:
        resume_text: Extracted text from resume
        
    Returns:
        List of dictionaries with job analysis results, sorted by best match first
        or special message for no matches
    """
    if not resume_text.strip():
        return []

    # Try AI comparison first
    ai_results = ai_compare_resume_to_jobs(resume_text)
    if ai_results:
        print("[Analyze] Using AI-powered semantic comparison")
        # Check if best match is too weak
        best_match = ai_results[0] if ai_results else {}
        if best_match.get("match_percent", 0) <= 10:
            return [{
                "title": "No Suitable Match",
                "matched": [],
                "missing": [],
                "match_percent": 0,
                "message": "No suitable jobs found for your current skills. Try adding more relevant experience or skills."
            }]
        return ai_results
    
    # Fallback to keyword matching
    print("[Analyze] Using keyword-based matching")
    _, job_listings = load_data()
    
    # Convert resume text to a set of lowercase words (simple keyword extraction)
    resume_skills = set(
        word.lower() for word in resume_text.split() if len(word) > 2
    )

    results = []
    for job in job_listings:
        job_title = job.get("title", "Unknown Role")
        job_skills = set(s.lower() for s in job.get("required_skills", []))

        matched = sorted(list(resume_skills & job_skills))
        missing = sorted(list(job_skills - resume_skills))
        match_percent = round(
            (len(matched) / len(job_skills) * 100) if job_skills else 0, 1
        )

        results.append({
            "title": job_title,
            "matched": matched,
            "missing": missing,
            "match_percent": match_percent,
        })

    # Sort by best match first
    results.sort(key=lambda x: x["match_percent"], reverse=True)
    
    # Check if best match is too weak
    if not results or results[0].get("match_percent", 0) <= 10:
        return [{
            "title": "No Suitable Match",
            "matched": [],
            "missing": [],
            "match_percent": 0,
            "message": "No suitable jobs found for your current skills. Try adding more relevant experience or skills."
        }]
    
    return results


def display_results(results: List[Dict]) -> None:
    """
    Display the skill gap analysis results in a formatted manner.
    
    Args:
        results: List of dictionaries containing job analysis results
    """
    print("\n" + "="*60)
    print("SKILL GAP ANALYSIS RESULTS")
    print("="*60)
    
    for result in results:
        job_title = result['job_title']
        matched = ", ".join(result['matched_skills']) if result['matched_skills'] else "None"
        missing = ", ".join(result['missing_skills']) if result['missing_skills'] else "None"
        match_pct = result['match_percentage']
        
        print(f"\n🎯 {job_title} ({match_pct:.0f}% match)")
        print(f"Matched: {matched}")
        print(f"Missing: {missing}")
        
        # Display learning guides if available
        if 'missing_guides' in result and result['missing_guides']:
            print("Guide:")
            for skill, guide in result['missing_guides']:
                print(f" - {skill} → {guide}")
        
        print("-" * 40)
    
    # Summary statistics
    if results:
        avg_match = sum(result['match_percentage'] for result in results) / len(results)
        best_match = max(results, key=lambda x: x['match_percentage'])
        worst_match = min(results, key=lambda x: x['match_percentage'])
        
        print(f"\nSUMMARY:")
        print(f"Average Match Rate: {avg_match:.1f}%")
        print(f"Best Match: {best_match['job_title']} ({best_match['match_percentage']:.0f}%)")
        print(f"Worst Match: {worst_match['job_title']} ({worst_match['match_percentage']:.0f}%)")
