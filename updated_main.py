# updated_main.py
from time import sleep
import indicator
import strategy
import api
from database import TradingDatabase
from dotenv import load_dotenv
import os
from typing import List

load_dotenv()

APPKEY = os.environ["APPKEY"]
APPSECRET = os.environ["APPSECRET"]
ACCOUNT = os.environ["ACCOUNT"]
ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]

CODE = "122640"

# 데이터베이스 초기화
db = TradingDatabase("trading_data.db")

def calculate_ma(prices: List[int], period: int) -> int:
    """이동평균 계산"""
    if len(prices) < period:
        return None
    return sum(prices[-period:]) // period

def get_ma_signal(ma20_list: List[int], ma60_list: List[int]) -> str:
    """이동평균 기반 매매 신호 생성"""
    if len(ma20_list) < 2 or len(ma60_list) < 2:
        return "HOLD"
    
    # 골든크로스/데드크로스 확인
    prev_ma20, curr_ma20 = ma20_list[-2], ma20_list[-1]
    prev_ma60, curr_ma60 = ma60_list[-2], ma60_list[-1]
    
    # 골든크로스: MA20이 MA60을 상향 돌파
    if prev_ma20 <= prev_ma60 and curr_ma20 > curr_ma60:
        return "BUY"
    # 데드크로스: MA20이 MA60을 하향 돌파
    elif prev_ma20 >= prev_ma60 and curr_ma20 < curr_ma60:
        return "SELL"
    
    return "HOLD"

def load_initial_data():
    """프로그램 시작시 기존 데이터 로드"""
    db.log_info("자동매매 프로그램 시작")
    
    # 최근 60개 가격 데이터 로드 (MA60 계산을 위해)
    recent_prices = db.get_recent_prices(CODE, 60)
    
    if recent_prices:
        db.log_info(f"기존 가격 데이터 로드: {len(recent_prices)}개")
        print(f"기존 데이터 로드 완료: {len(recent_prices)}개 가격 데이터")
    else:
        db.log_info("기존 데이터 없음 - 새로 시작")
        print("기존 데이터 없음 - 새로 시작합니다.")
    
    return recent_prices

def save_current_data(price: int, ma20: int, ma60: int, signal: str):
    """현재 데이터를 데이터베이스에 저장"""
    # 가격 데이터 저장
    db.save_price_data(CODE, price)
    
    # 이동평균 데이터 저장
    db.save_moving_averages(CODE, price, ma20, ma60)
    
    # 매매 신호 저장
    db.save_trading_signal(CODE, signal, price, ma20, ma60)

def execute_order_with_db(signal: str, quantity: int, price: int):
    """주문 실행 및 데이터베이스 기록"""
    if quantity <= 0:
        return False
    
    # 데이터베이스에 주문 기록 (PENDING 상태로)
    order_id = db.save_order(CODE, signal, quantity, price, "PENDING")
    
    try:
        # 실제 주문 실행
        result = api.order(signal, ACCOUNT, CODE, quantity, price)
        
        if result:
            # 성공시 상태 업데이트
            db.update_order_status(order_id, "SUCCESS")
            db.log_info(f"주문 성공: {signal} {quantity}주 @ {price:,}원")
            print(f"✅ {signal} {CODE} {quantity}개 {price:,}원 주문 성공")
            return True
        else:
            # 실패시 상태 업데이트
            db.update_order_status(order_id, "FAILED", "API 주문 실행 실패")
            db.log_error(f"주문 실패: {signal} {quantity}주 @ {price:,}원")
            print(f"❌ {signal} {CODE} {quantity}개 {price:,}원 주문 실패")
            return False
            
    except Exception as e:
        # 예외 발생시 상태 업데이트
        db.update_order_status(order_id, "FAILED", str(e))
        db.log_error(f"주문 예외 발생: {e}")
        print(f"❌ 주문 중 오류 발생: {e}")
        return False

def update_account_status():
    """계좌 상태 업데이트"""
    try:
        # 보유 수량 조회
        holding_quantity = api.fetch_quantity(ACCOUNT, CODE)
        
        # 총 평가금 조회
        total_evaluation = api.fetch_eval(ACCOUNT)
        
        if total_evaluation:
            total_evaluation = int(total_evaluation)
            
            # 데이터베이스에 계좌 상태 저장
            db.save_account_status(ACCOUNT, CODE, int(holding_quantity), total_evaluation)
            
            print(f"📊 보유수량: {holding_quantity}주, 총평가금: {total_evaluation:,}원")
            return holding_quantity, total_evaluation
        else:
            db.log_warning("총 평가금 조회 실패")
            return holding_quantity, 0
            
    except Exception as e:
        db.log_error(f"계좌 상태 업데이트 실패: {e}")
        return 0, 0

