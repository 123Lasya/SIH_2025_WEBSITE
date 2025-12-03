import random
def predict_price(crop, date):
    base = {
        "Groundnut": 6000,
        "Soybean": 5500,
        "Sunflower": 5000,
    }
    base_price = base.get(crop, 5000)
    noise = random.randint(-200, 200)
    return base_price + noise
import random

def predict_contract_prices(crop, date):
    base_price = {
        "Groundnut": 6500,
        "Soybean": 5200,
        "Sunflower": 4800,
    }.get(crop, 5000)

    # Fake logic for now — later you replace with ML model prediction
    grade_a = base_price + random.randint(100, 200)
    grade_b = base_price + random.randint(0, 100)
    grade_c = base_price - random.randint(50, 150)

    return grade_a, grade_b, grade_c
