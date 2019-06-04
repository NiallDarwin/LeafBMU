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

# PiBMU Checks module alpha_01

import logging, time

import bmu_gpio

bmu_log = logging.getLogger('bmu_logger')

MAX_CELL_WARN = 4.1
MIN_CELL_WARN = 3.3
DELTA_CELL_WARN = 0.01
MIN_TEMP_WARN = 3
MAX_TEMP_WARN = 40

MAX_CELL_CRIT = 4.15
MIN_CELL_CRIT = 3.00
DELTA_CELL_CRIT = 0.1
MIN_TEMP_CRIT = 2
MAX_TEMP_CRIT = 50

v_max_ok = False
v_min_ok = False
v_delta_ok = False
t_max_ok = False
t_min_ok = False

# 
contactors_closed = False

# Control from external system 
turn_hv_on =  False # True

# Is the battery status within safe limits
batttery_status_ok = False

def check_warnings(**kwargs):
	global turn_hv_on
	global v_max_ok
	global v_min_ok
	global v_delta_ok
	global t_max_ok
	global t_min_ok

	# Max cell voltage
	if 'v_max' in kwargs:
		v_max_ok = check_max(
				kwargs['v_max'],
				MAX_CELL_WARN,
				MAX_CELL_CRIT,
				'v_max')
		bmu_log.debug('v_max_ok: %s' % (v_max_ok))

	# Min cell voltage 
	if 'v_min' in kwargs:
		v_min_ok = check_min(
				kwargs['v_min'],
				MIN_CELL_WARN,
				MIN_CELL_CRIT,
				'v_min')
		bmu_log.debug('v_min_ok: %s' % (v_min_ok))

	# Cell voltage 'spread'
	if 'v_delta' in kwargs:
		v_delta_ok = check_max(
				kwargs['v_delta'],
				DELTA_CELL_WARN,
				DELTA_CELL_CRIT,
				'v_delta')
		bmu_log.debug('v_delta_ok: %s' % (v_delta_ok))

	# Min Temp
	if 't_min' in kwargs:
		t_min_ok = check_min(
				kwargs['t_min'],
				MIN_TEMP_WARN,
				MIN_TEMP_CRIT,
				't_min')
		bmu_log.debug('t_min_ok: %s' % (t_min_ok))

	# Max Temp
	if 't_max' in kwargs:
		t_max_ok = check_max(
				kwargs['t_max'],
				MAX_TEMP_WARN,
				MAX_TEMP_CRIT,
				't_max')
		bmu_log.debug('t_max_ok: %s' % (t_max_ok))

	#bmu_log.debug('%s %s %s %s %s %s' % (v_max_ok, v_min_ok, v_delta_ok, t_max_ok, t_min_ok, turn_hv_on))

def check_min(value,warn,crit,msg):
	bmu_log.info('Checking %s: %.3f %.3f %.3f' % (msg, value, warn, crit))
	if value <= warn:
		if value <= crit:
			bmu_log.critical('%s at critical limit (%.3f) at %.3f' % (msg, crit, value))
			# bmu_gpio.contactor_shutdown()
			return False
		else:
			bmu_log.warning('%s outside limit (%.3f) at %.3f' % (msg, warn, value))
			return True
	else:
		return True

def check_max(value,warn,crit,msg):
	bmu_log.info('Checking %s: %.3f %.3f %.3f' % (msg, value, warn, crit))
	if value >= warn:
		if value >= crit:
			bmu_log.critical('%s at critical limit (%.3f) at %.3f' % (msg, crit, value))
			# bmu_gpio.contactor_shutdown()
			return False
		else:
			bmu_log.warning('%s outside limit (%.3f) at %.3f' % (msg, warn, value))
			return True
	else:
		return True

def contactor_controller():
	global contactors_closed
	try:
		while True:
			# 'turn_hv_on' is the external control signal
			if turn_hv_on:
				# HV should be on or needs to be turned on
				# check operating limits
				if (v_max_ok and v_min_ok and v_delta_ok and t_max_ok and t_min_ok):
					# Operating limits are ok
					# Check contactors state, start up if required
					if not contactors_closed:
						# Contactor are open/off
						bmu_gpio.contactor_startup()
						contactors_closed = True
					else:
						# Contactors are closed/on
						# No action required
						pass
				else:
					# Cell voltage(s) and/or temperatures outside operating limits!
					# Check High Voltage contactors 
					if contactors_closed:
						# HV contactors are closed/on
						# Turn off HV
						bmu_gpio.power_led_status(-1)
						msg = 'Cell voltage(s) and/or temperatures outside safe operating range!\nHV contactors will open in 2 seconds'
						bmu_log.warning(msg)
						time.sleep(2)
						bmu_gpio.contactor_shutdown()
						contactors_closed = False

			else:
				# HV should be off
				# check contactors
				if contactors_closed:
					# Contactors are closed/on
					# Turn off HV
					msg = 'Shutdown instruction received from controller!\nHV contactors will open in 2 seconds'
					bmu_log.warning(msg)
					time.sleep(2)
					bmu_gpio.contactor_shutdown()
					contactors_closed = False
				else:
					# Contactors are open/off
					# Wait for the turn on signal from controller
					while not turn_hv_on:
						time.sleep(1)

	except Exception:
		bmu_log.exception('Exception raised in contactor controller thread')
	finally:
		# TODO emergency contactor shutdown
		print("Contactors emergency depowered")
		bmu_gpio.contactor_shutdown()