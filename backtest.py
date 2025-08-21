import json
import matplotlib.pyplot as plt
import indicator
import strategy

def load_prices(filename):
    result = []
    with open(filename, "r") as f:
        data = json.load(f)
    for item in data:
        current_price = int(item["stck_prpr"])
        result.append(current_price)
    return result

def show_graph(prices, ma20, ma60, interests):
    _, ax1 = plt.subplots()
    ax1.plot(range(len(prices)), prices, label="가격", color="black")
    ax1.plot(range(len(ma20)), ma20, label="MA20", color="orange")
    ax1.plot(range(len(ma60)), ma60, label="MA60", color="yellow")
    for i in range(len(prices)):
        y = prices[i]
        signal = strategy.ma_signal(ma20[:i + 1], ma60[:i + 1])
        if signal == "BUY":
            ax1.plot(i, y, "ro")  # 빨간 점: 매수
        elif signal == "SELL":
            ax1.plot(i, y, "go")  # 초록 점: 매도

    ax1.legend(loc="upper left")

    ax2 = ax1.twinx()
    ax2.plot(range(len(interests)), interests, label="수익률", color="blue")
    ax2.legend(loc="upper right")
    plt.title("백테스트 결과")
    plt.show()

def backtest(prices, initial_balance):
    balance = initial_balance
    quantity = 0
    ma20 = []
    ma60 = []
    interests = []

    for i in range(len(prices)):
        ma20.append(indicator.ma(prices[:i + 1], 20))
        ma60.append(indicator.ma(prices[:i + 1], 60))
        signal = strategy.ma_signal(ma20, ma60)

        if signal == "BUY":
            amount = balance // prices[i]
            quantity += amount
            balance -= amount * prices[i]
        elif signal == "SELL":
            amount = quantity
            quantity -= amount
            balance += amount * prices[i]

        roi = ((balance + prices[i] * quantity) / initial_balance - 1) * 100
        interests.append(roi)
        if signal is not None:
            print(f"시그널: {signal} 수익률: {roi:.2f}%")

    show_graph(prices, ma20, ma60, interests)

# 실행
sample_prices = load_prices("sample.json")
backtest(sample_prices, 1000 * 10000)