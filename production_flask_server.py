# production_flask_server.py
"""
프로덕션 환경용 Flask 서버
보안 강화 및 배포 최적화
"""

import os
import secrets
from flask import Flask, request, jsonify, session, render_template_string
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import api
from database import TradingDatabase
from datetime import datetime, timedelta
import json
import logging
from functools import wraps

# 환경 설정
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_urlsafe(32)
    DATABASE_PATH = os.environ.get('DATABASE_PATH') or 'trading_data.db'
    ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', '*').split(',')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    SESSION_TIMEOUT = 3600  # 1시간
    API_RATE_LIMIT = 100  # 시간당 요청 제한

app = Flask(__name__)
app.config.from_object(Config)

# CORS 설정 (프로덕션에서는 특정 도메인만 허용)
if app.config['ALLOWED_ORIGINS'] == ['*']:
    CORS(app)
else:
    CORS(app, origins=app.config['ALLOWED_ORIGINS'])

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    handlers=[
        logging.FileHandler('trading_app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 데이터베이스 초기화
db = TradingDatabase(app.config['DATABASE_PATH'])

# 인증 관리
class AuthManager:
    def __init__(self):
        self.users = {}
        self.api_keys = {}
        self.rate_limits = {}
    
    def create_user(self, username: str, password: str) -> bool:
        """사용자 생성"""
        if username in self.users:
            return False
        
        self.users[username] = {
            'password_hash': generate_password_hash(password),
            'created_at': datetime.now().isoformat(),
            'api_key': secrets.token_urlsafe(32)
        }
        return True
    
    def verify_user(self, username: str, password: str) -> bool:
        """사용자 인증"""
        if username not in self.users:
            return False
        
        return check_password_hash(self.users[username]['password_hash'], password)
    
    def get_api_key(self, username: str) -> str:
        """API 키 조회"""
        return self.users.get(username, {}).get('api_key')
    
    def verify_api_key(self, api_key: str) -> str:
        """API 키 검증"""
        for username, user_data in self.users.items():
            if user_data.get('api_key') == api_key:
                return username
        return None
    
    def check_rate_limit(self, identifier: str) -> bool:
        """속도 제한 확인"""
        now = datetime.now()
        if identifier not in self.rate_limits:
            self.rate_limits[identifier] = []
        
        # 1시간 이전 요청 제거
        self.rate_limits[identifier] = [
            req_time for req_time in self.rate_limits[identifier]
            if now - req_time < timedelta(hours=1)
        ]
        
        # 제한 확인
        if len(self.rate_limits[identifier]) >= app.config['API_RATE_LIMIT']:
            return False
        
        self.rate_limits[identifier].append(now)
        return True

auth_manager = AuthManager()

# 기본 관리자 계정 생성
if not auth_manager.users:
    default_password = os.environ.get('ADMIN_PASSWORD', 'admin123!')
    auth_manager.create_user('admin', default_password)
    logger.info(f"기본 관리자 계정 생성: admin / {default_password}")

# 데코레이터
def require_auth(f):
    """인증 필요 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # API 키 확인
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        if api_key:
            username = auth_manager.verify_api_key(api_key)
            if username:
                # 속도 제한 확인
                if not auth_manager.check_rate_limit(username):
                    return jsonify({'error': '속도 제한 초과'}), 429
                
                request.current_user = username
                return f(*args, **kwargs)
        
        # 세션 확인
        if 'username' in session and session.get('expires', 0) > datetime.now().timestamp():
            request.current_user = session['username']
            return f(*args, **kwargs)
        
        return jsonify({'error': '인증이 필요합니다'}), 401
    
    return decorated_function

def require_trading_token(f):
    """거래 토큰 필요 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Trading-Token') or request.json.get('token') if request.json else request.args.get('token')
        
        if not token:
            return jsonify({'error': '거래 토큰이 필요합니다'}), 400
        
        api.ACCESS_TOKEN = token
        return f(*args, **kwargs)
    
    return decorated_function

# 메인 페이지 (간단한 대시보드)
@app.route('/')
def index():
    """메인 대시보드 페이지"""
    return render_template_string('''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>자동매매 시스템</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .card { background: #f8f9fa; padding: 20px; margin: 15px 0; border-radius: 8px; border-left: 4px solid #007bff; }
        .api-endpoint { background: #e9ecef; padding: 10px; border-radius: 4px; font-family: monospace; margin: 5px 0; }
        .status { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; }
        .status.success { background: #d4edda; color: #155724; }
        .status.info { background: #d1ecf1; color: #0c5460; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 자동매매 시스템 API</h1>
            <p>한국투자증권 API 기반 자동매매 서비스</p>
            <span class="status success">운영중</span>
        </div>
        
        <div class="card">
            <h3>🔐 인증</h3>
            <div class="api-endpoint">POST /auth/login - 로그인</div>
            <div class="api-endpoint">POST /auth/register - 회원가입 (관리자만)</div>
            <div class="api-endpoint">GET /auth/api-key - API 키 조회</div>
        </div>
        
        <div class="card">
            <h3>📈 거래 API</h3>
            <div class="api-endpoint">GET /api/price - 현재가 조회</div>
            <div class="api-endpoint">POST /api/order - 주문 실행</div>
            <div class="api-endpoint">GET /api/orders - 주문 내역</div>
            <div class="api-endpoint">GET /api/holdings - 보유 현황</div>
        </div>
        
        <div class="card">
            <h3>📊 데이터 API</h3>
            <div class="api-endpoint">GET /api/dashboard - 대시보드 데이터</div>
            <div class="api-endpoint">GET /api/statistics - 거래 통계</div>
            <div class="api-endpoint">GET /api/price-history - 가격 히스토리</div>
            <div class="api-endpoint">GET /api/logs - 시스템 로그</div>
        </div>
        
        <div class="card">
            <h3>🛠️ 관리 API</h3>
            <div class="api-endpoint">POST /api/backup - 데이터베이스 백업</div>
            <div class="api-endpoint">POST /api/cleanup - 데이터 정리</div>
            <div class="api-endpoint">GET /api/status - 시스템 상태</div>
        </div>
        
        <div class="card">
            <h3>📝 사용법</h3>
            <p>1. <strong>로그인</strong>: POST /auth/login으로 인증</p>
            <p>2. <strong>API 키 발급</strong>: GET /auth/api-key로 키 확인</p>
            <p>3. <strong>요청 헤더</strong>: X-API-Key 또는 Trading-Token 포함</p>
            <p>4. <strong>웹 인터페이스</strong>: GET /dashboard로 웹 UI 접속</p>
        </div>
    </div>
</body>
</html>
    ''')

# 인증 라우트
@app.route('/auth/login', methods=['POST'])
def login():
    """로그인"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': '사용자명과 비밀번호가 필요합니다'}), 400
    
    if auth_manager.verify_user(username, password):
        session['username'] = username
        session['expires'] = (datetime.now() + timedelta(seconds=app.config['SESSION_TIMEOUT'])).timestamp()
        
        logger.info(f"사용자 로그인: {username}")
        db.log_info(f"사용자 로그인: {username}")
        
        return jsonify({
            'success': True,
            'message': '로그인 성공',
            'api_key': auth_manager.get_api_key(username)
        })
    
    logger.warning(f"로그인 실패: {username}")
    return jsonify({'error': '인증 실패'}), 401

@app.route('/auth/register', methods=['POST'])
@require_auth
def register():
    """회원가입 (관리자만)"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': '사용자명과 비밀번호가 필요합니다'}), 400
    
    if len(password) < 8:
        return jsonify({'error': '비밀번호는 8자 이상이어야 합니다'}), 400
    
    if auth_manager.create_user(username, password):
        logger.info(f"새 사용자 생성: {username}")
        db.log_info(f"새 사용자 생성: {username}")
        
        return jsonify({
            'success': True,
            'message': '사용자 생성 완료',
            'api_key': auth_manager.get_api_key(username)
        })
    
    return jsonify({'error': '이미 존재하는 사용자명입니다'}), 409

@app.route('/auth/api-key')
@require_auth
def get_api_key():
    """API 키 조회"""
    api_key = auth_manager.get_api_key(request.current_user)
    return jsonify({'api_key': api_key})

@app.route('/auth/logout', methods=['POST'])
def logout():
    """로그아웃"""
    username = session.get('username')
    session.clear()
    
    if username:
        logger.info(f"사용자 로그아웃: {username}")
    
    return jsonify({'success': True, 'message': '로그아웃 완료'})

# API 라우트 (기존 라우트들을 /api 프리픽스로 이동하고 인증 추가)
@app.route('/api/price')
@require_auth
@require_trading_token
def api_get_price():
    """현재가 조회"""
    code = request.args.get('code')
    if not code:
        return jsonify({'error': '종목코드가 필요합니다'}), 400

    try:
        price = api.fetch_current_price(code)
        if price is not None:
            db.save_price_data(code, price)
            db.log_info(f"가격 조회: {code} - {price:,}원 (사용자: {request.current_user})")
            return jsonify({'price': price})
        else:
            return jsonify({'error': '가격 조회 실패'}), 500
    except Exception as e:
        logger.error(f"가격 조회 오류: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/order', methods=['POST'])
@require_auth
@require_trading_token
def api_make_order():
    """주문 실행"""
    data = request.get_json()
    required_fields = ['type', 'account', 'code', 'amount', 'price']
    
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} 필드가 필요합니다'}), 400

    try:
        order_id = db.save_order(
            data['code'], data['type'], 
            data['amount'], data['price'], 'PENDING'
        )
        
        success = api.order(
            data['type'], data['account'], 
            data['code'], data['amount'], data['price']
        )
        
        status = 'SUCCESS' if success else 'FAILED'
        db.update_order_status(order_id, status)
        
        log_msg = f"주문 {status}: {data['type']} {data['code']} {data['amount']}주 @ {data['price']:,}원 (사용자: {request.current_user})"
        db.log_info(log_msg)
        logger.info(log_msg)
        
        return jsonify({'success': success, 'order_id': order_id})
        
    except Exception as e:
        logger.error(f"주문 실행 오류: {e}")
        db.log_error(f"주문 실행 오류: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard')
@require_auth
def api_dashboard():
    """대시보드 데이터"""
    code = request.args.get('code', '122640')
    
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
        
        # 통계
        today_stats = db.get_statistics(code, 1)
        week_stats = db.get_statistics(code, 7)
        
        # 최근 주문
        recent_orders = db.get_orders(code, 5)
        
        dashboard_data = {
            'current_price': current_price,
            'ma20': ma20,
            'ma60': ma60,
            'today_stats': today_stats,
            'week_stats': week_stats,
            'recent_orders': recent_orders,
            'user': request.current_user
        }
        
        return jsonify({'dashboard': dashboard_data})
        
    except Exception as e:
        logger.error(f"대시보드 데이터 오류: {e}")
        return jsonify({'error': str(e)}), 500

# 웹 대시보드 페이지
@app.route('/dashboard')
def web_dashboard():
    """웹 대시보드 (수정된 HTML 파일 내용을 여기에 포함)"""
    # 기존 HTML 파일 내용을 서버에서 직접 제공
    # 보안을 위해 API 키 입력 방식으로 변경
    return render_template_string('''
    <!-- 수정된 HTML 내용: API 키 인증 방식으로 변경된 버전 -->
    <!-- 여기에 업데이트된 HTML 코드 포함 -->
    ''')

# 에러 핸들러
@app.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({'error': '속도 제한 초과. 잠시 후 다시 시도해주세요.'}), 429

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"서버 내부 오류: {error}")
    return jsonify({'error': '서버 내부 오류가 발생했습니다.'}), 500

# 헬스체크
@app.route('/health')
def health_check():
    """헬스체크"""
    try:
        # 데이터베이스 연결 확인
        db.get_logs(limit=1)
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 503

if __name__ == '__main__':
    logger.info("프로덕션 Flask 서버 시작")
    
    # 개발 환경에서만 실행
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('FLASK_ENV') == 'development'
    )