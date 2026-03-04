from flask import Flask, render_template, request, jsonify
import re
import pickle
import os

app = Flask(__name__)

BASE_DIR = os.path.dirname(__file__)

# ======================
# LOAD ML MODEL
# ======================

model = pickle.load(open(os.path.join(BASE_DIR,"model/job_model.pkl"),"rb"))
vectorizer = pickle.load(open(os.path.join(BASE_DIR,"model/vectorizer.pkl"),"rb"))

analysis_history = []

# ======================
# CONSTANTS
# ======================

FREE_EMAIL_DOMAINS = [
"gmail.com","yahoo.com","hotmail.com","outlook.com","protonmail.com"
]

SCAM_KEYWORDS = [
"earn money fast",
"quick money",
"guaranteed income",
"guaranteed profits",
"easy money",
"no experience required",
"instant payment"
]

PAYMENT_PATTERNS = [
"registration fee",
"training fee",
"processing fee",
"security deposit",
"investment required",
"payment required",
"pay a fee"
]

URGENCY_WORDS = [
"urgent hiring",
"apply immediately",
"limited slots",
"hiring urgently",
"only today"
]

REMOTE_SCAMS = [
"data entry",
"typing job",
"work from home",
"online work"
]

CRYPTO_SCAMS = [
"crypto",
"bitcoin",
"forex",
"trading investment"
]

# ======================
# HELPER FUNCTIONS
# ======================

def ml_prediction(text):

    vec = vectorizer.transform([text])

    prediction = model.predict(vec)[0]

    try:
        prob = model.predict_proba(vec)[0][1]
    except:
        prob = 0.5

    return prediction, prob


def contains_keywords(text, keywords):

    found=[]

    for k in keywords:
        if k in text.lower():
            found.append(k)

    return found


def detect_salary(text):

    numbers=re.findall(r"\d{2,6}",text)

    for n in numbers:

        n=int(n)

        if n>200000:
            return True

    return False


def check_email(email):

    if not email:
        return False

    domain=email.split("@")[-1]

    if domain in FREE_EMAIL_DOMAINS:
        return True

    return False


def highlight_text(text, phrases):

    result=text

    for p in phrases:

        result=re.sub(
            f"({p})",
            r"<mark>\1</mark>",
            result,
            flags=re.IGNORECASE
        )

    return result


# ======================
# ANALYZER ENGINE
# ======================

def analyze_job(text,email):

    ml_label,ml_prob = ml_prediction(text)

    keyword_hits = contains_keywords(text,SCAM_KEYWORDS)
    payment_hits = contains_keywords(text,PAYMENT_PATTERNS)
    urgency_hits = contains_keywords(text,URGENCY_WORDS)
    remote_hits = contains_keywords(text,REMOTE_SCAMS)
    crypto_hits = contains_keywords(text,CRYPTO_SCAMS)

    salary_risk = detect_salary(text)
    email_risk = check_email(email)

    language_score = min(len(keyword_hits)*15,40)
    payment_score = min(len(payment_hits)*25,60)
    urgency_score = min(len(urgency_hits)*10,30)
    remote_score = min(len(remote_hits)*10,30)
    crypto_score = min(len(crypto_hits)*25,60)

    salary_score = 20 if salary_risk else 0
    email_score = 20 if email_risk else 0

    ml_score = int(ml_prob*100)

    raw_score = (
        ml_score*0.5
        + language_score
        + payment_score
        + urgency_score
        + remote_score
        + crypto_score
        + salary_score
        + email_score
    )

    total_score = min(int(raw_score),100)

    if total_score>=70:
        level="HIGH RISK"
    elif total_score>=40:
        level="MODERATE RISK"
    else:
        level="LOW RISK"

    scam_type="Legitimate Job"

    if crypto_hits:
        scam_type="Crypto Investment Scam"
    elif payment_hits:
        scam_type="Registration Fee Scam"
    elif remote_hits:
        scam_type="Work From Home Scam"

    explanations=[]

    if ml_prob>0.7:
        explanations.append("Machine learning analysis suggests the posting resembles known job scams.")

    if payment_hits:
        explanations.append("The job requires payment or registration fees which legitimate employers rarely request.")

    if keyword_hits:
        explanations.append("The description promises easy or guaranteed income which is commonly used in fraudulent advertisements.")

    if email_risk:
        explanations.append("The recruiter uses a free email domain rather than an official company email.")

    if salary_risk:
        explanations.append("The salary mentioned appears unusually high compared to typical job postings.")

    if crypto_hits:
        explanations.append("The advertisement references cryptocurrency or trading profits which frequently appear in investment scams.")

    if not explanations:
        explanations.append("No strong scam indicators were detected in this job posting.")

    highlighted_text=highlight_text(text, SCAM_KEYWORDS+PAYMENT_PATTERNS)

    recommendations=[
    "Never pay registration or training fees to apply for a job.",
    "Verify the company using its official website and LinkedIn.",
    "Search online for scam reports related to the recruiter.",
    "Avoid jobs promising guaranteed income or extremely high salaries."
    ]

    result={
    "score":total_score,
    "level":level,
    "scam_type":scam_type,
    "ml_probability":round(ml_prob*100,2),
    "language_score":language_score,
    "payment_score":payment_score,
    "urgency_score":urgency_score,
    "remote_score":remote_score,
    "crypto_score":crypto_score,
    "salary_score":salary_score,
    "email_score":email_score,
    "explanations":explanations,
    "recommendations":recommendations,
    "highlighted_text":highlighted_text
    }

    return result


