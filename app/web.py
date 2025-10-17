from flask import Flask, request, render_template_string
import os
from core.parser import extract_text
from core.recommender import analyze_resume
from core.guides import generate_role_based_guide
import markdown

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Inline HTML template
HTML = """
<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>Skill Gap Recommender</title>
    <link href=\"https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap\" rel=\"stylesheet\">
    <style>
        body {
            font-family: 'Inter', sans-serif;
            background: #f7f8fa;
            margin: 0;
            padding: 2rem;
            color: #222;
        }
        .container {
            max-width: 700px;
            margin: 0 auto;
            background: #fff;
            padding: 2rem;
            border-radius: 16px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.08);
        }
        h2 {
            text-align: center;
            font-size: 1.8rem;
            font-weight: 600;
            margin-bottom: 1rem;
        }
        form {
            text-align: center;
            margin-bottom: 1.5rem;
            border: 2px dashed #ccc;
            border-radius: 12px;
            padding: 1.5rem;
            background: #fafafa;
        }
        input[type=\"file\"] {
            margin: 0.5rem 0;
        }
        button {
            background: linear-gradient(135deg, #007BFF, #00A6FF);
            color: white;
            border: none;
            padding: 0.7rem 1.4rem;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: 0.2s ease;
        }
        button:hover {
            opacity: 0.9;
        }
        hr { margin: 1.5rem 0; }
        .result {
            background: #f1f5ff;
            padding: 1.2rem;
            border-radius: 10px;
            border-left: 5px solid #007BFF;
        }
        .error {
            background: #ffe6e6;
            color: #d9534f;
            padding: 1rem;
            border-radius: 8px;
            margin-top: 1rem;
            font-weight: 500;
        }
    </style>
    </head>
<body>
    <div class=\"container\">
        <h2>🎯 Skill Gap Recommender</h2>
        <form action=\"/upload\" method=\"post\" enctype=\"multipart/form-data\"> 
            <input type=\"file\" name=\"resume\" accept=\".pdf,.png,.jpg,.jpeg\" required><br>
            <button type=\"submit\">Analyze Resume</button>
        </form>

        {% if result %}
        <div class=\"result\">
            <h3>📄 Results for {{ filename }}</h3>
            <p><b>Best Match:</b> {{ result['title'] }} ({{ result['match_percent'] }}%)</p>
            <p><b>Matched Skills:</b> {{ result['matched'] }}</p>
            <p><b>Missing Skills:</b> {{ result['missing'] }}</p>
            <p><b>AI Learning Guides:</b></p>
            <ul>
                {% for g in result['guides'] %}
                    <li>{{ g | safe }}</li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}

        {% if error %}
        <div class=\"error\">⚠️ Error: {{ error }}</div>
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
        return render_template_string(HTML, error="No file uploaded")

    file = request.files["resume"]
    if not file.filename:
        return render_template_string(HTML, error="No file selected")

    # Validate file type
    allowed_extensions = {'.pdf', '.png', '.jpg', '.jpeg'}
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        return render_template_string(HTML, error="Unsupported file type. Please upload PDF, PNG, JPG, or JPEG files.")

    try:
        # Save uploaded file
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        # Extract text from resume
        resume_text = extract_text(file_path)
        if not resume_text.strip():
            return render_template_string(HTML, error="Could not extract text from the uploaded file")

        # Analyze resume for skills (returns list of job matches)
        print(f"[Web] Analyzing resume text length: {len(resume_text)}")
        results = analyze_resume(resume_text)
        print(f"[Web] Analysis results: {len(results)} jobs found")
        
        if not results:
            return render_template_string(HTML, error="No job matches found for this resume")

        # Pick best-matched role
        best_match = results[0] if isinstance(results, list) and results else {}
        job_title = best_match.get("title", "Unknown Role")
        matched_skills = best_match.get("matched", [])
        missing_skills = best_match.get("missing", [])
        print(f"[Web] Best match: {job_title}, missing skills: {missing_skills}")

        # Generate role-specific AI guides
        print(f"[Web] Generating guides for {len(missing_skills)} missing skills")
        best_match["guides"] = generate_role_based_guide(job_title, matched_skills, missing_skills)
        # Convert Markdown to HTML for clean rendering
        best_match["guides"] = [markdown.markdown(g, extensions=["extra"]) for g in best_match["guides"]]
        print(f"[Web] Generated {len(best_match['guides'])} guides")

        # Clean up uploaded file
        os.remove(file_path)

        return render_template_string(HTML, result=best_match, filename=file.filename)

    except Exception as e:
        print(f"Error processing file: {e}")
        return render_template_string(HTML, error=f"Error processing file: {str(e)}")

if __name__ == "__main__":
    app.run(debug=True, host="localhost", port=5000)
