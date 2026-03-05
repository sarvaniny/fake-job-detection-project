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

KNOWN_COMPANIES = [
"amazon","google","microsoft","apple","meta","netflix","tesla","ibm"
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

        if n>3000:
            return True

    return False


def check_email(email):

    if not email:
        return False

    domain=email.split("@")[-1]

    if domain in FREE_EMAIL_DOMAINS:
        return True

    return False


def company_email_mismatch(text,email):

    if not email:
        return False

    domain=email.split("@")[-1]

    for company in KNOWN_COMPANIES:
        if company in text.lower() and company not in domain:
            return True

    return False


def detect_duplicate_email(text):

    emails=re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",text)

    if len(emails)>1:
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
    email_mismatch = company_email_mismatch(text,email)
    duplicate_email = detect_duplicate_email(text)

    language_score = min(len(keyword_hits)*15,40)
    payment_score = min(len(payment_hits)*25,60)
    urgency_score = min(len(urgency_hits)*10,30)
    remote_score = min(len(remote_hits)*10,30)
    crypto_score = min(len(crypto_hits)*25,60)

    salary_score = 15 if salary_risk else 0
    email_score = 20 if email_risk else 0
    mismatch_score = 20 if email_mismatch else 0
    duplicate_score = 10 if duplicate_email else 0

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
        + mismatch_score
        + duplicate_score
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

    # ======================
    # EMAIL ANALYSIS
    # ======================

    if email_risk:
        explanations.append(
        "Email Legitimacy Analysis: The recruiter email uses a public email provider (such as Gmail or Yahoo). "
        "Legitimate companies typically communicate using official corporate domains. "
        "Free email providers are commonly used in fraudulent recruitment schemes because they allow anonymous account creation."
        )

    if email_mismatch:
        explanations.append(
        "Company Identity Mismatch: The job description references a well-known company, "
        "but the recruiter email domain does not match the official company domain. "
        "Impersonation of well-known companies is a frequent tactic used in job scams."
        )

    if duplicate_email:
        explanations.append(
        "Recruitment Behavior Analysis: The same recruiter email address appears multiple times in the job posting. "
        "Repeated contact information may indicate mass-distributed scam postings."
        )

    # ======================
    # JOB CONTENT ANALYSIS
    # ======================

    if salary_risk:
        explanations.append(
        "Compensation Risk Analysis: The salary mentioned in the job description appears unusually high for "
        "a role that requires little or no prior experience. Scammers often advertise inflated salaries "
        "to attract a large number of applicants quickly."
        )

    if urgency_hits:
        explanations.append(
        "Recruitment Pressure Indicators: The job description contains urgency phrases such as "
        "'apply immediately' or 'limited slots'. Scammers often create artificial urgency "
        "to prevent candidates from properly verifying the job offer."
        )

    # ======================
    # SCAM PATTERN ANALYSIS
    # ======================

    if payment_hits:
        explanations.append(
        "Financial Request Detection: The job posting appears to request payment from applicants. "
        "Legitimate employers rarely require candidates to pay registration fees, training deposits, "
        "or equipment costs during recruitment."
        )

    if crypto_hits:
        explanations.append(
        "Investment Scam Pattern: The advertisement references cryptocurrency trading or investment activity. "
        "Many job scams use fake crypto trading roles to convince victims to deposit money into fraudulent platforms."
        )

    if remote_hits:
        explanations.append(
        "Remote Work Scam Pattern: The role resembles common remote job scam formats such as "
        "data entry or online work positions that promise high pay with minimal experience."
        )

    # ======================
    # MACHINE LEARNING ANALYSIS
    # ======================

    if ml_prob > 0.7:
        explanations.append(
        "Machine Learning Assessment: The job description shows strong similarity to patterns found "
        "in previously identified fraudulent job postings."
        )

    if not explanations:
        explanations.append(
        "No strong scam indicators were detected. However applicants should still independently "
        "verify the employer and avoid sharing sensitive information before confirming job legitimacy."
        )

    highlighted_text = highlight_text(
        text,
        SCAM_KEYWORDS +
        PAYMENT_PATTERNS +
        URGENCY_WORDS +
        REMOTE_SCAMS +
        CRYPTO_SCAMS
    )

    recommendations=[
    "Research the company using its official website and LinkedIn presence.",
    "Avoid sending money or cryptocurrency during recruitment.",
    "Verify recruiter email domains carefully.",
    "Search online for scam reports related to the company."
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
# COMPANY CHECKER
# ======================

def analyze_company(name, website, email):

    score = 100
    flags = []

    if email:
        domain = email.split("@")[-1]
        if domain in FREE_EMAIL_DOMAINS:
            score -= 25
            flags.append("Recruiter is using a free email domain instead of an official company email.")

    if website and name:
        if name.lower() not in website.lower():
            score -= 20
            flags.append("The website domain does not clearly match the company name.")

    suspicious_words = ["crypto","investment","guaranteed","profit"]

    text = (website or "") + (email or "")

    for word in suspicious_words:
        if word in text.lower():
            score -= 15
            if "Suspicious financial or investment related terms detected." not in flags:
                flags.append("Suspicious financial or investment related terms detected.")

    if score < 0:
        score = 0

    if score >= 85:
        level = "HIGH TRUST"
    elif score >= 60:
        level = "MODERATE TRUST"
    else:
        level = "LOW TRUST"

    return {
        "score": score,
        "level": level,
        "flags": flags if flags else ["No strong risk indicators detected."]
    }


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


@app.route("/company-checker", methods=["GET","POST"])
def company_checker():

    result=None
    name=""
    website=""
    email=""

    if request.method=="POST":

        name=request.form.get("company_name")
        website=request.form.get("company_website")
        email=request.form.get("recruiter_email")

        result=analyze_company(name,website,email)

    return render_template(
        "company_checker.html",
        result=result,
        company_name=name,
        company_website=website,
        recruiter_email=email
    )


@app.route("/scam-library")
def scam_library():
    return render_template("scam_library.html")


# ======================
# SMART ASSISTANT
# ======================

@app.route("/ask",methods=["POST"])
def ask():

    question=request.json["question"].lower()

    if "official email" in question or "company email" in question:
        return jsonify({"answer":"Yes, legitimate recruiters usually use official company email domains."})

    if "gmail" in question or "yahoo" in question:
        return jsonify({"answer":"Recruiters using free email services like Gmail or Yahoo may indicate a scam."})

    if "crypto" in question or "bitcoin" in question:
        return jsonify({"answer":"Crypto trading job offers that require deposits are a common scam tactic."})

    if "data entry" in question or "work from home" in question:
        return jsonify({"answer":"Many scams advertise simple work-from-home jobs with unrealistic salaries."})

    if "fee" in question or "pay" in question:
        return jsonify({"answer":"Legitimate employers rarely ask candidates to pay fees during recruitment."})

    return jsonify({"answer":"Common signs of job scams include payment requests, unrealistic salaries, fake recruiters, and urgency pressure."})


if __name__=="__main__":
    app.run(debug=True)