"""
test_triage_edge_cases module
"""


def triage_score(patient_age, heart_rate, systolic_bp, oxygen_sat, temperature_c):
    score = 0
    if heart_rate > 120 or heart_rate < 40:
        score += 2
    if systolic_bp < 90:
        score += 3
    if oxygen_sat < 92:
        score += 3
    if temperature_c > 38.5 or temperature_c < 35:
        score += 2
    if patient_age > 75:
        score += 1
    priority = "LOW"
    if score >= 6:
        priority = "CRITICAL"
    elif score >= 3:
        priority = "HIGH"
    return score, priority


test_cases = [
    (0, 0, 0, 0, 0),
    (150, 200, 0, 0, 50),
    (80, 100, 80, 90, 34),
    (20, 80, 120, 100, 37),
    (100, 130, 85, 91, 39),
]
for test_age, hr, bp, spo2, temp in test_cases:
    test_score, test_priority = triage_score(test_age, hr, bp, spo2, temp)
    print(
        f"Age: {test_age}, HR: {hr}, BP: {bp}, SPO2: {spo2}, Temp: {temp} -> Score: {test_score}, Priority: {test_priority}"
    )
