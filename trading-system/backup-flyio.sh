# 백업 스크립트 for Fly.io
# backup-flyio.sh
#!/bin/bash

APP_NAME="trading-system"
BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)

echo "💾 Fly.io 데이터 백업 시작"

# 백업 디렉토리 생성
mkdir -p $BACKUP_DIR

# 데이터베이스 백업
echo "🗄️ 데이터베이스 백업 중..."
flyctl ssh sftp get /data/trading_data.db $BACKUP_DIR/trading_data_$DATE.db -a $APP_NAME

# 설정 백업
echo "⚙️ 설정 백업 중..."
flyctl config save -a $APP_NAME > $BACKUP_DIR/config_$DATE.json

# 로그 백업
echo "📄 로그 백업 중..."
flyctl logs -a $APP_NAME > $BACKUP_DIR/logs_$DATE.txt

echo "✅ 백업 완료: $BACKUP_DIR/"
ls -la $BACKUP_DIR/
