"""
core/guides.py
AI-generated learning guides via Gemini, with local JSON caching.
"""

import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GRPC_LOG_SEVERITY_THRESHOLD"] = "ERROR"

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

CACHE_PATH = os.path.join(os.path.dirname(__file__), "../data/guide_cache.json")

# Static fallback guides used when Gemini is unavailable
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


def get_guide(skill):
    return learning_guides.get(skill, f"Learn {skill} from official docs and tutorials.")


def _load_cache():
    if not os.path.exists(CACHE_PATH):
        return {}
    try:
        with open(CACHE_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save_cache(cache):
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "w") as f:
        json.dump(cache, f, indent=2)


def _cache_key(skill, job_title=""):
    # skill + job_title combined so Docker for Backend Dev
    # and Docker for DevOps Engineer are stored separately
    return f"{skill.lower()}||{job_title.lower().strip()}"


def generate_role_based_guide(job_title, matched_skills, missing_skills):
    if not missing_skills:
        return ["No missing skills — you're fully matched!"]

    cache = _load_cache()
    cached_results = {}
    skills_to_generate = []

    for skill in missing_skills:
        key = _cache_key(skill, job_title)
        if key in cache:
            print(f"[Cache] Hit: {skill} ({job_title})")
            cached_results[skill] = cache[key]
        else:
            skills_to_generate.append(skill)

    # everything was cached, no API call needed
    if not skills_to_generate:
        return [cached_results[skill] for skill in missing_skills]

    # no API key, use static fallbacks
    if not os.getenv("GEMINI_API_KEY"):
        for skill in skills_to_generate:
            guide = get_guide(skill)
            cached_results[skill] = guide
            cache[_cache_key(skill, job_title)] = guide
        _save_cache(cache)
        return [cached_results[skill] for skill in missing_skills]

    # single Gemini call for all uncached skills
    prompt = f"""
    You are an AI career mentor.
    The candidate wants to work as a {job_title}.
    They already know: {', '.join(matched_skills)}.
    They need to learn: {', '.join(skills_to_generate)}.

    For each missing skill give 2-3 short actionable steps with specific resources.
    Format your response exactly like this:

    SKILL: <skill name>
    <guide text>

    SKILL: <skill name>
    <guide text>

    No other text outside this format.
    """

    try:
        model = genai.GenerativeModel(model_name="models/gemini-2.5-flash")
        response = model.generate_content(prompt)
        text = (response.text or "").strip()

        if not text:
            raise ValueError("Empty response from Gemini")

        # parse "SKILL: name\nguide text" blocks
        blocks = text.split("SKILL:")
        parsed = {}
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            lines = block.splitlines()
            skill_name = lines[0].strip()
            guide_text = "\n".join(lines[1:]).strip()
            if skill_name and guide_text:
                parsed[skill_name.lower()] = guide_text

        for skill in skills_to_generate:
            guide = parsed.get(skill.lower(), get_guide(skill))
            cached_results[skill] = guide
            cache[_cache_key(skill, job_title)] = guide

        _save_cache(cache)
        print(f"[Cache] Saved {len(skills_to_generate)} new guides")

    except Exception as e:
        print(f"[Gemini API error] {e}")
        for skill in skills_to_generate:
            guide = get_guide(skill)
            cached_results[skill] = guide
            cache[_cache_key(skill, job_title)] = guide
        _save_cache(cache)

    return [cached_results[skill] for skill in missing_skills]


def generate_ai_guide(skill, user_skills, job_title=None):
    job_title = job_title or ""
    key = _cache_key(skill, job_title)

    cache = _load_cache()
    if key in cache:
        print(f"[Cache] Hit: {skill}")
        return cache[key]

    if not os.getenv("GEMINI_API_KEY"):
        return get_guide(skill)

    prompt = f"""
    The user currently knows: {', '.join(user_skills)}.
    They are missing the skill: {skill}.
    The target job role is: {job_title or 'unspecified'}.
    Suggest one concise practical learning path (under two sentences)
    explaining what to focus on first and one resource to learn it.
    """

    try:
        model = genai.GenerativeModel(model_name="models/gemini-2.5-flash")
        response = model.generate_content(prompt)
        text = (response.text or "").strip()

        if not text:
            raise ValueError("Empty response")

        cache[key] = text
        _save_cache(cache)
        return text

    except Exception as e:
        print(f"[Gemini API error] {e}")
        fallback = get_guide(skill)
        cache[key] = fallback
        _save_cache(cache)
        return fallback