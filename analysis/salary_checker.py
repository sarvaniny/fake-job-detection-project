import re

def check_salary(job_description):

    job_description = job_description.lower()

    pattern = r"\d{4,}"

    numbers = re.findall(pattern, job_description)

    for num in numbers:
        value = int(num)

        if value > 100000:
            return True

    return False