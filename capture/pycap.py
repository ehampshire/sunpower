#!/usr/bin/python
# -*- coding: utf-8 -*-

import pcapy, re, sys, requests
from impacket.ImpactDecoder import *

#
# Configuration
#

HOME_ASSISTANT_LONG_LIVED_API_KEY = "ABCDEFG"
HOME_ASSISTANT_URL = "http://192.168.1.20:8123"
SUNPOWER_PORTAL_IP = "34.208.188.187" # I doubt this will change often, but my IP was different from @ehampshire's. Best to check this with wireshark
DEVICE = "eth0"

#
#
#

# Constants
regex = re.compile(r'^([0-9]+)\t')
head = {'Authorization': 'Bearer ' + HOME_ASSISTANT_LONG_LIVED_API_KEY}
maxBytes = 100000
promiscuous = True
readTimeout = 1000 # in milliseconds

# Globals
lastProduction = None
lastActualProduction = None
lastConsumption = None

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def http_post(url, data):
    post = urlencode(data)
    req = urllib2.Request(url, post)
    response = urllib2.urlopen(req)
    return response.read()

def parseAndPostData(msg):
	global lastProduction, lastConsumption

	if (msg[0] == "130"):
		currentProduction = float(msg[4])

		if lastProduction:
			actualProduction = currentProduction - lastProduction
			print('\tActual Production (kWh): %.2f\n' % actualProduction)
			response = requests.post(HOME_ASSISTANT_URL + "/api/states/sensor.power_production", json={"state": round(actualProduction, 3), "attributes": { "friendly_name": "Power Production", "unit_of_measurement": "kW", "icon": "hass:solar-power" }}, headers=head)
			print('\tResponse: %s\n' % response.json())
			lastActualProduction = actualProduction

		lastProduction = currentProduction

		# Post temperature
		response = requests.post(HOME_ASSISTANT_URL + "/api/states/sensor.inverter_temperature", json={"state": float(msg[10]), "attributes": { "friendly_name": "Inverter Temperature", "unit_of_measurement": "°C", "icon": "hass:thermometer" }}, headers=head)
		print('\tTemperature Response: %s\n' % response.json())

	elif (msg[0] == "131"):
		currentConsumption = float(msg[5])

		if lastActualProduction and lastConsumption:
			actualConsumption = currentConsumption - lastConsumption + lastActualProduction
			print('\tActual Consumption (kWh): %.2f\n' % actualConsumption)
			response = requests.post(HOME_ASSISTANT_URL + "/api/states/sensor.power_consumption", json={"state": round(actualConsumption, 3), "attributes": { "friendly_name": "Power Consumption", "unit_of_measurement": "kW", "icon": "hass:power-plug" }}, headers=head)
			print('\tResponse: %s\n' % response.json())

		lastConsumption = currentConsumption

# callback for received packets
def recv_pkts(hdr, data):
	global regex

	line_list = EthDecoder().decode(data).child().child().get_data_as_string().split('\n')
	for line in line_list:
		if not line:
	   		continue

		if regex.match(line) or len(line.strip()) > 0:
			msg = line.split()

			# Ignore empty, header, or control messages
			if (len(msg) < 1 or not is_number(msg[0]) or msg[0] == "100" or msg[0] == "102" or msg[0] == "1002" or msg[0] == "120"):
			   continue

			if(msg[0] == "130"):
				print("production message (130): ")
			elif(msg[0] == "131"):
				print("net metering message (131): ")
			else:
				print("unmatched message: ")

			print('\t%s' % msg)

			if(msg[0] == "130" or msg[0] == "131"):
				try:
					parseAndPostData(msg)
				except Exception as e:
					print("Failed to parse message, stumbled on exception: \n%s" % e)

if __name__ == "__main__":
	pc = pcapy.open_live(DEVICE, maxBytes, promiscuous, readTimeout)
	pc.setfilter("ip && tcp")
	sys.exit(pc.loop(-1, recv_pkts)) # capture packets