# ======================
# ROUTES
# ======================

@app.route("/",methods=["GET","POST"])
def index():

    result=None
    job_text=""
    recruiter_email=""

    if request.method=="POST":

        job_text=request.form.get("job_description")
        recruiter_email=request.form.get("recruiter_email")

        result=analyze_job(job_text,recruiter_email)

        analysis_history.append(result)

    return render_template(
        "index.html",
        result=result,
        job_text=job_text,
        recruiter_email=recruiter_email
    )


@app.route("/assistant")
def assistant():
    return render_template("assistant.html")


@app.route("/dashboard")
def dashboard():

    total=len(analysis_history)

    high=sum(1 for r in analysis_history if r["level"]=="HIGH RISK")
    medium=sum(1 for r in analysis_history if r["level"]=="MODERATE RISK")
    low=sum(1 for r in analysis_history if r["level"]=="LOW RISK")

    return render_template(
        "dashboard.html",
        total=total,
        high=high,
        medium=medium,
        low=low
    )


# ======================
# SMART ASSISTANT
# ======================

@app.route("/ask",methods=["POST"])
def ask():

    question=request.json["question"].lower()

    # positive signals first

    if "company email" in question or "official email" in question:
        return jsonify({
        "answer":"Yes, that is generally a positive sign. Legitimate recruiters typically use official company email domains. However, you should still verify the company and job posting."
        })

    if "gmail" in question or "yahoo" in question:
        return jsonify({
        "answer":"Recruiters using free email services like Gmail or Yahoo may not represent a legitimate company. It is safer to verify the recruiter through the company website."
        })

    if "fee" in question or "training fee" in question or "registration fee" in question:
        return jsonify({
        "answer":"Legitimate employers almost never ask candidates to pay registration or training fees during recruitment."
        })

    if "salary" in question or "earn" in question or "income" in question:
        return jsonify({
        "answer":"Be cautious of jobs promising extremely high income with little experience. Unrealistic salaries are commonly used in job scams."
        })

    if "crypto" in question or "bitcoin" in question or "trading" in question:
        return jsonify({
        "answer":"Many scams involve cryptocurrency trading opportunities promising guaranteed profits. Always research the company before engaging."
        })

    if "remote" in question or "work from home" in question or "data entry" in question:
        return jsonify({
        "answer":"Remote jobs can be legitimate but scammers often disguise fraud as simple work-from-home or data entry jobs."
        })

    return jsonify({
    "answer":"Common signs of job scams include payment requests, unrealistic salaries, and urgent hiring pressure. Always research the company before applying."
    })


# ======================

if __name__=="__main__":
    app.run(debug=True)