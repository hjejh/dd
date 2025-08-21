# flyio-monitor.py (Fly.io 모니터링)
"""
Fly.io 환경에서의 모니터링 스크립트
"""

import os
import time
import requests
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FlyioMonitor:
    def __init__(self, app_name):
        self.app_name = app_name
        self.app_url = f"https://{app_name}.fly.dev"
        
    def check_health(self):
        """헬스체크"""
        try:
            response = requests.get(f"{self.app_url}/health", timeout=10)
            if response.status_code == 200:
                logger.info("✅ 앱 상태 정상")
                return True
            else:
                logger.warning(f"⚠️ 앱 상태 이상: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ 헬스체크 실패: {e}")
            return False
    
    def get_metrics(self):
        """메트릭 수집"""
        try:
            response = requests.get(f"{self.app_url}/api/statistics?days=1", timeout=10)
            if response.status_code == 200:
                stats = response.json().get('statistics', {})
                logger.info(f"📊 오늘 거래: {stats.get('total_orders', 0)}회")
                return stats
        except Exception as e:
            logger.error(f"❌ 메트릭 수집 실패: {e}")
        return {}
    
    def send_alert(self, message):
        """알림 발송 (Webhook 등)"""
        webhook_url = os.environ.get('ALERT_WEBHOOK_URL')
        if webhook_url:
            try:
                requests.post(webhook_url, json={'text': message})
                logger.info(f"📢 알림 발송: {message}")
            except Exception as e:
                logger.error(f"❌ 알림 발송 실패: {e}")

# 사용 예시
if __name__ == "__main__":
    app_name = os.environ.get('FLY_APP_NAME', 'trading-system')
    monitor = FlyioMonitor(app_name)
    
    while True:
        if not monitor.check_health():
            monitor.send_alert(f"🚨 {app_name} 앱 헬스체크 실패")
        
        monitor.get_metrics()
        time.sleep(300)  # 5분마다 체크