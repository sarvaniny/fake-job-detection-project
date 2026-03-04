from flask import Flask, render_template, request
import joblib
import re

app = Flask(__name__)

model = joblib.load("model/job_model.pkl")
vectorizer = joblib.load("model/vectorizer.pkl")


def detect_keywords(text):

    suspicious = [
        "work from home",
        "earn fast",
        "no experience required",
        "registration fee",
        "telegram",
        "urgent hiring",
        "limited seats",
        "guaranteed income",
        "weekly payment",
        "training fee",
        "verification fee"
    ]

    text = text.lower()

    detected = []

    for word in suspicious:
        if word in text:
            detected.append(word)

    return detected


def email_risk(email):

    if not email:
        return False

    risky = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]

    for r in risky:
        if r in email.lower():
            return True

    return False


def salary_risk(text):

    numbers = re.findall(r"\d+", text)

    for n in numbers:
        if int(n) > 100000:
            return True

    return False


def compute_risk(prediction, keywords, email_flag, salary_flag):

    score = 0

    if prediction == 1:
        score += 40

    score += len(keywords) * 10

    if email_flag:
        score += 20

    if salary_flag:
        score += 15

    if score > 100:
        score = 100

    return score


def generate_analysis(prediction, keywords, email_flag, salary_flag):

    insights = []

    if prediction == 1:
        insights.append(
            "The machine learning model classified this job post as potentially fraudulent based on textual patterns commonly found in scam postings."
        )

    if keywords:
        insights.append(
            f"The job description contains suspicious phrases such as: {', '.join(keywords)}."
        )

    if email_flag:
        insights.append(
            "The recruiter email uses a free domain which is often associated with fraudulent recruiters."
        )

    if salary_flag:
        insights.append(
            "The salary mentioned in the job post appears unusually high compared to typical job postings."
        )

    if not insights:
        insights.append(
            "No strong fraud indicators were detected in the job description."
        )

    return insights


@app.route("/", methods=["GET", "POST"])
def index():

    result = None

    if request.method == "POST":

        job_text = request.form.get("job_description")
        recruiter_email = request.form.get("recruiter_email")

        if job_text:

            vector = vectorizer.transform([job_text])

            prediction = model.predict(vector)[0]

            try:
                conf = abs(model.decision_function(vector)[0])
                confidence = round(min(conf * 10, 100), 2)
            except:
                confidence = 75

            label = "Fraudulent Job Post" if prediction == 1 else "Legitimate Job Post"

            keywords = detect_keywords(job_text)

            email_flag = email_risk(recruiter_email)

            salary_flag = salary_risk(job_text)

            risk_score = compute_risk(prediction, keywords, email_flag, salary_flag)

            insights = generate_analysis(prediction, keywords, email_flag, salary_flag)

            result = {
                "prediction": label,
                "confidence": confidence,
                "keywords": keywords,
                "risk_score": risk_score,
                "insights": insights
            }

    return render_template("index.html", result=result)


@app.route("/assistant")
def assistant():
    return render_template("assistant.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


if __name__ == "__main__":
    app.run(debug=True)