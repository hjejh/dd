# 복원 스크립트 for Fly.io
# restore-flyio.sh
#!/bin/bash

APP_NAME="trading-system"

if [ -z "$1" ]; then
    echo "사용법: ./restore-flyio.sh <백업파일.db>"
    exit 1
fi

BACKUP_FILE=$1

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ 백업 파일을 찾을 수 없습니다: $BACKUP_FILE"
    exit 1
fi

echo "🔄 Fly.io 데이터 복원 시작"

# 현재 데이터베이스 백업
echo "💾 현재 데이터베이스 백업 중..."
flyctl ssh sftp get /data/trading_data.db ./current_backup.db -a $APP_NAME

# 앱 일시 중지
echo "⏸️ 앱 일시 중지..."
flyctl scale count 0 -a $APP_NAME

# 데이터베이스 복원
echo "🔄 데이터베이스 복원 중..."
flyctl ssh sftp put $BACKUP_FILE /data/trading_data.db -a $APP_NAME

# 앱 재시작
echo "🚀 앱 재시작..."
flyctl scale count 1 -a $APP_NAME

# 상태 확인
sleep 30
flyctl status -a $APP_NAME

echo "✅ 복원 완료!"