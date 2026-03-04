def check_email(email):

    if not email:
        return False

    suspicious_domains = [
        "gmail.com",
        "yahoo.com",
        "hotmail.com",
        "outlook.com",
        "protonmail.com"
    ]

    email = email.lower()

    for domain in suspicious_domains:
        if domain in email:
            return True

    return False