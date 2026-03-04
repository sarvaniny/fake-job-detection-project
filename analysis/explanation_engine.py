def generate_explanation(keywords, email_risk, salary_risk, scam_patterns):

    explanations = []

    if keywords:
        explanations.append(
            "The job description contains suspicious language often used in job scams."
        )

    if email_risk:
        explanations.append(
            "The recruiter is using a personal email domain instead of an official company domain."
        )

    if salary_risk:
        explanations.append(
            "The salary mentioned appears unusually high for typical job postings."
        )

    if scam_patterns:
        explanations.append(
            "The system detected patterns that match known job scam formats."
        )

    if not explanations:
        explanations.append(
            "No strong fraud signals were detected in this job posting."
        )

    return explanations