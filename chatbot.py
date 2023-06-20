#!/usr/bin/env python3
"""chatbot module for whatsapp main app
"""
import base64
import os
from datetime import datetime as dt
from flask import Flask, request, session
from twilio.rest import Client
from stkPush import make_pay
from schools import schools

# variables for mpesa payload
ts = dt.now().strftime("%Y%m%d%H%M%S")
# Practice sandbox passkey
pk = 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'
pw = base64.b64encode(f'{174379}{pk}{ts}'.encode('utf-8')).decode()
payload = {
  "BusinessShortCode": 174379,
  "Password": pw,
  "Timestamp": ts,
  "TransactionType": "CustomerPayBillOnline",
  "Amount": "1",
  "PartyA": 254708374149,  # user phone number
  "PartyB": 174379,
  "PhoneNumber": 254708374149,  # receives prompt
  "CallBackURL": "https://lipa-fees.onrender.com/results",
  "AccountReference": "Payx",  # school code
  "TransactionDesc": "lets test this out"  # student number
}

# setup the twilio client
client = Client(os.getenv('ACCOUNT_SID'), os.getenv('AUTH_TOKEN'))

app = Flask(__name__)
app.secret_key = os.getenv('SK')

start = 'Welcome to Lipa Fees\n\
Replace the text in UPPER with actual values\n\
Reply "/search SCH-FIRSTNAME"'


@app.route('/test')
def hello():
    """checks if service is running"""
    return '', 200


@app.route('/lipafees', methods=['POST'])
def main():
    """Main entry point for chatbot"""
    commands = {
        '/start': start,
        '/search': get_school,
        '/code': set_payload,
        '/pay': confirm,
    }
    if request.method == 'POST':
        session['user'] = request.values.get('From')
        cmd = request.values.get('Body').split(' ')
        cmd1 = cmd[0].lower()
        if cmd1 not in list(commands.keys()):
            body = f'Hi {request.values.get("ProfileName")},\nReply with\
"/start" to initiate payment'
        elif cmd1 == '/start':
            body = commands['/start']
        else:
            body = commands.get(cmd1)(cmd)
        sendSMS(session['user'], body)
    return 'success'


@app.route('/results', methods=['GET', 'POST'])
def callback():
    """return user response"""
    print('received response')
    resp = request.get_json(force=True)['Body']['stkCallback']
    if resp['ResultCode'] == 0:
        items = resp['CallbackMetadata']['Item']
        body = 'Transaction Success\nMpesaReceiptNumber: {}\n\
Amount: {}\n'.format(items[1]['Value'], items[0]['Value'])
    else:
        body = 'Error: ' + resp['ResultDesc']
        return body
    sendSMS(session['user'], body)
    del session['user']
    return 'success update'


def sendSMS(recipient, body):
    client.messages.create(
        from_='whatsapp:+14155238886',
        body=body,
        to=recipient
    )


def get_school(data):
    """return list of schools that start with start"""
    if len(data) != 2:
        return 'Reply with\n"/search SCHOOL-FIRSTNAME"'
    choice = data[1].upper()
    mydata = ''
    if choice[0] in list(schools.keys()):
        for school, code in schools.get(choice[0]).items():
            if choice in school:
                mydata += '{}\n code = {}\n'.format(school, str(code))
    if mydata == '':
        return 'No results found for {}.\
\nReply with\n"/search SCHOOL-FIRSTNAME"'.format(choice)
    mydata += 'Reply with:\n"/code CODE STUDENTNUMBER AMOUNT"'
    return mydata


def set_payload(ref):
    """update payload"""
    if len(ref) != 4:
        return 'Reply with:\n"/code CODE STUDENTNUMBER AMOUNT"'
    payload['PartyA'] = payload['PhoneNumber'] = int(request.values.get('From')
                                                     [10:])
    payload['AccountReference'] = ref[1]
    payload['TransactionDesc'] = ref[2]
    payload['Amount'] = ref[3]

    return 'Reply:\n"/pay 1" to pay with this whatsapp number\n\
"/pay 254xxxxxxxxx" to use another number'


def confirm(ref):
    """calls the stk prompt"""
    if len(ref) != 2:
        return 'Reply:\n"/pay 1" to pay with this whatsapp number\n\
"/pay 254xxxxxxxxx" to use another number'
    if ref[1] != '1':
        payload['PhoneNumber'] = payload['PartyA'] = ref[1]
    resp = make_pay(payload)
    if resp.get('ResponseCode') == '0':
        return resp.get('CustomerMessage')
    return 'Error: {}'.format(resp.get('errorMessage'))
