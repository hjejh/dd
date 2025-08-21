# flyio-production.py (Fly.io 최적화 서버)
"""
Fly.io 환경에 최적화된 Flask 서버
"""

import os
import sys
import logging
from production_flask_server import app, db

# Fly.io 환경 설정
class FlyioConfig:
    # Fly.io 특화 설정
    FLY_APP_NAME = os.environ.get('FLY_APP_NAME')
    FLY_REGION = os.environ.get('FLY_REGION')
    FLY_PUBLIC_IP = os.environ.get('FLY_PUBLIC_IP')
    
    # 데이터베이스 경로 (볼륨 마운트)
    DATABASE_PATH = '/data/trading_data.db'
    
    # 로깅 설정
    LOG_LEVEL = 'INFO'
    
    # 성능 설정
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Fly.io 헬스체크 대응
    HEALTH_CHECK_PATH = '/health'

# 앱 설정 업데이트
app.config.from_object(FlyioConfig)

# Fly.io 최적화 로깅
logging.basicConfig(
    level=getattr(logging, FlyioConfig.LOG_LEVEL),
    format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Fly.io 환경 정보 로깅
@app.before_first_request
def log_environment():
    logger.info(f"🚀 Fly.io에서 앱 시작")
    logger.info(f"📱 앱 이름: {FlyioConfig.FLY_APP_NAME}")
    logger.info(f"🌍 리전: {FlyioConfig.FLY_REGION}")
    logger.info(f"🌐 공인 IP: {FlyioConfig.FLY_PUBLIC_IP}")
    
    # 데이터베이스 초기화
    try:
        db.log_info(f"Fly.io에서 서비스 시작 - 리전: {FlyioConfig.FLY_REGION}")
        logger.info("✅ 데이터베이스 연결 성공")
    except Exception as e:
        logger.error(f"❌ 데이터베이스 연결 실패: {e}")

# Fly.io 특화 헬스체크
@app.route('/health')
def flyio_health_check():
    """Fly.io 최적화 헬스체크"""
    try:
        # 데이터베이스 연결 확인
        db.get_logs(limit=1)
        
        health_data = {
            'status': 'healthy',
            'app': FlyioConfig.FLY_APP_NAME,
            'region': FlyioConfig.FLY_REGION,
            'database': 'connected',
            'timestamp': db.db.execute('SELECT datetime("now")').fetchone()[0] if hasattr(db, 'db') else None
        }
        
        return health_data, 200
        
    except Exception as e:
        logger.error(f"헬스체크 실패: {e}")
        return {
            'status': 'unhealthy',
            'error': str(e),
            'app': FlyioConfig.FLY_APP_NAME,
            'region': FlyioConfig.FLY_REGION
        }, 503

# Fly.io 스케일링 정보
@app.route('/fly-info')
def fly_info():
    """Fly.io 환경 정보"""
    return {
        'app_name': FlyioConfig.FLY_APP_NAME,
        'region': FlyioConfig.FLY_REGION,
        'public_ip': FlyioConfig.FLY_PUBLIC_IP,
        'instance_id': os.environ.get('FLY_MACHINE_ID'),
        'version': os.environ.get('FLY_IMAGE_REF')
    }

# 그레이스풀 셧다운
import signal
import atexit

def cleanup():
    """앱 종료시 정리 작업"""
    try:
        db.log_info("Fly.io에서 서비스 종료")
        db.close()
        logger.info("✅ 정리 작업 완료")
    except Exception as e:
        logger.error(f"❌ 정리 작업 실패: {e}")

# 시그널 핸들러 등록
signal.signal(signal.SIGTERM, lambda s, f: cleanup())
signal.signal(signal.SIGINT, lambda s, f: cleanup())
atexit.register(cleanup)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False
    )