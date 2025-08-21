from dotenv import load_dotenv
import os

load_dotenv()
import requests
from datetime import datetime

BASE_URL = "https://openapi.koreainvestment.com:9443"
ACCOUNT = os.environ["ACCOUNT"]
APPKEY = os.environ["APPKEY"]
APPSECRET = os.environ["APPSECRET"]
ACCESS_TOKEN = os.environ["ACCESS_TOKEN"]

def fetch_current_price(code):
    url = f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price"
    headers = {
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appkey": APPKEY,
        "appsecret": APPSECRET,
        "tr_id": "FHKST01010100"
    }
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": code
    }
    res = requests.get(url, headers=headers, params=params)
    try:
        data = res.json()
        return int(data["output"]["stck_prpr"])
    except Exception as e:
        print(e)
        return None

def fetch_orders(account, code):
    today = datetime.today().strftime('%Y%m%d')
    url = f"{BASE_URL}/uapi/domestic-stock/v1/trading/inquire-daily-ccld"
    headers = {
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appkey": APPKEY,
        "appsecret": APPSECRET,
        "tr_id": "TTTC0081R"
    }
    params = {
        "CANO": account[:8],
        "ACNT_PRDT_CD": account[-2:],
        "INQR_STRT_DT": today,
        "INQR_END_DT": today,
        "SLL_BUY_DVSN_CD": "00",
        "INQR_DVSN": "00",
        "PDNO": code,
        "CCLD_DVSN": "02",  # 미체결
        "ORD_GNO_BRNO": "",
        "ODNO": "",
        "INQR_DVSN_3": "00",
        "INQR_DVSN_1": "",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": ""
    }

    try:
        res = requests.get(url, headers=headers, params=params)
        data = res.json()
        return data["output1"]
    except Exception as e:
        print(e)
        return []

def cancel_order(account, order_no):
    url = f"{BASE_URL}/uapi/domestic-stock/v1/trading/order-rvsecncl"
    headers = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appkey": APPKEY,
        "appsecret": APPSECRET,
        "tr_id": "TTTC0013U"
    }
    body = {
        "CANO": account[:8],
        "ACNT_PRDT_CD": account[-2:],
        "KRX_FWDG_ORD_ORGNO": "",
        "ORGN_ODNO": order_no,
        "ORD_DVSN": "00",
        "RVSE_CNCL_DVSN_CD": "02",  # 취소
        "ORD_QTY": "0",  # 잔량전부 취소
        "ORD_UNPR": "0",  # 취소
        "QTY_ALL_ORD_YN": "Y",  # 잔량 전부
    }

    try:
        res = requests.post(url, headers=headers, json=body)
        data = res.json()
        return data["rt_cd"] == "0"
    except Exception as e:
        print(e)
        return False

def clear_orders(account, code):
    orders = fetch_orders(account, code)
    for order in orders:
        order_no = order["odno"]
        result = cancel_order(account, order_no)
        print(f"{order_no} 취소 성공" if result else f"{order_no} 취소 실패")

def fetch_avail(account, code, target_price):
    url = f"{BASE_URL}/uapi/domestic-stock/v1/trading/inquire-psbl-order"
    headers = {
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appkey": APPKEY,
        "appsecret": APPSECRET,
        "tr_id": "TTTC8908R"
    }
    params = {
        "CANO": account[:8],
        "ACNT_PRDT_CD": account[-2:],
        "PDNO": code,
        "ORD_UNPR": str(target_price),
        "ORD_DVSN": "00",  # 지정가
        "CMA_EVLU_AMT_ICLD_YN": "N",
        "OVRS_ICLD_YN": "N",
    }
    try:
        res = requests.get(url, headers=headers, params=params)
        data = res.json()
        return data["output"]["nrcvb_buy_qty"]  # 미수 없는 매수 가능 수량
    except Exception as e:
        print(e)
        return 0

def fetch_quantity(account, code):
    url = f"{BASE_URL}/uapi/domestic-stock/v1/trading/inquire-balance"
    headers = {
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appkey": APPKEY,
        "appsecret": APPSECRET,
        "tr_id": "TTTC8434R"  # 주식 잔고 조회
    }
    params = {
        "CANO": account[:8],
        "ACNT_PRDT_CD": account[-2:],
        "AFHR_FLPR_YN": "N",
        "INQR_DVSN": "02",  # 종목별
        "UNPR_DVSN": "01",  # 단가 구분 기본값
        "FUND_STTL_ICLD_YN": "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN": "00",  # 전일 매매 포함
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": ""
    }

    try:
        res = requests.get(url, headers=headers, params=params)
        data = res.json()
        for item in data["output1"]:
            if item["pdno"] == code:
                return item["hldg_qty"]
        return 0
    except Exception as e:
        print(e)
        return 0

def order(order_type, account, code, amount, target_price):
    url = f"{BASE_URL}/uapi/domestic-stock/v1/trading/order-cash"
    headers = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appkey": APPKEY,
        "appsecret": APPSECRET,
        "tr_id": "TTTC0012U" if order_type == "BUY" else "TTTC0011U"  # 주식 현금 매수/매도 주문
    }
    body = {
        "CANO": account[:8],
        "ACNT_PRDT_CD": account[-2:],
        "PDNO": code,
        "ORD_DVSN": "00",  # 지정가
        "ORD_QTY": str(amount),
        "ORD_UNPR": str(target_price)
    }

    try:
        res = requests.post(url, headers=headers, json=body)
        data = res.json()
        return data["rt_cd"] == "0"
    except Exception as e:
        print(e)
        return False

def fetch_eval(account):
    url = f"{BASE_URL}/uapi/domestic-stock/v1/trading/inquire-balance"
    headers = {
        "authorization": f"Bearer {ACCESS_TOKEN}",
        "appkey": APPKEY,
        "appsecret": APPSECRET,
        "tr_id": "TTTC8434R"  # 주식 잔고 조회
    }
    params = {
        "CANO": account[:8],
        "ACNT_PRDT_CD": account[-2:],
        "AFHR_FLPR_YN": "N",
        "OFL_YN": "",  # 공란
        "INQR_DVSN": "02",  # 종목별
        "UNPR_DVSN": "01",  # 단가 구분 기본값
        "FUND_STTL_ICLD_YN": "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN": "00",  # 전일 매매 포함
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": ""
    }

    try:
        res = requests.get(url, headers=headers, params=params)
        data = res.json()
        print(data)
        return data["output2"][0]["tot_evlu_amt"]
    except Exception as e:
        print(e)
        return None

