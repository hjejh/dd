import requests

BASE_URL = "https://openapi.koreainvestment.com:9443"
APPKEY = "PS2QwTtUZ4Okjl0WdAeYdFtLOzWEonCCRVEv"
APPSECRET = "aEj1vNnd4ankdePa2QTM7btsuK17xsogN5SWbKYNSxoFVNXQa9ymFivMJodDJ7uNEWJTe+YVWCteIT2YAGMYL+fH5bTVDjx95ZQW/YDEpnllmyccjUyT+ArtogBY9ZMPzt9cQlkd4IXWHh5N5VvnPESvlPP57lDFaymFDFqUvlOj/4DwDR8="

url = f"{BASE_URL}/oauth2/tokenP"
headers = {
    "Content-Type": "application/json"
}
body = {
    "grant_type": "client_credentials",
    "appkey": APPKEY,
    "appsecret": APPSECRET
}
try:
    res = requests.post(url, headers=headers, json=body)
    data = res.json()
    print(data)
except Exception as e:
    print(e)
