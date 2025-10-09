#!/usr/bin/env python3
"""
Skill Gap Recommender - CLI Runner
"""

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from core.recommender import load_data, get_recommendations, display_results

def main():
    print("Skill Gap Recommender")
    print("====================")

    # Load data (using sample data for now)
    resume_skills, job_listings = load_data()

    print(f"Loaded {len(resume_skills)} resume skills")
    print(f"Loaded {len(job_listings)} job listings")

    # Get recommendations using the new function
    results = get_recommendations(resume_skills, job_listings)

    # Display results
    if results:
        display_results(results)
    else:
        print("No jobs found with a 60–90% skill match.")

    # Save output to JSON for next module
    os.makedirs("output", exist_ok=True)
    with open("output/skill_gap_results.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main()