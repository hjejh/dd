# flask_server.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import api

app = Flask(__name__)
CORS(app)

@app.route("/price")
def get_price():
    code = request.args.get("code")
    token = request.args.get("token")
    if not code or not token:
        return jsonify({"error": "Missing parameters"}), 400

    api.ACCESS_TOKEN = token
    price = api.fetch_current_price(code)
    if price is not None:
        return jsonify({"price": price})
    else:
        return jsonify({"error": "가격 조회 실패"}), 500

@app.route("/order", methods=["POST"])
def make_order():
    data = request.get_json()
    order_type = data.get("type")
    account = data.get("account")
    code = data.get("code")
    amount = data.get("amount")
    price = data.get("price")
    token = data.get("token")

    if not all([order_type, account, code, amount, price, token]):
        return jsonify({"error": "누락된 요청 데이터"}), 400

    api.ACCESS_TOKEN = token
    success = api.order(order_type, account, code, amount, price)
    return jsonify({"success": success})

@app.route("/fetch_quantity")
def fetch_quantity():
    account = request.args.get("account")
    code = request.args.get("code")
    token = request.args.get("token")
    if not all([account, code, token]):
        return jsonify({"error": "Missing parameters"}), 400

    api.ACCESS_TOKEN = token
    quantity = api.fetch_quantity(account, code)
    return jsonify({"quantity": quantity})

@app.route("/clear_orders", methods=["POST"])
def clear_orders():
    data = request.get_json()
    account = data.get("account")
    code = data.get("code")
    token = data.get("token")

    if not all([account, code, token]):
        return jsonify({"error": "누락된 요청 데이터"}), 400

    api.ACCESS_TOKEN = token
    api.clear_orders(account, code)
    return jsonify({"message": "미체결 주문 정리 완료"})

@app.route("/fetch_eval")
def fetch_eval():
    account = request.args.get("account")
    token = request.args.get("token")
    if not all([account, token]):
        return jsonify({"error": "Missing parameters"}), 400

    api.ACCESS_TOKEN = token
    evaluation = api.fetch_eval(account)
    return jsonify({"evaluation": evaluation})

if __name__ == "__main__":
    app.run(port=5000)
