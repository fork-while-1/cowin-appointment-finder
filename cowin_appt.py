#!/usr/bin/env python

import requests, json, hashlib, subprocess, time, sys
# uncomment for OTP scraping
# import pandas as pd
# import sqlite3
from datetime import date
from collections import OrderedDict

# ######### BEGIN USER CONFIG ############

# Can be 18 or 45
MIN_AGE = 18

DOSE_NUMBER = 1

# phone number associated with account
MOBILE = 9876543210

# reference ID of person to be vaccinated
REFERENCE_ID = 0

# pincodes of hospitals to search
PINCODES = [400056, 400076, 400004, 400059]

# name of browser to show captcha in (e.g.: firefox, google-chrome)
BROWSER = "start chrome"

# keep at 0 if you'll manually enter OTP
# set to 1 if you have your Mac synced with your Iphone (NOT IMPLEMENTED YET)
AUTO_OTP = 0

NUM_TRIES = 1000

CAPTCHA_PATH = "C:\\Users\\name\Downloads\\tmp.html"
# ######### END USER CONFIG ############

bearer_token = ""

SLEEP_INTERVAL = 90

URL_BASE = "https://cdn-api.co-vin.in/api/v2/"


def scrape_otp_message(icloud_name):
	# NOT IMPLEMENTED
	# base source code from: https://medium.com/analytics-vidhya/how-to-login-to-websites-requiring-otp-text-message-using-python-65f435c8b4f6
	
    conn = sqlite3.connect("/Users/{0}/Library/Messages/chat.db".format(icloud_name))

    messages = pd.read_sql_query("select * from message order by ROWID desc limit 1", conn)
    handles = pd.read_sql_query("select * from handle order by ROWID desc limit 1", conn)

    messages.rename(columns={'ROWID': 'message_id'}, inplace=True)
    handles.rename(columns={'id': 'phone_number', 'ROWID': 'handle_id'}, inplace=True)
    imessage_df = pd.merge(messages[['text', 'handle_id', 'date', 'is_sent', 'message_id']],
                           handles[['handle_id', 'phone_number']], on='handle_id', how='left')

    for index, row in imessage_df.iterrows():
        if row['handle_id'] == HANDLE_ID:
            verification_code_text = row['text']
            return verification_code_text
        else:
            print("verification code not found")
            return None

    return "Some error occurred"


def send_req(endpoint,payload=None):
	session = requests.Session()
	# we use a specefic order of headers because some websites use this as a heuristic to tell if you're
	# using a real browser or not (to discourage bots). This ordering worked so we're sticking to this
	session.headers = OrderedDict()
	session.headers["Host"] = "cdn-api.co-vin.in"
	session.headers["Accept-Encoding"] = "deflate, gzip, br"
	session.headers["authority"] = "cdn-api.co-vin.in"
	session.headers["pragma"] = "no-cache"
	session.headers["cache-control"] = "no-cache"
	session.headers["sec-ch-ua"] = '" Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"'
	session.headers["accept"] = "application/json, text/plain, */*"
	session.headers["authorization"] = bearer_token
	session.headers["sec-ch-ua-mobile"] =  "?0"
	session.headers["user-agent"] =  "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36'"
	session.headers["content-type"] =  "application/json"
	session.headers["origin"] =  "https://selfregistration.cowin.gov.in"
	session.headers["sec-fetch-site"] =  "cross-site"
	session.headers["sec-fetch-mode"] =  "cors"
	session.headers["sec-fetch-dest"] = "empty"
	session.headers["referer"] = "https://selfregistration.cowin.gov.in/"
	session.headers["accept-language"] =  "en-US,en;q=0.9"
	if payload == None:
		response = session.get(endpoint)
	else:
		response = session.post(endpoint, data = json.dumps(payload))
	if response.status_code == 401:
		print("Something went wrong: Unauthenticated")
		sys.exit(1)
	try:
		return json.loads(response.text)
	except:
		print(response.text)
		return {'error':'Unknown Error'}

def plot_captcha(captcha_img):
	template = "<!DOCTYPE html><html><body>{0}</body></html>"
	with open(CAPTCHA_PATH,'w') as fdesc:
		fdesc.write(template.format(captcha_img))
	proc = subprocess.Popen("{0} file://{1}".format(BROWSER,CAPTCHA_PATH), shell = True)
	return proc	

def authorize():
	endpoint = URL_BASE + "auth/generateMobileOTP"
	payload = {"secret" : "U2FsdGVkX18Atl3VKsQbmGVrYpEWYwC0lkb72Eq2yYA7tiQ0tIjRcXMvBq94SDvk5Frdp67HaYkW7q4SwBkteA==",
	        "mobile": MOBILE}

	txnId = send_req(endpoint,payload)["txnId"]

	if AUTO_OTP:
		otp = scrape_otp_message()
	else:
		print("Enter OTP:", end=' ')
		otp = input()
	
	otp_sha256 = hashlib.sha256(otp.encode()).hexdigest()

	endpoint = URL_BASE + "auth/validateMobileOtp"
	payload = {"otp" : otp_sha256,
                "txnId": txnId}
    
	bearer_token_resp = send_req(endpoint,payload)
	try:
		bearer_token = "Bearer " + bearer_token_resp["token"]
	except KeyError:
		print("Bearer token error: " + bearer_token_resp["error"])
		sys.exit(1)
	return bearer_token


def find_appointments():
	current_date = date.today()
	day = current_date.day
	month = current_date.month
	year = current_date.year
	endpoint = URL_BASE + "appointment/sessions/calendarByPin?pincode={0}" +  "&date={0:02d}-{1:02d}-{2}".format(day,month,year)

	for i in range(NUM_TRIES):
		print("Trying {0}th time ...".format(i))
		time.sleep(SLEEP_INTERVAL)
		index = 0
		available_slots = list()
		for pincode in PINCODES:
			endpoint = endpoint.format(pincode)
			centers_resp = send_req(endpoint)
			try:
				centers = centers_resp["centers"]
			except Exception as e:
				print("Something went wrong: " + centers_resp["error"])
				continue
			for center in centers:
				for session in center["sessions"]:
					if session["available_capacity"] != 0 and session["min_age_limit"] == MIN_AGE:
						print(center["name"])
						print(session["date"])
						for  slot in session["slots"]:
							print("\t{0}: {1}".format(index, slot))
							available_slots.append([center["center_id"],session["session_id"], slot])
							index += 1
		if len(available_slots):
			print("Enter slot ID to select, or n to skip:", end = ' ')	
			slot_id = int(input())
			if slot_id == 'n':
				continue
			endpoint = URL_BASE + "auth/getRecaptcha"
			payload = {}
			captcha_img_resp = send_req(endpoint,payload)
			try:
				captcha_img = captcha_img_resp["captcha"]
			except KeyError as e:
				print("Something went wrong, please try again")
				continue
			proc = plot_captcha(captcha_img)
			print("Enter captcha (case sensitive):", end=' ')
			captcha = input()
			endpoint = URL_BASE + "appointment/schedule"
			payload = {"center_id" : available_slots[slot_id][0],
			            "session_id" : available_slots[slot_id][1],
			            "beneficiaries" : [REFERENCE_ID],
			            "slot": available_slots[slot_id][2],
			            "captcha" : captcha,
			            "dose" : DOSE_NUMBER}
			appointment_conf = send_req(endpoint,payload)
			try:
				print("Success! Appointment Confirmation Number: " + appointment_conf["appointment_confirmation_no"])
				proc.kill()
				return
			except Exception as e:
				print("Something went wrong: " + appointment_conf["error"])
				proc.kill()
				continue

print(authorize())
find_appointments()
