# setup_database.py
"""
자동매매 시스템 데이터베이스 설정 및 초기화 스크립트
"""

import os
import sqlite3
import json
from datetime import datetime, timedelta
from database import TradingDatabase

def create_sample_data(db: TradingDatabase, stock_code: str = "122640"):
    """샘플 데이터 생성"""
    print("📊 샘플 데이터 생성 중...")
    
    # 샘플 가격 데이터 (최근 60일)
    base_price = 50000
    prices = []
    
    for i in range(60):
        # 가격 변동 시뮬레이션 (±3% 범위)
        import random
        change_rate = (random.random() - 0.5) * 0.06  # -3% ~ +3%
        base_price = int(base_price * (1 + change_rate))
        prices.append(base_price)
        
        # 데이터베이스에 저장
        db.save_price_data(stock_code, base_price)
        
        # 이동평균 계산 (20일 이후부터)
        if i >= 19:
            ma20 = sum(prices[-20:]) // 20
            ma60 = sum(prices[-min(60, len(prices)):]) // min(60, len(prices)) if i >= 59 else None
            
            db.save_moving_averages(stock_code, base_price, ma20, ma60)
            
            # 간단한 신호 생성
            if i >= 59:  # 60일 후부터 신호 생성
                signal = "HOLD"
                if ma20 > ma60:
                    signal = "BUY" if random.random() > 0.7 else "HOLD"
                else:
                    signal = "SELL" if random.random() > 0.7 else "HOLD"
                
                db.save_trading_signal(stock_code, signal, base_price, ma20, ma60)
                
                # 주문 데이터 생성 (30% 확률)
                if signal != "HOLD" and random.random() > 0.7:
                    quantity = random.randint(1, 10)
                    status = "SUCCESS" if random.random() > 0.1 else "FAILED"
                    db.save_order(stock_code, signal, quantity, base_price, status)
    
    # 자동매매 설정 생성
    db.save_trading_settings(
        stock_code=stock_code,
        is_active=False,
        ma_short_period=20,
        ma_long_period=60,
        max_buy_amount=1000000,
        additional_settings={
            "auto_start": False,
            "risk_level": "medium",
            "stop_loss_rate": 0.05,
            "take_profit_rate": 0.1
        }
    )
    
    print(f"✅ {stock_code} 샘플 데이터 생성 완료")

def check_database_integrity(db_path: str):
    """데이터베이스 무결성 검사"""
    print("🔍 데이터베이스 무결성 검사 중...")
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # 테이블 존재 확인
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = [
                'price_data', 'moving_averages', 'trading_signals', 
                'orders', 'account_status', 'trading_settings', 'trading_logs'
            ]
            
            missing_tables = [table for table in expected_tables if table not in tables]
            
            if missing_tables:
                print(f"❌ 누락된 테이블: {missing_tables}")
                return False
            
            # 각 테이블의 레코드 수 확인
            for table in expected_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"📊 {table}: {count}개 레코드")
            
            print("✅ 데이터베이스 무결성 검사 완료")
            return True
            
    except Exception as e:
        print(f"❌ 데이터베이스 검사 실패: {e}")
        return False

def backup_existing_database(db_path: str):
    """기존 데이터베이스 백업"""
    if os.path.exists(db_path):
        backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            import shutil
            shutil.copy2(db_path, backup_path)
            print(f"📦 기존 데이터베이스 백업: {backup_path}")
            return backup_path
        except Exception as e:
            print(f"❌ 백업 실패: {e}")
            return None
    return None

def restore_database(backup_path: str, db_path: str):
    """데이터베이스 복원"""
    try:
        import shutil
        shutil.copy2(backup_path, db_path)
        print(f"🔄 데이터베이스 복원 완료: {backup_path} -> {db_path}")
        return True
    except Exception as e:
        print(f"❌ 복원 실패: {e}")
        return False

def optimize_database(db_path: str):
    """데이터베이스 최적화"""
    print("⚡ 데이터베이스 최적화 중...")
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # VACUUM으로 데이터베이스 압축
            cursor.execute("VACUUM")
            
            # 통계 업데이트
            cursor.execute("ANALYZE")
            
            conn.commit()
            
        print("✅ 데이터베이스 최적화 완료")
        return True
        
    except Exception as e:
        print(f"❌ 최적화 실패: {e}")
        return False