def cleanup_orders():
    """미체결 주문 정리"""
    try:
        api.clear_orders(ACCOUNT, CODE)
        db.log_info("미체결 주문 정리 완료")
        print("🔄 미체결 주문 정리 완료")
    except Exception as e:
        db.log_error(f"미체결 주문 정리 실패: {e}")
        print(f"❌ 미체결 주문 정리 실패: {e}")

def main_trading_loop():
    """메인 자동매매 루프"""
    print("🚀 자동매매 시스템 시작")
    print("=" * 50)
    
    # 초기 데이터 로드
    prices = load_initial_data()
    
    # 자동매매 설정 확인/생성
    settings = db.get_trading_settings(CODE)
    if not settings:
        db.save_trading_settings(CODE, True, 20, 60, 1000000)
        settings = db.get_trading_settings(CODE)
        print("🔧 초기 자동매매 설정 생성 완료")
    
    print(f"📈 종목: {CODE}")
    print(f"⚙️  MA 설정: {settings['ma_short_period']}/{settings['ma_long_period']}")
    print(f"💰 최대 매수금액: {settings['max_buy_amount']:,}원")
    print("=" * 50)
    
    cycle_count = 0
    
    try:
        while True:
            cycle_count += 1
            print(f"\n📊 매매 사이클 #{cycle_count}")
            print("-" * 30)
            
            try:
                # 현재 가격 조회
                current_price = api.fetch_current_price(CODE)
                if current_price is None:
                    db.log_error("가격 조회 실패")
                    print("❌ 가격 조회 실패")
                    sleep(60)
                    continue
                
                # 가격 리스트에 추가
                prices.append(current_price)
                
                # 이동평균 계산
                ma20 = calculate_ma(prices, 20)
                ma60 = calculate_ma(prices, 60)
                
                # 이동평균이 계산 가능한 경우에만 진행
                if ma20 is None or ma60 is None:
                    print(f"📈 가격: {current_price:,}원 (데이터 수집 중...)")
                    db.save_price_data(CODE, current_price)
                    sleep(60)
                    continue
                
                # 매매 신호 판단
                # 최근 이동평균 데이터 가져오기
                recent_ma_data = db.get_latest_moving_averages(CODE, 2)
                
                # 신호 계산을 위한 MA 리스트 구성
                ma20_list = []
                ma60_list = []
                
                for data in recent_ma_data:
                    ma20_list.append(data['ma20'])
                    ma60_list.append(data['ma60'])
                
                # 현재 값 추가
                ma20_list.append(ma20)
                ma60_list.append(ma60)
                
                signal = get_ma_signal(ma20_list, ma60_list)
                
                print(f"📈 가격: {current_price:,}원")
                print(f"📊 MA20: {ma20:,}원, MA60: {ma60:,}원")
                print(f"🎯 신호: {signal}")
                
                # 데이터베이스에 현재 데이터 저장
                save_current_data(current_price, ma20, ma60, signal)
                
                # 미체결 주문 정리
                cleanup_orders()
                
                # 매매 실행
                executed = False
                if signal == "BUY":
                    # 매수 가능 수량 조회
                    available_qty = api.fetch_avail(ACCOUNT, CODE, current_price)
                    if available_qty > 0:
                        executed = execute_order_with_db("BUY", available_qty, current_price)
                    else:
                        print("💰 매수 가능 자금 부족")
                        
                elif signal == "SELL":
                    # 보유 수량 조회
                    holding_qty = api.fetch_quantity(ACCOUNT, CODE)
                    if holding_qty > 0:
                        executed = execute_order_with_db("SELL", holding_qty, current_price)
                    else:
                        print("📦 보유 주식 없음")
                
                if not executed and signal != "HOLD":
                    print("⏸️  주문 조건 미충족")
                elif signal == "HOLD":
                    print("⏸️  대기")
                
                # 계좌 상태 업데이트 (매 사이클마다)
                holding_qty, total_eval = update_account_status()
                
                # 가격 히스토리 관리 (메모리 효율성을 위해 최근 100개만 유지)
                if len(prices) > 100:
                    prices = prices[-100:]
                
                print(f"💤 1분 대기...")
                
            except Exception as e:
                db.log_error(f"매매 사이클 오류: {e}")
                print(f"❌ 매매 사이클 오류: {e}")
            
            sleep(60)
            
    except KeyboardInterrupt:
        print("\n🛑 사용자에 의해 중단됨")
        db.log_info("사용자에 의해 자동매매 중단")
    except Exception as e:
        print(f"\n💥 예기치 못한 오류: {e}")
        db.log_error(f"예기치 못한 오류로 프로그램 종료: {e}")
    finally:
        print("🔄 프로그램 종료 중...")
        
        # 최종 상태 저장
        try:
            update_account_status()
            
            # 통계 출력
            stats = db.get_statistics(CODE, 1)  # 오늘의 통계
            if stats:
                print("\n📈 오늘의 거래 통계:")
                print(f"  - 총 주문 횟수: {stats.get('total_orders', 0)}")
                print(f"  - 성공한 주문: {stats.get('successful_orders', 0)}")
                print(f"  - 매수 횟수: {stats.get('buy_count', 0)}")
                print(f"  - 매도 횟수: {stats.get('sell_count', 0)}")
                print(f"  - 총 거래금액: {stats.get('total_amount', 0):,}원")
            
        except Exception as e:
            print(f"❌ 종료 처리 중 오류: {e}")
        
        print("👋 자동매매 시스템 종료")

