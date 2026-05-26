  
from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os
import json

load_dotenv()

app = Flask(__name__)
CORS(app)

@app.route("/ping")
def ping():
    return "pong", 200

@app.route("/form_generation", methods=["POST"])
def form_generation():
    try:
        llm = ChatGroq(
            model="llama-3.1-8b-instant",
            api_key=os.getenv("API_KEY"),
            temperature=0.5
        )

        data = request.json
        role = data.get("role")
        experience = data.get("experience")
        sections = data.get("sections")

        feedback_sections = {}

        for section in sections:
            prompt = f"""
            Generate 5 role-specific performance evaluation questions.
            Role: {role}
            Experience Level: {experience}
            Section: {section}

            Important instructions based on experience level:
            - If experience is 0-1 years or "fresher": Use simple language, ask about basic concepts,
              learning attitude, foundational skills, and willingness to grow. Avoid jargon.
              Focus on potential, not past achievements.
            - If experience is 1-3 years: Ask about hands-on application of skills, small project
              ownership, and early problem-solving.
            - If experience is 3+ years: Ask about advanced skills, leadership, strategy,
              and measurable impact.

            Tailor every question to match the {experience} experience level for a {role}.
            Return ONLY a JSON array like:
            ["question1", "question2", "question3", "question4", "question5"]
            """

            response = llm.invoke(prompt)
            output_text = response.content

            start = output_text.find("[")
            end = output_text.rfind("]") + 1

            if start == -1 or end == -1:
                questions = ["Unable to generate questions"]
            else:
                try:
                    questions = json.loads(output_text[start:end])
                except:
                    questions = ["Error parsing questions"]

            formatted_questions = [
                {f"question_{i+1}": q} for i, q in enumerate(questions[:5])
            ]

            feedback_sections[section] = {"questions": formatted_questions}

        final_output = {
            "employee_information": {"role": role, "experience": experience},
            "feedback_sections": feedback_sections,
            "open_ended_feedback": {
                "areas_for_improvement": f"What areas should a {role} with {experience} experience focus on improving?",
                "strengths": f"What foundational strengths should a {role} at {experience} level demonstrate?",
                "suggestions_for_growth": f"What growth path would you suggest for a {role} with {experience} experience?"
            }
        }

        return jsonify(final_output)

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=True, port=port)