import sys
import os
import ast

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, render_template_string
from core.parser import extract_text
from core.recommender import analyze_resume
from core.guides import generate_role_based_guide
import markdown

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Skill Gap Recommender</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Inter', sans-serif;
            background: #f7f8fa;
            margin: 0;
            padding: 2rem;
            color: #222;
        }
        .container {
            max-width: 750px;
            margin: 0 auto;
            background: #fff;
            padding: 2rem;
            border-radius: 16px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.08);
        }
        h2 { text-align: center; font-size: 1.8rem; font-weight: 600; margin-bottom: 1rem; }
        h3 { font-size: 1.2rem; margin-bottom: 1rem; }
        .upload-form {
            text-align: center;
            margin-bottom: 1.5rem;
            border: 2px dashed #ccc;
            border-radius: 12px;
            padding: 1.5rem;
            background: #fafafa;
        }
        input[type="file"] { margin: 0.5rem 0; }
        button {
            background: linear-gradient(135deg, #007BFF, #00A6FF);
            color: white;
            border: none;
            padding: 0.6rem 1.2rem;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            font-size: 0.9rem;
            transition: opacity 0.2s;
        }
        button:hover { opacity: 0.85; }
        .job-card {
            background: #f1f5ff;
            border-left: 5px solid #007BFF;
            border-radius: 10px;
            padding: 1.2rem 1.4rem;
            margin-bottom: 1rem;
        }
        .job-card h4 { margin: 0 0 0.5rem 0; font-size: 1.05rem; }
        .match-pct {
            display: inline-block;
            background: #007BFF;
            color: white;
            border-radius: 20px;
            padding: 2px 10px;
            font-size: 0.85rem;
            font-weight: 600;
            margin-left: 8px;
        }
        .skill-label { font-size: 0.82rem; font-weight: 600; color: #555; margin-top: 0.5rem; }
        .skill-tag {
            display: inline-block;
            padding: 2px 9px;
            border-radius: 12px;
            font-size: 0.8rem;
            margin: 2px;
        }
        .tag-matched { background: #d4edda; color: #155724; }
        .tag-missing { background: #f8d7da; color: #721c24; }
        .roadmap-section {
            background: #f1f5ff;
            border-left: 5px solid #28a745;
            border-radius: 10px;
            padding: 1.4rem;
            margin-top: 1.5rem;
        }
        .roadmap-section h3 { color: #155724; }
        .guide-block {
            background: white;
            border-radius: 8px;
            padding: 1rem 1.2rem;
            margin-top: 0.8rem;
            border: 1px solid #dde6ff;
            font-size: 0.92rem;
            line-height: 1.6;
        }
        .guide-block ul { margin: 0.3rem 0 0 1rem; padding: 0; }
        .error {
            background: #ffe6e6;
            color: #d9534f;
            padding: 1rem;
            border-radius: 8px;
            margin-top: 1rem;
            font-weight: 500;
        }
        hr { border: none; border-top: 1px solid #e0e0e0; margin: 1.2rem 0; }
    </style>
</head>
<body>
<div class="container">
    <h2>🔍 Skill Gap Recommender</h2>

    <!-- Upload Form -->
    <div class="upload-form">
        <form action="/upload" method="post" enctype="multipart/form-data">
            <p style="margin:0 0 0.7rem 0; color:#555;">Upload your resume to find matching roles</p>
            <input type="file" name="resume" accept=".pdf,.png,.jpg,.jpeg" required><br><br>
            <button type="submit">Analyze Resume</button>
        </form>
    </div>

    <!-- Job Matches -->
    {% if matches %}
    <h3>📄 Top matches for <em>{{ filename }}</em></h3>
    {% for job in matches %}
    <div class="job-card">
        <h4>
            {{ job.title }}
            <span class="match-pct">{{ job.match_percent }}%</span>
        </h4>

        <div class="skill-label">✅ Matched</div>
        <div>
            {% for s in job.matched %}
            <span class="skill-tag tag-matched">{{ s }}</span>
            {% endfor %}
            {% if not job.matched %}<span style="color:#888;font-size:0.85rem;">None</span>{% endif %}
        </div>

        <div class="skill-label" style="margin-top:0.6rem;">❌ Missing</div>
        <div>
            {% for s in job.missing %}
            <span class="skill-tag tag-missing">{{ s }}</span>
            {% endfor %}
            {% if not job.missing %}<span style="color:#888;font-size:0.85rem;">None</span>{% endif %}
        </div>

        {% if job.missing %}
        <form action="/roadmap" method="post" style="margin-top:0.9rem;">
            <input type="hidden" name="job_title" value="{{ job.title }}">
            <input type="hidden" name="matched" value="{{ job.matched }}">
            <input type="hidden" name="missing" value="{{ job.missing }}">
            <button type="submit">Generate Roadmap →</button>
        </form>
        {% else %}
        <p style="margin-top:0.8rem; color:#155724; font-weight:600;">🎉 You meet all requirements!</p>
        {% endif %}
    </div>
    {% endfor %}
    {% endif %}

    <!-- Roadmap -->
    {% if roadmap %}
    <div class="roadmap-section">
        <h3>🗺️ Learning Roadmap: {{ roadmap.title }}</h3>
        <p style="margin:0 0 0.4rem 0;">
            <span class="skill-label">Skills to learn: </span>
            {% for s in roadmap.missing %}
            <span class="skill-tag tag-missing">{{ s }}</span>
            {% endfor %}
        </p>
        <hr>
        {% for guide in roadmap.guides %}
        <div class="guide-block">{{ guide | safe }}</div>
        {% endfor %}
    </div>
    {% endif %}

    <!-- Error -->
    {% if error %}
    <div class="error">⚠️ {{ error }}</div>
    {% endif %}

</div>
</body>
</html>
"""


@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML)


@app.route("/upload", methods=["POST"])
def upload():
    if "resume" not in request.files:
        return render_template_string(HTML, error="No file uploaded.")

    file = request.files["resume"]
    if not file.filename:
        return render_template_string(HTML, error="No file selected.")

    allowed_extensions = {'.pdf', '.png', '.jpg', '.jpeg'}
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        return render_template_string(HTML, error="Unsupported file type. Upload PDF, PNG, JPG, or JPEG.")

    try:
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        resume_text = extract_text(file_path)
        os.remove(file_path)

        if not resume_text.strip():
            return render_template_string(HTML, error="Could not extract text from file.")

        raw_results = analyze_resume(resume_text)

        if not raw_results:
            return render_template_string(HTML, error="No job matches found.")

        # Normalize field names and filter > 60%, top 5
        matches = []
        for job in raw_results:
            pct = job.get("match_percent", job.get("match_percentage", 0))
            if pct > 60:
                matches.append({
                    "title":         job.get("title", job.get("job_title", "Unknown")),
                    "match_percent": round(pct, 1),
                    "matched":       job.get("matched", job.get("matched_skills", [])),
                    "missing":       job.get("missing", job.get("missing_skills", [])),
                })

        matches.sort(key=lambda x: x["match_percent"], reverse=True)
        matches = matches[:5]

        if not matches:
            return render_template_string(HTML, error="No jobs found with >60% match for your resume.")

        return render_template_string(HTML, matches=matches, filename=file.filename)

    except Exception as e:
        print(f"[Upload error] {e}")
        return render_template_string(HTML, error=f"Error processing file: {str(e)}")


@app.route("/roadmap", methods=["POST"])
def roadmap():
    job_title   = request.form.get("job_title", "")
    matched_raw = request.form.get("matched", "[]")
    missing_raw = request.form.get("missing", "[]")

    try:
        matched_skills = ast.literal_eval(matched_raw)
    except Exception:
        matched_skills = []

    try:
        missing_skills = ast.literal_eval(missing_raw)
    except Exception:
        missing_skills = []

    guides_raw = generate_role_based_guide(job_title, matched_skills, missing_skills)
    guides = [markdown.markdown(g) for g in guides_raw]

    return render_template_string(HTML, roadmap={
        "title":   job_title,
        "matched": matched_skills,
        "missing": missing_skills,
        "guides":  guides,
    })


if __name__ == "__main__":
    app.run(debug=True, host="localhost", port=5000)