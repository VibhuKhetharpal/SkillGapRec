"""
core/guides.py  — Gemini Edition
Provides static + AI-generated learning guides using Google's Gemini API.
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv

# Suppress noisy gRPC logs
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GRPC_LOG_SEVERITY_THRESHOLD"] = "ERROR"

# Load environment and configure Gemini v1 client
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# --- Static fallback guides ---
learning_guides = {
    "Python": "Advance your Python by building small automation or data projects.",
    "JavaScript": "Learn JS fundamentals from MDN and build DOM projects.",
    "React": "Start with React official docs and build a To-Do app.",
    "TypeScript": "Read the TypeScript handbook and refactor a JS script.",
    "SQL": "Practice SELECT, JOIN, and subqueries on LeetCode or W3Schools.",
    "Tableau": "Take Tableau beginner tutorials on YouTube.",
    "Statistics": "Learn core concepts from Khan Academy.",
    "Machine Learning": "Follow a beginner ML playlist or course.",
    "Docker": "Do Docker's official Get-Started tutorial.",
    "AWS": "Try AWS Cloud Practitioner free course.",
    "Django": "Follow Django's official tutorial and deploy a mini app.",
    "HTML": "Learn HTML5 structure and semantics from W3Schools.",
    "CSS": "Practice Flexbox and Grid with freeCodeCamp.",
    "Excel": "Master formulas and pivot tables with Microsoft Learn.",
    "Git": "Learn basic Git commands using GitHub Guides.",
    "PostgreSQL": "Install PostgreSQL and practice with sample databases.",
    "Node.js": "Build a REST API using Express.js and Node.js.",
    "MongoDB": "Learn NoSQL concepts and practice with MongoDB Atlas.",
    "Kubernetes": "Learn container orchestration with Kubernetes basics.",
    "CI/CD": "Set up GitHub Actions or Jenkins pipeline.",
    "Linux": "Practice Linux commands and system administration.",
    "Monitoring": "Learn tools like Prometheus and Grafana for system monitoring."
}

def get_guide(skill: str) -> str:
    """Return the static fallback guide."""
    return learning_guides.get(skill, "No guide available.")


def generate_ai_guide(skill: str, user_skills: list[str], job_title: str = None) -> str:
    """
    Generate a concise learning guide using Gemini if possible.
    Falls back to static guide if API key missing or call fails.
    """
    if not os.getenv("GEMINI_API_KEY"):
        return get_guide(skill)

    prompt = f"""
    The user currently knows: {', '.join(user_skills)}.
    They are missing the skill: {skill}.
    The target job role is: {job_title or 'unspecified'}.
    Suggest one concise, practical learning path (under two sentences)
    explaining what to focus on first and one resource to learn it.
    """

    try:
        model = genai.GenerativeModel(model_name="models/gemini-2.5-flash")
        response = model.generate_content(prompt)
        text = getattr(response, "text", None)
        if isinstance(text, str):
            cleaned = text.strip()
            if cleaned:
                return cleaned
        return get_guide(skill)
    except Exception as e:
        print(f"[Gemini API error] {e}")
        return get_guide(skill)