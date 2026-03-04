def calculate_risk_score(prediction, keywords, email_risk, salary_risk):

    score = 0

    if prediction == 1:
        score += 40

    score += len(keywords) * 10

    if email_risk:
        score += 20

    if salary_risk:
        score += 15

    if score > 100:
        score = 100

    return score