def show_menu():
    """메뉴 표시"""
    print("\n" + "=" * 50)
    print("🤖 자동매매 시스템")
    print("=" * 50)
    print("1. 자동매매 시작")
    print("2. 현재 상태 조회")
    print("3. 거래 내역 조회")
    print("4. 통계 조회")
    print("5. 로그 조회")
    print("6. 설정 변경")
    print("7. 데이터베이스 백업")
    print("8. 오래된 데이터 정리")
    print("0. 종료")
    print("=" * 50)

def show_current_status():
    """현재 상태 조회"""
    print("\n📊 현재 상태")
    print("-" * 30)
    
    try:
        # 현재 가격
        current_price = api.fetch_current_price(CODE)
        if current_price:
            print(f"현재가: {current_price:,}원")
        
        # 계좌 상태
        holding_qty = api.fetch_quantity(ACCOUNT, CODE)
        total_eval = api.fetch_eval(ACCOUNT)
        
        print(f"보유 수량: {holding_qty}주")
        if total_eval:
            print(f"총 평가금: {int(total_eval):,}원")
        
        # 최근 신호
        recent_signals = db.get_logs(limit=5)
        if recent_signals:
            print("\n최근 활동:")
            for log in recent_signals[:3]:
                print(f"  {log['timestamp']}: {log['message']}")
                
    except Exception as e:
        print(f"❌ 상태 조회 실패: {e}")

def show_trade_history():
    """거래 내역 조회"""
    print("\n📋 최근 거래 내역")
    print("-" * 30)
    
    orders = db.get_orders(CODE, 10)
    if orders:
        for order in orders:
            status_emoji = "✅" if order['status'] == 'SUCCESS' else "❌" if order['status'] == 'FAILED' else "⏳"
            print(f"{status_emoji} {order['timestamp'][:19]} | {order['order_type']} {order['quantity']}주 @ {order['price']:,}원")
    else:
        print("거래 내역이 없습니다.")

def show_statistics():
    """통계 조회"""
    print("\n📈 거래 통계")
    print("-" * 30)
    
    # 1일, 7일, 30일 통계
    for days in [1, 7, 30]:
        stats = db.get_statistics(CODE, days)
        print(f"\n최근 {days}일:")
        print(f"  총 주문: {stats.get('total_orders', 0)}회")
        print(f"  성공률: {stats.get('successful_orders', 0)}/{stats.get('total_orders', 0)}회")
        print(f"  매수: {stats.get('buy_count', 0)}회, 매도: {stats.get('sell_count', 0)}회")
        print(f"  총 거래금액: {stats.get('total_amount', 0):,}원")

def interactive_mode():
    """대화형 모드"""
    while True:
        show_menu()
        choice = input("\n선택하세요: ").strip()
        
        if choice == "1":
            main_trading_loop()
        elif choice == "2":
            show_current_status()
        elif choice == "3":
            show_trade_history()
        elif choice == "4":
            show_statistics()
        elif choice == "5":
            logs = db.get_logs(limit=20)
            print("\n📋 최근 로그")
            print("-" * 30)
            for log in logs:
                level_emoji = "🔴" if log['log_level'] == 'ERROR' else "🟡" if log['log_level'] == 'WARNING' else "🔵"
                print(f"{level_emoji} {log['timestamp'][:19]} | {log['message']}")
        elif choice == "6":
            print("⚙️ 설정 변경 기능은 추후 구현 예정입니다.")
        elif choice == "7":
            backup_path = db.backup_database()
            if backup_path:
                print(f"✅ 백업 완료: {backup_path}")
            else:
                print("❌ 백업 실패")
        elif choice == "8":
            if db.cleanup_old_data(90):
                print("✅ 90일 이전 데이터 정리 완료")
            else:
                print("❌ 데이터 정리 실패")
        elif choice == "0":
            print("👋 프로그램을 종료합니다.")
            break
        else:
            print("❌ 잘못된 선택입니다.")
        
        input("\nEnter를 눌러 계속...")

if __name__ == "__main__":
    try:
        interactive_mode()
    except Exception as e:
        print(f"💥 프로그램 오류: {e}")
        db.log_error(f"프로그램 오류: {e}")
    finally:
        db.close()