def detect_scam_pattern(text):

    text = text.lower()

    patterns = {

        "Registration Fee Scam": [
            "registration fee",
            "pay fee",
            "deposit",
            "training fee",
            "security deposit"
        ],

        "Work From Home Scam": [
            "work from home",
            "online job",
            "remote job"
        ],

        "Data Entry Scam": [
            "data entry",
            "typing job",
            "captcha work"
        ],

        "Telegram Recruitment Scam": [
            "telegram",
            "contact on telegram"
        ],

        "Unrealistic Salary Scam": [
            "earn 50000",
            "high income",
            "easy money",
            "weekly income"
        ]
    }

    detected_patterns = []

    for pattern, keywords in patterns.items():

        for word in keywords:

            if word in text:
                detected_patterns.append(pattern)
                break

    return detected_patterns