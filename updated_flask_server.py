# updated_flask_server.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import api
from database import TradingDatabase
from datetime import datetime, timedelta
import json

app = Flask(__name__)
CORS(app)

# 데이터베이스 초기화
db = TradingDatabase("trading_data.db")

@app.route("/price")
def get_price():
    """현재가 조회"""
    code = request.args.get("code")
    token = request.args.get("token")
    
    if not code or not token:
        return jsonify({"error": "Missing parameters"}), 400

    api.ACCESS_TOKEN = token
    price = api.fetch_current_price(code)
    
    if price is not None:
        # 데이터베이스에 가격 저장
        db.save_price_data(code, price)
        db.log_info(f"가격 조회: {code} - {price:,}원")
        
        return jsonify({"price": price})
    else:
        db.log_error(f"가격 조회 실패: {code}")
        return jsonify({"error": "가격 조회 실패"}), 500

@app.route("/order", methods=["POST"])
def make_order():
    """주문 실행"""
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
    
    # 데이터베이스에 주문 기록 (PENDING 상태)
    order_id = db.save_order(code, order_type, amount, price, "PENDING")
    
    try:
        success = api.order(order_type, account, code, amount, price)
        
        if success:
            # 성공시 상태 업데이트
            db.update_order_status(order_id, "SUCCESS")
            db.log_info(f"주문 성공: {order_type} {code} {amount}주 @ {price:,}원")
            
            return jsonify({"success": True, "order_id": order_id})
        else:
            # 실패시 상태 업데이트
            db.update_order_status(order_id, "FAILED", "API 주문 실행 실패")
            db.log_error(f"주문 실패: {order_type} {code} {amount}주 @ {price:,}원")
            
            return jsonify({"success": False, "order_id": order_id})
            
    except Exception as e:
        # 예외 발생시 상태 업데이트
        db.update_order_status(order_id, "FAILED", str(e))
        db.log_error(f"주문 예외: {e}")
        
        return jsonify({"success": False, "error": str(e), "order_id": order_id}), 500

@app.route("/fetch_quantity")
def fetch_quantity():
    """보유 수량 조회"""
    account = request.args.get("account")
    code = request.args.get("code")
    token = request.args.get("token")
    
    if not all([account, code, token]):
        return jsonify({"error": "Missing parameters"}), 400

    api.ACCESS_TOKEN = token
    
    try:
        quantity = api.fetch_quantity(account, code)
        
        # 데이터베이스에 계좌 상태 저장
        total_eval = api.fetch_eval(account)
        if total_eval:
            db.save_account_status(account, code, int(quantity), int(total_eval))
        
        db.log_info(f"보유 수량 조회: {code} - {quantity}주")
        
        return jsonify({"quantity": int(quantity)})
        
    except Exception as e:
        db.log_error(f"보유 수량 조회 실패: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/clear_orders", methods=["POST"])
def clear_orders():
    """미체결 주문 정리"""
    data = request.get_json()
    account = data.get("account")
    code = data.get("code")
    token = data.get("token")

    if not all([account, code, token]):
        return jsonify({"error": "누락된 요청 데이터"}), 400

    api.ACCESS_TOKEN = token
    
    try:
        api.clear_orders(account, code)
        db.log_info(f"미체결 주문 정리: {code}")
        
        return jsonify({"message": "미체결 주문 정리 완료"})
        
    except Exception as e:
        db.log_error(f"미체결 주문 정리 실패: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/fetch_eval")
def fetch_eval():
    """총 평가금 조회"""
    account = request.args.get("account")
    token = request.args.get("token")
    
    if not all([account, token]):
        return jsonify({"error": "Missing parameters"}), 400

    api.ACCESS_TOKEN = token
    
    try:
        evaluation = api.fetch_eval(account)
        
        if evaluation:
            evaluation = int(evaluation)
            db.log_info(f"총 평가금 조회: {evaluation:,}원")
            return jsonify({"evaluation": evaluation})
        else:
            return jsonify({"evaluation": 0})
            
    except Exception as e:
        db.log_error(f"총 평가금 조회 실패: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/price_history")
def get_price_history():
    """가격 히스토리 조회"""
    code = request.args.get("code")
    limit = request.args.get("limit", 100)
    
    if not code:
        return jsonify({"error": "Missing code parameter"}), 400
    
    try:
        history = db.get_price_history(code, int(limit))
        return jsonify({"history": history})
        
    except Exception as e:
        db.log_error(f"가격 히스토리 조회 실패: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/moving_averages")
def get_moving_averages():
    """이동평균 데이터 조회"""
    code = request.args.get("code")
    count = request.args.get("count", 10)
    
    if not code:
        return jsonify({"error": "Missing code parameter"}), 400
    
    try:
        ma_data = db.get_latest_moving_averages(code, int(count))
        return jsonify({"moving_averages": ma_data})
        
    except Exception as e:
        db.log_error(f"이동평균 데이터 조회 실패: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/orders")
def get_orders():
    """주문 내역 조회"""
    code = request.args.get("code")
    limit = request.args.get("limit", 50)
    
    try:
        orders = db.get_orders(code, int(limit))
        return jsonify({"orders": orders})
        
    except Exception as e:
        db.log_error(f"주문 내역 조회 실패: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/statistics")
