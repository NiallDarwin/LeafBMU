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

# PiBMU Control alpha_01
import logging, os, time, can, queue, math
from logging.handlers import RotatingFileHandler
from threading import Thread

# import local modules
import can_data, data_to_csv, limit_checks, bmu_gpio

VERSION = '1'

# Setup logging
log_level = logging.INFO #DEBUG #INFO #WARNING
log_filename = 'reb_bmu.log'
log_formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')

log_handler = RotatingFileHandler(log_filename, maxBytes=1024*1024, backupCount=2)
log_handler.setFormatter(log_formatter)
log_handler.setLevel(log_level)

bmu_log = logging.getLogger('bmu_logger')
bmu_log.setLevel(log_level)
bmu_log.addHandler(log_handler)

bmu_log.info('Starting PiBMU version: %s' % (VERSION))

# Thread monitoring battery operating limits
cc = Thread(target=limit_checks.contactor_controller)
cc.start()

# Check for usb drive and update filepath for logging
data_to_csv.usb_drive_exists()

# CAN message values
PID_REQUEST = 0x79B
PID_REPLY   = 0x7BB
PID_BAT_VA = 0x1DB

GROUP_1 = 0x01 # 6 lines, SOC, Ah, SOH etc
GROUP_2 = 0x02 # 29 lines, Cell voltages.
GROUP_3 = 0x03 # 5 lines, Vmin and Vmax
GROUP_4 = 0x04 # 3 lines, Pack temperatures.

# Connect to CAN interface
bmu_log.info('Bring up can1 interface...')
os.system("sudo /sbin/ip link set can1 up type can bitrate 500000")
time.sleep(0.2)
bmu_log.info('CAN interface ready')

try:
	bus = can.interface.Bus(channel='can1', bustype='socketcan')
except OSError:
	bmu_log.error('PiCAN board not detected.')
	exit()
time.sleep(0.2)


# CAN BUS request message thread
def request_data_group(group):
	msg_data = [0x02, 0x21, group, 0x00, 0x00, 0x00, 0x00, 0x00]
	msg = can.Message(arbitration_id=PID_REQUEST, data=msg_data, extended_id=False)
	bus.send(msg)
	bmu_log.debug('Request sent for data group: %d' % group)

# CAN BUS message receive thread
def can_rx_task():
	while True:
		can_msg = bus.recv()
		if can_msg.arbitration_id == PID_BAT_VA:
			can_data.data1DB(can_msg.data)

		if can_msg.arbitration_id != PID_REPLY:
			str_data = ' '.join(format(b, '02X') for b in can_msg.data)
			if can_msg.arbitration_id == PID_REQUEST:
				if can_msg.data[0] != 0x30:
					bmu_log.info('Request data group %d: %02X %s' % (
							can_msg.data[2],
							can_msg.arbitration_id, str_data
							))
			else:
				bmu_log.debug("Unrecognised CAN message: %02X %s" % (
						can_msg.arbitration_id,
						str_data
						))
		else:
			q.put(can_msg)


# Setup for receive thread and message queue
q = queue.Queue()
rx = Thread(target=can_rx_task)
rx.start()

# Main loop
try:
	while True:
		try:
			can_msg = q.get(True,0.5)

			if can_msg.data[0] != 0x10:
				bmu_log.error('CAN message out of sequence: %02X %s' % (
						can_msg.arbitration_id, 
						can_data.bytearray_to_str(can_msg.data)
						)
				) 
			else:

				msg_data = [0x30, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
				msg = can.Message(arbitration_id=PID_REQUEST, data=msg_data, extended_id=False)
				bus.send(msg)

				group_data = can_msg.data[1:8]
				msgs_expected = math.ceil((int(group_data[0])+1)/7)
				bmu_log.debug("Expecting %d" % (msgs_expected))

				for _ in range(msgs_expected-1):
					can_msg = q.get()
					# TODO check msg sequence numbers
					for x in range(1, 8):
						group_data.append(can_msg.data[x])

				if msgs_expected == 6:
					# General data
					can_data.group1(group_data)
					time.sleep(0.2)
					request_data_group(GROUP_2)

				elif msgs_expected == 29:
					# Cell voltages
					can_data.group2(group_data)
					time.sleep(0.2)
					request_data_group(GROUP_3)

				elif msgs_expected == 5:
					# Vmin and Vmax
					can_data.group3(group_data)
					time.sleep(0.2)
					request_data_group(GROUP_4)

				elif msgs_expected == 3:
					# Pack temperatures
					can_data.group4(group_data)
					time.sleep(0.2)
					request_data_group(GROUP_1)

				else:
					bmu_log.error(
						"Unrecognised data group length %d - %s" % 
						(msgs_expected, can_data.bytearray_to_str(group_data))
					)

				# format byte array and output to stdout
				byte_str = ""
				for x in range(len(group_data)):
					value = format(group_data[x],'02x')
					if x%7 != 6:
						byte_str = byte_str + value + ' '
					else:
						byte_str = byte_str + value + '\n'
				bmu_log.debug('\n'+byte_str)
				
		except queue.Empty:
			print("Get CAN msg timed out...retrying")
			time.sleep(0.2)
			request_data_group(GROUP_1)

except KeyboardInterrupt:
	bmu_log.info("Program terminated by keyboard interupt")

except Exception:
	bmu_log.exception("Unexpected error in main loop")

finally:
	bmu_log.info("Cleaning up control")
	limit_checks.turn_hv_on = False
	rx.join()
	cc.join()
	exit()
