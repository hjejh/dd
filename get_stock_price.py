import requests

BASE_URL = "https://openapi.koreainvestment.com:9443"
APPKEY = "PS2QwTtUZ4Okjl0WdAeYdFtLOzWEonCCRVEv"
APPSECRET = "aEj1vNnd4ankdePa2QTM7btsuK17xsogN5SWbKYNSxoFVNXQa9ymFivMJodDJ7uNEWJTe+YVWCteIT2YAGMYL+fH5bTVDjx95ZQW/YDEpnllmyccjUyT+ArtogBY9ZMPzt9cQlkd4IXWHh5N5VvnPESvlPP57lDFaymFDFqUvlOj/4DwDR8="

ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJ0b2tlbiIsImF1ZCI6ImRiZTNjMWYwLWUxZTgtNDQzZC1iOGNjLTQyOWQ3ZjA5NjEyZCIsInByZHRfY2QiOiIiLCJpc3MiOiJ1bm9ndyIsImV4cCI6MTc1NDk2NjAxNCwiaWF0IjoxNzU0ODc5NjE0LCJqdGkiOiJQUzJRd1R0VVo0T2tqbDBXZEFlWWRGdExPeldFb25DQ1JWRXYifQ.IVPODySbOUpEM6tsewG4hfDFP-mSzItRExIw8gf7xMhv7eu3i_DSTcgq9sOqR2ut6i0sm-WtaY6koQgVpvioNw"

url = f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice"
headers = {
    "content-type": "application/json; charset=utf-8",
    "authorization": f"Bearer {ACCESS_TOKEN}",
    "appkey": APPKEY,
    "appsecret": APPSECRET,
    "tr_id": "FHKST03010200",
    "custtype": "P"
}
params = {
    "FID_ETC_CLS_CODE": "",
    "FID_COND_MRKT_DIV_CODE": "J",
    "FID_INPUT_ISCD": "122640", 
    "FID_INPUT_HOUR_1": "093000",
    "FID_PW_DATA_INCU_YN": "Y"
}
try:
    res = requests.get(url, headers=headers, params=params)
    data = res.json()
    print(data["output1"]["hts_kor_isnm"])  # HTS 한글 종목명
    for item in data["output2"]:
        print(f"시간: {item['stck_bsop_date']} {item['stck_cntg_hour']} 가격:{item['stck_prpr']}")
except Exception as e:
    print(e)

