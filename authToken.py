import base64
import requests
from os import getenv


def get_auth():
    """retrieve the authorization token"""
    url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?\
grant_type=client_credentials'
    token = '{}:{}'.format(getenv('CK'), getenv('CS'))
    token = base64.b64encode(token.encode('utf8')).decode()
    response = requests.get(url, headers={'Authorization': 'Basic ' + token})
    return response.json().get('access_token')
