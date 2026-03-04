def explain_prediction(job_description, keywords, email_risk, salary_risk):

    reasons = []

    if keywords:
        reasons.append(
            "The job description contains suspicious recruitment phrases often used in online job scams."
        )

    if email_risk:
        reasons.append(
            "The recruiter is using a non-corporate email address which is commonly associated with fraudulent job postings."
        )

    if salary_risk:
        reasons.append(
            "The job advertisement mentions unusually high salary figures which are unrealistic for typical job roles."
        )

    if not reasons:
        return "The job description does not contain strong indicators of fraud based on the analyzed patterns."

    return " ".join(reasons)