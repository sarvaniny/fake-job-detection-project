from flask import Flask, render_template, request, jsonify
import re
import pickle
import os
import json

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
"registration charge",
"registration cost",
"payment required",
"verification fee",
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

# NEW DETECTION LISTS

SUSPICIOUS_TLDS = [
".xyz",".top",".online",".site",".store",".buzz",".live"
]

ADVANCED_SCAM_PHRASES = [
"earn per day",
"earn per week",
"instant withdrawal",
"limited time opportunity",
"double your income",
"no interview required"
]
SUSPICIOUS_DOMAIN_KEYWORDS = [
"jobs",
"career",
"hiring",
"apply",
"opportunity",
"income",
"earn",
"remote",
"work"
]
SALARY_HIGHLIGHT_PATTERNS = [
r"\$\d+\s*per\s*day",
r"\$\d+\s*per\s*week",
r"\$\d+\s*per\s*month",
r"₹\d+\s*per\s*day",
r"₹\d+\s*per\s*week",
r"\d+\s*per\s*day",
r"\d+\s*per\s*week"
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


def advanced_salary_detection(text):

    patterns=[
    r"\$\d+\s*per\s*day",
    r"\d+\s*per\s*day",
    r"\d+\s*per\s*week",
    r"earn\s*\$\d+",
    r"earn\s*\d+\s*daily"
    ]

    for p in patterns:
        if re.search(p,text.lower()):
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


def suspicious_domain_pattern(email):

    if not email:
        return False

    domain=email.split("@")[-1]

    if any(char.isdigit() for char in domain):
        return True

    return False


def suspicious_tld(email):

    if not email:
        return False

    domain=email.split("@")[-1]

    for t in SUSPICIOUS_TLDS:
        if domain.endswith(t):
            return True

    return False


def lookalike_company_domain(text,email):

    if not email:
        return False

    domain=email.split("@")[-1]

    for company in KNOWN_COMPANIES:

        altered=company.replace("o","0").replace("l","1")

        if altered in domain:
            return True

    return False


# ======================
# SCAM DATABASE FUNCTIONS
# ======================

def extract_company_name(text):

    for company in KNOWN_COMPANIES:
        if company in text.lower():
            return company

    return "Unknown"


def check_scam_database(text,email):

    try:

        path=os.path.join(BASE_DIR,"data","scam_reports.json")

        if not os.path.exists(path):
            return False

        with open(path) as f:
            reports=json.load(f)

        for r in reports:

            if r["company"].lower() in text.lower():
                return True

            if email and r["email"].lower()==email.lower():
                return True

    except:
        return False

    return False


def save_scam_report(text,email,score,scam_type):

    try:

        path=os.path.join(BASE_DIR,"data","scam_reports.json")

        if not os.path.exists(path):
            with open(path,"w") as f:
                json.dump([],f)

        with open(path,"r") as f:
            reports=json.load(f)

        for r in reports:
            if email and r.get("email")==email:
                return

        report={
    "company":extract_company_name(text),
    "email":email,
    "website":"",
    "type":scam_type,
    "score":score,
    "date":str(__import__("datetime").datetime.now())
}

        reports.append(report)

        with open(path,"w") as f:
            json.dump(reports,f,indent=4)

    except:
        pass


def highlight_text(text, phrases):

    result=text

    # highlight phrase matches
    for p in phrases:

        result=re.sub(
            f"({p})",
            r"<mark>\1</mark>",
            result,
            flags=re.IGNORECASE
        )

    # highlight salary patterns
    for pattern in SALARY_HIGHLIGHT_PATTERNS:

        result=re.sub(
            pattern,
            lambda m: f"<mark>{m.group()}</mark>",
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
    advanced_phrase_hits = contains_keywords(text,ADVANCED_SCAM_PHRASES)

    salary_risk = detect_salary(text) or advanced_salary_detection(text)

    email_risk = check_email(email)
    email_mismatch = company_email_mismatch(text,email)
    duplicate_email = detect_duplicate_email(text)

    domain_pattern_risk = suspicious_domain_pattern(email)
    tld_risk = suspicious_tld(email)
    lookalike_domain = lookalike_company_domain(text,email)

    scam_db_hit = check_scam_database(text,email)

    language_score = min(len(keyword_hits)*15,40)
    payment_score = min(len(payment_hits)*25,60)
    urgency_score = min(len(urgency_hits)*10,30)
    remote_score = min(len(remote_hits)*10,30)
    crypto_score = min(len(crypto_hits)*25,60)
    advanced_phrase_score = min(len(advanced_phrase_hits)*15,30)

    salary_score = 15 if salary_risk else 0
    email_score = 20 if email_risk else 0
    mismatch_score = 20 if email_mismatch else 0
    duplicate_score = 10 if duplicate_email else 0
    domain_pattern_score = 15 if domain_pattern_risk else 0
    tld_score = 10 if tld_risk else 0
    lookalike_score = 25 if lookalike_domain else 0
    scam_db_score = 40 if scam_db_hit else 0

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
        + domain_pattern_score
        + tld_score
        + lookalike_score
        + scam_db_score
        + advanced_phrase_score
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

    # AUTO SAVE SCAM REPORT
    if total_score >= 70:
        save_scam_report(text,email,total_score,scam_type)

    explanations=[]

    if email_risk:
        explanations.append("Email Legitimacy Analysis: The recruiter email uses a public email provider which is commonly used in scam postings.")

    if email_mismatch:
        explanations.append("Company Identity Mismatch: The recruiter email domain does not match the company mentioned in the job post.")

    if duplicate_email:
        explanations.append("Recruitment Behavior Analysis: Multiple recruiter emails detected in the job description.")

    if salary_risk:
        explanations.append("Compensation Risk Analysis: The salary mentioned appears unusually high for the described role.")

    if urgency_hits:
        explanations.append("Recruitment Pressure Indicators: Urgency phrases were detected encouraging immediate application.")

    if payment_hits:
        explanations.append("Financial Request Detection: The job description requests payment from applicants.")

    if crypto_hits:
        explanations.append("Investment Scam Pattern: The posting references cryptocurrency trading or investment.")

    if remote_hits:
        explanations.append("Remote Work Scam Pattern: The job resembles common remote scam formats like data entry jobs.")

    if domain_pattern_risk:
        explanations.append("Domain Structure Warning: The recruiter domain contains suspicious patterns such as numbers.")

    if tld_risk:
        explanations.append("Domain Reputation Warning: The email domain uses a high-risk top-level domain.")

    if lookalike_domain:
        explanations.append("Brand Impersonation Detection: The recruiter domain appears to imitate a known company name.")

    if scam_db_hit:
        explanations.append("Scam Database Match: This company or email appears in previously reported scam records.")

    if advanced_phrase_hits:
        explanations.append("High Profit Language Detection: The job description contains phrases commonly used in scams promising easy money.")

    if ml_prob > 0.7:
        explanations.append("Machine Learning Assessment: The text closely resembles known fraudulent job postings.")

    if not explanations:
        explanations.append("No strong scam indicators detected but applicants should still verify the employer.")

    highlighted_text = highlight_text(
        text,
        SCAM_KEYWORDS +
        PAYMENT_PATTERNS +
        URGENCY_WORDS +
        REMOTE_SCAMS +
        CRYPTO_SCAMS +
        ADVANCED_SCAM_PHRASES
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

    domain = ""
    if email:
        domain = email.split("@")[-1]

    # FREE EMAIL PROVIDERS
    if domain in FREE_EMAIL_DOMAINS:
        score -= 25
        flags.append("Recruiter is using a free email provider instead of an official company domain.")

    # DOMAIN CONTAINS NUMBERS (SUSPICIOUS)
    if domain and any(char.isdigit() for char in domain):
        score -= 15
        flags.append("Recruiter email domain contains unusual numeric patterns which may indicate impersonation.")

    # SUSPICIOUS TLD CHECK
    for tld in SUSPICIOUS_TLDS:
        if domain.endswith(tld):
            score -= 15
            flags.append("The email domain uses a high-risk top-level domain often associated with scams.")
            break

    # DOMAIN-COMPANY SIMILARITY CHECK
    if name and domain:
        company = name.lower().replace(" ", "")
        if company not in domain:
            score -= 20
            flags.append("The recruiter email domain does not appear to match the company name.")
    
    # WEBSITE TLD CHECK
    if website:
        for tld in SUSPICIOUS_TLDS:
            if website.endswith(tld):
                score -= 10
                flags.append("The company website uses a suspicious domain extension.")
                break
                # DOMAIN AGE RISK SIMULATION
    if website:
        w = website.lower()

        for keyword in SUSPICIOUS_DOMAIN_KEYWORDS:
            if keyword in w:
                score -= 10
                flags.append("The website domain structure resembles newly registered job recruitment domains often used in scams.")
                break       

    # SCAM DATABASE CROSS-CHECK
    try:
        path = os.path.join(BASE_DIR,"data","scam_reports.json")

        if os.path.exists(path):

            with open(path) as f:
                reports = json.load(f)

            for r in reports:

                if name and r["company"].lower() in name.lower():
                    score -= 30
                    flags.append("This company appears in previously reported scam records.")
                    break

                if email and r["email"].lower() == email.lower():
                    score -= 30
                    flags.append("This recruiter email has been reported in scam records.")
                    break
    except:
        pass

    # LIMIT SCORE
    if score < 0:
        score = 0

    # TRUST LEVEL
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

    # scam type distribution
    scam_types={}

    for r in analysis_history:

        t=r["scam_type"]

        scam_types[t]=scam_types.get(t,0)+1


    # recent analyses (last 5)
    recent_analyses=analysis_history[-5:][::-1]


    # analyzer usage statistics
    avg_risk=0
    if total>0:
        avg_risk=sum(r["score"] for r in analysis_history)/total
        avg_risk=round(avg_risk,2)


    # scam reports count
    report_count=0

    path=os.path.join(BASE_DIR,"data","scam_reports.json")

    if os.path.exists(path):

        with open(path) as f:

            reports=json.load(f)

            report_count=len(reports)


    return render_template(
        "dashboard.html",
        total=total,
        high=high,
        medium=medium,
        low=low,
        scam_types=scam_types,
        report_count=report_count,
        recent_analyses=recent_analyses,
        avg_risk=avg_risk
    )

    total=len(analysis_history)

    high=sum(1 for r in analysis_history if r["level"]=="HIGH RISK")
    medium=sum(1 for r in analysis_history if r["level"]=="MODERATE RISK")
    low=sum(1 for r in analysis_history if r["level"]=="LOW RISK")

    # scam type distribution
    scam_types={}

    for r in analysis_history:

        t=r["scam_type"]

        scam_types[t]=scam_types.get(t,0)+1

    # scam reports count
    report_count=0

    path=os.path.join(BASE_DIR,"data","scam_reports.json")

    if os.path.exists(path):

        with open(path) as f:

            reports=json.load(f)

            report_count=len(reports)

    return render_template(
        "dashboard.html",
        total=total,
        high=high,
        medium=medium,
        low=low,
        scam_types=scam_types,
        report_count=report_count
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
@app.route("/report-scam",methods=["GET","POST"])
def report_scam():

    success=False

    if request.method=="POST":

        company=request.form.get("company")
        email=request.form.get("email")
        website=request.form.get("website")
        scam_type=request.form.get("scam_type")

        path=os.path.join(BASE_DIR,"data","scam_reports.json")

        if not os.path.exists(path):
            with open(path,"w") as f:
                json.dump([],f)

        with open(path,"r") as f:
            reports=json.load(f)

        report={
        "company":company,
        "email":email,
        "website":website,
        "type":scam_type,
        "date":str(__import__("datetime").datetime.now())
        }

        reports.append(report)

        with open(path,"w") as f:
            json.dump(reports,f,indent=4)

        success=True

    return render_template("report_scam.html",success=success)

# ======================
# SMART ASSISTANT
# ======================

@app.route("/ask",methods=["POST"])
def ask():

    question=request.json["question"]
    q=question.lower()

    # =====================
    # JOB ANALYSIS VIA CHAT
    # =====================

    if len(q) > 120:

        result = analyze_job(question,None)

        reply = f"""
Job Risk Analysis:

Risk Level: {result['level']}
Risk Score: {result['score']}%

Scam Type: {result['scam_type']}

Key Reasons:
"""

        for e in result["explanations"][:3]:
            reply += f"\n• {e}"

        reply += "\n\nRecommendation: Always verify the company website and never pay recruitment fees."

        return jsonify({"answer":reply})


    # =====================
    # SAFETY CHECKLIST
    # =====================

    if "verify" in q or "check recruiter" in q or "is this job real" in q:

        checklist = """
Job Scam Safety Checklist:

✔ Check the company website domain  
✔ Verify recruiter email domain  
✔ Search company name + scam online  
✔ Never pay registration or training fees  
✔ Avoid crypto payments for jobs  
✔ Be cautious of high salary offers for simple work
"""

        return jsonify({"answer":checklist})


    # =====================
    # EMAIL QUESTIONS
    # =====================

    if "official email" in q or "company email" in q:

        return jsonify({"answer":
        "Legitimate recruiters usually use official company domains (example: hr@company.com). "
        "Emails from Gmail, Yahoo, or Outlook can be suspicious if claiming to represent a company."})


    if "gmail" in q or "yahoo" in q:

        return jsonify({"answer":
        "Recruiters using free email services like Gmail or Yahoo are sometimes legitimate, "
        "but many job scams use them because they are easy to create anonymously."})


    # =====================
    # COMMON SCAM TYPES
    # =====================

    if "crypto" in q or "bitcoin" in q:

        return jsonify({"answer":
        "Crypto job scams usually ask victims to deposit cryptocurrency to 'activate accounts' "
        "or perform fake trading tasks. Legitimate employers never require crypto payments."})


    if "data entry" in q or "work from home" in q:

        return jsonify({"answer":
        "Many scams advertise simple work-from-home data entry jobs with unrealistic salaries. "
        "They often request training fees or security deposits."})


    if "fee" in q or "pay" in q:

        return jsonify({"answer":
        "Legitimate employers rarely ask candidates to pay fees during recruitment. "
        "Registration fees, training fees, or deposits are major scam indicators."})


    # =====================
    # DEFAULT RESPONSE
    # =====================

    return jsonify({"answer":
    "Common signs of job scams include payment requests, unrealistic salaries, fake recruiter emails, "
    "and urgency pressure. You can also paste a job description here and I will analyze it."})


if __name__=="__main__":
    app.run(debug=True)