import json

def load_prices(filename):
    data = {}
    result = []

    with open(filename, "r") as f:
        data = json.load(f)
        f.close()
    for item in data:
        current_price = int(item["stck_prpr"])
        result.append(current_price)

    return result

def ma(values, window_size):
    if len(values) >= window_size:
        target_values = values[-window_size:]
        return sum(target_values) / window_size
    else:
        return None

def ma_signal(ma_short_term, ma_long_term):
    if len(ma_short_term) < 2 or len(ma_long_term) < 2:
        return None
    if None in ma_short_term[-2:] or None in ma_long_term[-2:]:
        return None
    prev = ma_short_term[-2] - ma_long_term[-2]
    current = ma_short_term[-1] - ma_long_term[-1]

    if prev < 0 and current >= 0:
        return "BUY"
    elif prev >= 0 and current < 0:
        return "SELL"
    else:
        return None

def test(prices):
    ma20 = []
    ma60 = []
    for i in range(len(prices)):
        ma20.append(ma(prices[:i + 1], 20))
        ma60.append(ma(prices[:i + 1], 60))
        signal = ma_signal(ma20, ma60)
        print(f"시그널: {signal} MA20: {ma20[-1]} MA60: {ma60[-1]}")

sample_prices = load_prices("sample.json")
test(sample_prices)

