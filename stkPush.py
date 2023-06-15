import requests
from authToken import get_auth

url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
headers = {
  'Content-Type': 'application/json',
  'Authorization': 'Bearer ' + get_auth(),
}


def make_pay(payload):
    """push pay to mpesa"""
    r = requests.post(url, headers=headers, json=payload)
    return r.json()
