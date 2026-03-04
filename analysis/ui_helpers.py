def get_signal_labels(keywords, email_risk, salary_risk, patterns):

    signals = []

    if keywords:
        signals.append("Suspicious Language")

    if email_risk:
        signals.append("Personal Email Recruiter")

    if salary_risk:
        signals.append("Unrealistic Salary")

    for p in patterns:
        signals.append(p)

    return signals