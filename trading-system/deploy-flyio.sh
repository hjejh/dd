# deploy-flyio.sh
#!/bin/bash

echo "🚀 Fly.io 배포 시작"

# Fly CLI 설치 확인
if ! command -v flyctl &> /dev/null; then
    echo "📦 Fly CLI 설치 중..."
    curl -L https://fly.io/install.sh | sh
    export PATH="$HOME/.fly/bin:$PATH"
fi

# Fly.io 로그인 확인
if ! flyctl auth whoami &> /dev/null; then
    echo "🔐 Fly.io 로그인이 필요합니다."
    flyctl auth login
fi

# 앱 이름 설정
read -p "앱 이름을 입력하세요 (기본: trading-system): " APP_NAME
APP_NAME=${APP_NAME:-trading-system}

# 앱 생성 (이미 존재하면 스킵)
if ! flyctl apps list | grep -q "$APP_NAME"; then
    echo "📱 새 앱 생성: $APP_NAME"
    flyctl apps create $APP_NAME --region nrt
    
    # fly.toml 업데이트
    sed -i "s/app = \"trading-system\"/app = \"$APP_NAME\"/" fly.toml
else
    echo "📱 기존 앱 사용: $APP_NAME"
fi

# 볼륨 생성 (데이터 영속성을 위해)
if ! flyctl volumes list -a $APP_NAME | grep -q "trading_data"; then
    echo "💾 데이터 볼륨 생성 중..."
    flyctl volumes create trading_data --region nrt --size 3 -a $APP_NAME
fi

# 시크릿 설정
echo "🔐 환경 변수 설정 중..."

# 시크릿 키 생성
SECRET_KEY=$(openssl rand -base64 32)
flyctl secrets set SECRET_KEY="$SECRET_KEY" -a $APP_NAME

# 관리자 비밀번호 설정
ADMIN_PASSWORD=$(openssl rand -base64 16)
flyctl secrets set ADMIN_PASSWORD="$ADMIN_PASSWORD" -a $APP_NAME

# 한국투자증권 API 설정
read -p "한국투자증권 APPKEY를 입력하세요: " APPKEY
read -p "한국투자증권 APPSECRET을 입력하세요: " APPSECRET
read -p "계좌번호를 입력하세요: " ACCOUNT

if [ ! -z "$APPKEY" ]; then
    flyctl secrets set APPKEY="$APPKEY" -a $APP_NAME
fi
if [ ! -z "$APPSECRET" ]; then
    flyctl secrets set APPSECRET="$APPSECRET" -a $APP_NAME
fi
if [ ! -z "$ACCOUNT" ]; then
    flyctl secrets set ACCOUNT="$ACCOUNT" -a $APP_NAME
fi

# CORS 설정
DOMAIN="https://$APP_NAME.fly.dev"
flyctl secrets set ALLOWED_ORIGINS="$DOMAIN" -a $APP_NAME

# 배포 실행
echo "🚢 배포 중..."
flyctl deploy -a $APP_NAME

# 데이터베이스 초기화 (첫 배포시)
read -p "데이터베이스를 초기화하시겠습니까? (y/N): " INIT_DB
if [ "$INIT_DB" = "y" ]; then
    echo "🗄️ 데이터베이스 초기화 중..."
    flyctl ssh console -a $APP_NAME -C "python setup_database.py"
fi

# 도메인 정보 출력
echo "✅ 배포 완료!"
echo "🌐 앱 URL: https://$APP_NAME.fly.dev"
echo "📊 대시보드: https://$APP_NAME.fly.dev/dashboard"
echo "🔑 관리자 비밀번호: $ADMIN_PASSWORD"

# 앱 상태 확인
echo "📋 앱 상태 확인 중..."
flyctl status -a $APP_NAME

# 로그 확인
echo "📄 최근 로그:"
flyctl logs -a $APP_NAME --limit 20

echo ""
echo "💡 유용한 명령어:"
echo "  flyctl logs -a $APP_NAME          # 로그 확인"
echo "  flyctl ssh console -a $APP_NAME   # SSH 접속"
echo "  flyctl status -a $APP_NAME        # 상태 확인"
echo "  flyctl deploy -a $APP_NAME        # 재배포"