def get_statistics():
    """통계 조회"""
    code = request.args.get("code")
    days = request.args.get("days", 7)
    
    if not code:
        return jsonify({"error": "Missing code parameter"}), 400
    
    try:
        stats = db.get_statistics(code, int(days))
        return jsonify({"statistics": stats})
        
    except Exception as e:
        db.log_error(f"통계 조회 실패: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/logs")
def get_logs():
    """로그 조회"""
    level = request.args.get("level")  # INFO, WARNING, ERROR
    limit = request.args.get("limit", 100)
    
    try:
        logs = db.get_logs(level, int(limit))
        return jsonify({"logs": logs})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/trading_settings", methods=["GET", "POST"])
def trading_settings():
    """자동매매 설정 조회/저장"""
    code = request.args.get("code") or request.json.get("code") if request.json else None
    
    if not code:
        return jsonify({"error": "Missing code parameter"}), 400
    
    if request.method == "GET":
        # 설정 조회
        try:
            settings = db.get_trading_settings(code)
            return jsonify({"settings": settings})
            
        except Exception as e:
            db.log_error(f"자동매매 설정 조회 실패: {e}")
            return jsonify({"error": str(e)}), 500
    
    else:  # POST
        # 설정 저장
        data = request.get_json()
        
        try:
            is_active = data.get("is_active", False)
            ma_short = data.get("ma_short_period", 20)
            ma_long = data.get("ma_long_period", 60)
            max_buy = data.get("max_buy_amount", 1000000)
            additional = data.get("additional_settings", {})
            
            success = db.save_trading_settings(
                code, is_active, ma_short, ma_long, max_buy, additional
            )
            
            if success:
                db.log_info(f"자동매매 설정 저장: {code}")
                return jsonify({"success": True})
            else:
                return jsonify({"success": False}), 500
                
        except Exception as e:
            db.log_error(f"자동매매 설정 저장 실패: {e}")
            return jsonify({"error": str(e)}), 500

@app.route("/dashboard")
def get_dashboard():
    """대시보드 데이터 조회"""
    code = request.args.get("code")
    
    if not code:
        return jsonify({"error": "Missing code parameter"}), 400
    
    try:
        # 현재가
        current_price = None
        recent_prices = db.get_recent_prices(code, 1)
        if recent_prices:
            current_price = recent_prices[0]
        
        # 최근 이동평균
        ma_data = db.get_latest_moving_averages(code, 1)
        ma20 = ma_data[0]['ma20'] if ma_data else None
        ma60 = ma_data[0]['ma60'] if ma_data else None
        
        # 오늘의 통계
        today_stats = db.get_statistics(code, 1)
        
        # 최근 주문
        recent_orders = db.get_orders(code, 5)
        
        # 최근 로그
        recent_logs = db.get_logs(limit=10)
        
        dashboard_data = {
            "current_price": current_price,
            "ma20": ma20,
            "ma60": ma60,
            "today_stats": today_stats,
            "recent_orders": recent_orders,
            "recent_logs": recent_logs
        }
        
        return jsonify({"dashboard": dashboard_data})
        
    except Exception as e:
        db.log_error(f"대시보드 데이터 조회 실패: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/backup", methods=["POST"])
def backup_database():
    """데이터베이스 백업"""
    try:
        backup_path = db.backup_database()
        
        if backup_path:
            db.log_info(f"데이터베이스 백업 생성: {backup_path}")
            return jsonify({"success": True, "backup_path": backup_path})
        else:
            return jsonify({"success": False}), 500
            
    except Exception as e:
        db.log_error(f"데이터베이스 백업 실패: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/cleanup", methods=["POST"])
def cleanup_old_data():
    """오래된 데이터 정리"""
    data = request.get_json()
    days_to_keep = data.get("days_to_keep", 90)
    
    try:
        success = db.cleanup_old_data(days_to_keep)
        
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False}), 500
            
    except Exception as e:
        db.log_error(f"데이터 정리 실패: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/status")
def get_status():
    """서버 상태 조회"""
    try:
        # 데이터베이스 연결 확인
        test_logs = db.get_logs(limit=1)
        
        # 최근 활동 시간
        recent_activity = None
        if test_logs:
            recent_activity = test_logs[0]['timestamp']
        
        status_data = {
            "server_time": datetime.now().isoformat(),
            "database_connected": True,
            "recent_activity": recent_activity,
            "version": "1.0.0"
        }
        
        return jsonify({"status": status_data})
        
    except Exception as e:
        return jsonify({
            "status": {
                "server_time": datetime.now().isoformat(),
                "database_connected": False,
                "error": str(e),
                "version": "1.0.0"
            }
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    db.log_error(f"서버 내부 오류: {error}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    # 서버 시작 로그
    db.log_info("Flask 서버 시작")
    print("🚀 자동매매 API 서버 시작")
    print("📍 http://localhost:5000")
    print("📊 사용 가능한 엔드포인트:")
    print("  - GET /price - 현재가 조회")
    print("  - POST /order - 주문 실행")
    print("  - GET /orders - 주문 내역 조회")
    print("  - GET /statistics - 통계 조회")
    print("  - GET /dashboard - 대시보드 데이터")
    print("  - GET /logs - 로그 조회")
    print("  - GET /status - 서버 상태")
    
    try:
        app.run(host="0.0.0.0", port=5000, debug=False)
    except KeyboardInterrupt:
        db.log_info("Flask 서버 종료")
        print("\n👋 서버 종료")
    except Exception as e:
        db.log_error(f"서버 실행 오류: {e}")
        print(f"💥 서버 오류: {e}")
    finally:
        db.close()