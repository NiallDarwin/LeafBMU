#!/usr/bin/python3
#
## Copyright 2018-2019 Mark Hornby
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
##    http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.

import os, logging, time, csv
from datetime import datetime

bmu_log = logging.getLogger('bmu_logger')

csv_dir = '/media/pi'
csv_filename = '/media/pi/BATMON1/bmu_data.csv'

fieldnames = ['timestamp', 'relay1', 'relay2', 'relay3', 'voltage', 'hx', 'soc', 'capacity', 'soh', 't1', 't2', 't3', 't4']
for i in range(96):
	fieldnames.append('cell%d' % (i+1)) # Add cell voltage columns

# Check file path, update path with first usb drive name
def usb_drive_exists():
	global csv_filename
	if os.path.isdir(csv_dir):
		for entry in os.scandir(csv_dir):
			if entry.is_dir() and os.access(csv_dir+'/'+entry.name,os.W_OK):
				csv_filename = csv_dir+'/'+entry.name+'/'+'batmon_data.csv'
				bmu_log.info('CSV Filepath changed to: ' + csv_filename)
			else:
				bmu_log.info(entry.name + ' is not a directory or is not writable')
	else:
		# no mount point, no usb drive 
		bmu_log.error('No USB drives detected, unable to log data.')
		time.sleep(1)
	return None

# Log battery data to csv file
def log_to_csv(bat_data):
	bat_data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
	#if 'relay1' not in bat_data:
	#	bat_data['relay1'] = int(RELAY_1.is_pressed)
	#	bat_data['relay2'] = int(RELAY_2.is_pressed)
	#	bat_data['relay3'] = int(RELAY_3.is_pressed)
	exists = os.path.isfile(csv_filename)
	try:
		with open(csv_filename, 'a') as f:
			writer = csv.DictWriter(f, fieldnames=fieldnames)
			if not exists:
				writer.writeheader()
			writer.writerow(bat_data)
	except FileNotFoundError:
		usb_drive_exists()
	except OSError:
		bmu_log.error('Error while attempting to log to csv file.')
		usb_drive_exists()