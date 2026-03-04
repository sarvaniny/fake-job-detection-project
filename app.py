from flask import Flask, render_template, request, jsonify
import re

app = Flask(__name__)

analysis_history = []

FREE_EMAIL_DOMAINS = [
"gmail.com","yahoo.com","hotmail.com","outlook.com","protonmail.com"
]

SCAM_LANGUAGE = [
"earn money fast",
"quick money",
"guaranteed income",
"guaranteed profits",
"passive income",
"no experience required"
]

PAYMENT_PATTERNS = [
r"registration fee",
r"processing fee",
r"training fee",
r"security deposit",
r"deposit",
r"investment required",
r"pay.*fee"
]

URGENCY_PATTERNS = [
r"apply immediately",
r"urgent hiring",
r"limited slots",
r"only today",
r"limited time"
]

REMOTE_PATTERNS = [
r"data entry",
r"typing job",
r"work from home"
]

CRYPTO_PATTERNS = [
r"crypto",
r"bitcoin",
r"trading investment",
r"automated trading"
]


def detect_patterns(text, patterns):
    matches=[]
    for p in patterns:
        if re.search(p,text.lower()):
            matches.append(p)
    return matches


def detect_keywords(text):
    found=[]
    for k in SCAM_LANGUAGE:
        if k in text.lower():
            found.append(k)
    return found


def check_email(email):
    if not email:
        return False
    domain=email.split("@")[-1]
    return domain in FREE_EMAIL_DOMAINS


def detect_unrealistic_salary(text):

    nums=re.findall(r"\d+",text)

    for n in nums:
        if int(n)>50000:
            return True

    return False


def highlight_phrases(text,phrases):

    highlighted=text

    for p in phrases:
        highlighted=re.sub(
            f"({p})",
            r"<mark>\1</mark>",
            highlighted,
            flags=re.IGNORECASE
        )

    return highlighted


def analyze_job(text,email):

    keyword_hits=detect_keywords(text)
    payment_hits=detect_patterns(text,PAYMENT_PATTERNS)
    urgency_hits=detect_patterns(text,URGENCY_PATTERNS)
    remote_hits=detect_patterns(text,REMOTE_PATTERNS)
    crypto_hits=detect_patterns(text,CRYPTO_PATTERNS)

    email_risk=check_email(email)
    salary_risk=detect_unrealistic_salary(text)

    language_score=min(len(keyword_hits)*20,100)
    payment_score=min(len(payment_hits)*40,100)
    urgency_score=min(len(urgency_hits)*20,100)
    remote_score=min(len(remote_hits)*20,100)
    crypto_score=min(len(crypto_hits)*30,100)
    email_score=40 if email_risk else 0
    salary_score=40 if salary_risk else 0

    total_score=min(
        language_score+
        payment_score+
        urgency_score+
        remote_score+
        crypto_score+
        email_score+
        salary_score,
        100
    )

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

    if crypto_hits:
        explanations.append("Crypto investment programs are frequently used in online job scams.")

    if payment_hits:
        explanations.append("The job requires deposits or registration fees which legitimate employers rarely request.")

    if keyword_hits:
        explanations.append("The advertisement contains language promising easy income.")

    if email_risk:
        explanations.append("The recruiter is using a free email provider instead of a corporate domain.")

    if salary_risk:
        explanations.append("The salary or profit claims appear unusually high.")

    if not explanations:
        explanations.append("No strong scam indicators were detected.")

    highlighted_text=highlight_phrases(
        text,
        SCAM_LANGUAGE+["registration fee","crypto","guaranteed profits"]
    )

    recommendations=[
    "Never pay registration or training fees to recruiters.",
    "Verify company websites and LinkedIn pages.",
    "Avoid guaranteed profit or unrealistic salary claims."
    ]

    return{
        "score":total_score,
        "level":level,
        "scam_type":scam_type,
        "explanations":explanations,
        "highlighted_text":highlighted_text,
        "recommendations":recommendations,

        "language_score":language_score,
        "payment_score":payment_score,
        "urgency_score":urgency_score,
        "remote_score":remote_score,
        "email_score":email_score,
        "salary_score":salary_score
    }


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


@app.route("/ask",methods=["POST"])
def ask():

    q=request.json["question"].lower()

    knowledge={

    "registration fee":"Legitimate employers almost never charge candidates fees during hiring.",
    "training fee":"Training fee requests are a common scam tactic.",
    "data entry":"Many data entry work-from-home jobs are scams.",
    "work from home":"Always verify remote jobs carefully before applying.",
    "gmail recruiter":"Recruiters using Gmail instead of company domains may be suspicious.",
    "telegram":"Scammers often move conversations to Telegram to avoid monitoring.",
    "crypto job":"Crypto investment job offers promising guaranteed profit are usually scams.",
    "easy money":"Easy money promises are strong scam indicators.",
    "high salary":"Extremely high salary offers should be verified carefully."
    }

    for k in knowledge:
        if k in q:
            return jsonify({"answer":knowledge[k]})

    return jsonify({
    "answer":"Be cautious of jobs promising high income, requesting payment, or pressuring you to act quickly."
    })


if __name__=="__main__":
    app.run(debug=True)