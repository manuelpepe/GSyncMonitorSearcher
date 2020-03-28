#!/usr/bin/python3
import re
import json
import smtplib
import requests

from os.path import isdir
from bs4 import BeautifulSoup
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import *


HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'}
SAVE_FILE = 'monitors.txt'


def get_data_url():
	""" Finds the JSON url from which the page loads the monitor data. The current url has a timestamp so it's likely to change. """
	url = 'https://www.nvidia.com/en-us/geforce/products/g-sync-monitors/specs/'
	page = requests.get(url, headers=HEADERS)
	soup = BeautifulSoup(page.text, 'html.parser')
	for script in soup.find_all('script'):
		if script.text and 'g-sync-monitors-specs' in script.text:
			match = re.search('/content/.*\.json', script.text)
			return f'https://www.nvidia.com{match.group(0)}'


def get_monitors(url):
	""" Returns generator with monitor IDs (<manufacturer>_<model>). """
	page = requests.get(url, headers=HEADERS)
	data = json.loads(page.text)
	return [f"{row['manufacturer']} {row['model']}" for row in data['data']]

def compare_monitors(newmons):
	""" Compares new monitors with last run and returns difference. """
	try:
		with open(SAVE_FILE, 'r') as f:
			oldmons = [l.strip() for l in f.readlines()]
	except FileNotFoundError:
		oldmons = []

	return set(newmons) - set(oldmons)

def save_monitors(monitors):
	with open(SAVE_FILE, 'w') as f:
		f.write('\n'.join(monitors))

def send_email(diff):
	mons = "Found new G-Sync monitors:\n\n"
	mons += '\n'.join(diff)
	print(mons)

	s = smtplib.SMTP(host=EMAIL_HOST, port=EMAIL_PORT)
	s.starttls()
	s.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

	msg = MIMEMultipart()
	msg['From']=EMAIL_ADDRESS
	msg['To']=EMAIL_TARGET
	msg['Subject']="New G-Sync Monitors"
	msg.attach(MIMEText(mons, 'plain'))

	s.send_message(msg)
	del msg


def main():
	url = get_data_url()
	newmons = [m.strip() for m in get_monitors(url)]
	diff = compare_monitors(newmons)
	if diff:
		send_email(diff)
	save_monitors(newmons)

if __name__ == '__main__':
	main()