def export_data_to_json(db: TradingDatabase, stock_code: str, output_file: str):
    """데이터를 JSON으로 내보내기"""
    print(f"📤 데이터 내보내기: {output_file}")
    
    try:
        export_data = {
            "export_time": datetime.now().isoformat(),
            "stock_code": stock_code,
            "price_history": db.get_price_history(stock_code, 1000),
            "moving_averages": db.get_latest_moving_averages(stock_code, 100),
            "orders": db.get_orders(stock_code, 1000),
            "statistics": {
                "1_day": db.get_statistics(stock_code, 1),
                "7_days": db.get_statistics(stock_code, 7),
                "30_days": db.get_statistics(stock_code, 30)
            },
            "settings": db.get_trading_settings(stock_code)
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 데이터 내보내기 완료: {output_file}")
        return True
        
    except Exception as e:
        print(f"❌ 내보내기 실패: {e}")
        return False

def import_data_from_json(db: TradingDatabase, input_file: str):
    """JSON에서 데이터 가져오기"""
    print(f"📥 데이터 가져오기: {input_file}")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            import_data = json.load(f)
        
        stock_code = import_data['stock_code']
        
        # 가격 데이터 가져오기
        for price_data in import_data['price_history']:
            db.save_price_data(stock_code, price_data['price'])
        
        # 이동평균 데이터 가져오기
        for ma_data in import_data['moving_averages']:
            db.save_moving_averages(
                stock_code, ma_data['price'], 
                ma_data['ma20'], ma_data['ma60']
            )
        
        # 설정 가져오기
        if 'settings' in import_data and import_data['settings']:
            settings = import_data['settings']
            db.save_trading_settings(
                stock_code,
                settings.get('is_active', False),
                settings.get('ma_short_period', 20),
                settings.get('ma_long_period', 60),
                settings.get('max_buy_amount', 1000000),
                settings.get('additional_settings', {})
            )
        
        print(f"✅ 데이터 가져오기 완료")
        return True
        
    except Exception as e:
        print(f"❌ 가져오기 실패: {e}")
        return False

def show_menu():
    """메뉴 표시"""
    print("\n" + "=" * 60)
    print("🗄️  자동매매 시스템 데이터베이스 관리")
    print("=" * 60)
    print("1. 새 데이터베이스 생성 (기존 데이터 삭제)")
    print("2. 데이터베이스 무결성 검사")
    print("3. 샘플 데이터 생성")
    print("4. 데이터베이스 백업")
    print("5. 데이터베이스 복원")
    print("6. 데이터베이스 최적화")
    print("7. 오래된 데이터 정리")
    print("8. 데이터 JSON 내보내기")
    print("9. JSON 데이터 가져오기")
    print("10. 통계 조회")
    print("0. 종료")
    print("=" * 60)

def main():
    """메인 함수"""
    db_path = "trading_data.db"
    
    while True:
        show_menu()
        choice = input("\n선택하세요: ").strip()
        
        if choice == "1":
            # 새 데이터베이스 생성
            if os.path.exists(db_path):
                confirm = input("⚠️  기존 데이터베이스가 삭제됩니다. 계속하시겠습니까? (y/N): ")
                if confirm.lower() != 'y':
                    print("❌ 취소됨")
                    continue
                
                backup_existing_database(db_path)
                os.remove(db_path)
            
            db = TradingDatabase(db_path)
            print("✅ 새 데이터베이스 생성 완료")
            
        elif choice == "2":
            # 무결성 검사
            check_database_integrity(db_path)
            
        elif choice == "3":
            # 샘플 데이터 생성
            stock_code = input("종목코드 입력 (기본: 122640): ").strip() or "122640"
            db = TradingDatabase(db_path)
            create_sample_data(db, stock_code)
            
        elif choice == "4":
            # 백업
            db = TradingDatabase(db_path)
            backup_path = db.backup_database()
            if backup_path:
                print(f"✅ 백업 완료: {backup_path}")
            else:
                print("❌ 백업 실패")
                
        elif choice == "5":
            # 복원
            backup_path = input("복원할 백업 파일 경로: ").strip()
            if os.path.exists(backup_path):
                restore_database(backup_path, db_path)
            else:
                print("❌ 백업 파일을 찾을 수 없습니다")
                
        elif choice == "6":
            # 최적화
            optimize_database(db_path)
            
        elif choice == "7":
            # 오래된 데이터 정리
            days = input("보관 기간 (일, 기본: 90): ").strip()
            days = int(days) if days.isdigit() else 90
            db = TradingDatabase(db_path)
            if db.cleanup_old_data(days):
                print(f"✅ {days}일 이전 데이터 정리 완료")
            else:
                print("❌ 데이터 정리 실패")
                
        elif choice == "8":
            # JSON 내보내기
            stock_code = input("종목코드 (기본: 122640): ").strip() or "122640"
            output_file = input("출력 파일명 (기본: export_data.json): ").strip() or "export_data.json"
            db = TradingDatabase(db_path)
            export_data_to_json(db, stock_code, output_file)
            
        elif choice == "9":
            # JSON 가져오기
            input_file = input("가져올 JSON 파일: ").strip()
            if os.path.exists(input_file):
                db = TradingDatabase(db_path)
                import_data_from_json(db, input_file)
            else:
                print("❌ 파일을 찾을 수 없습니다")
                
        elif choice == "10":
            # 통계 조회
            stock_code = input("종목코드 (기본: 122640): ").strip() or "122640"
            db = TradingDatabase(db_path)
            
            print(f"\n📊 {stock_code} 통계")
            print("-" * 40)
            
            for days in [1, 7, 30]:
                stats = db.get_statistics(stock_code, days)
                print(f"\n최근 {days}일:")
                print(f"  총 주문: {stats.get('total_orders', 0)}회")
                print(f"  성공한 주문: {stats.get('successful_orders', 0)}회")
                print(f"  매수: {stats.get('buy_count', 0)}회")
                print(f"  매도: {stats.get('sell_count', 0)}회")
                print(f"  총 거래금액: {stats.get('total_amount', 0):,}원")
            
        elif choice == "0":
            print("👋 프로그램 종료")
            break
            
        else:
            print("❌ 잘못된 선택입니다")
        
        input("\n📋 Enter를 눌러 계속...")

if __name__ == "__main__":
    print("🚀 자동매매 데이터베이스 관리 도구")
    print("📝 이 도구를 사용하여 데이터베이스를 설정하고 관리할 수 있습니다.")
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 사용자에 의해 중단됨")
    except Exception as e:
        print(f"\n💥 오류 발생: {e}")