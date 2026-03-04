def check_keywords(job_description):

    suspicious_keywords = [
        "work from home",
        "earn fast",
        "earn money quickly",
        "no experience required",
        "registration fee",
        "telegram contact",
        "urgent hiring",
        "limited seats",
        "guaranteed income",
        "weekly payment",
        "instant payout",
        "training fee"
    ]

    job_description = job_description.lower()

    detected_keywords = []

    for keyword in suspicious_keywords:
        if keyword in job_description:
            detected_keywords.append(keyword)

    return detected_keywords