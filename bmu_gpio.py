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

import logging, time
from gpiozero import LED
# Import local modules:
# No local modules

bmu_log = logging.getLogger('bmu_logger')

# Supply power status indicator LED
POWER_LED = LED(27) #27  / 26=LED on CAN board

def power_led_status(supply_voltage):
	if supply_voltage >=12:
		POWER_LED.on()
		bmu_log.info('Supply voltage: %.2f - Power LED on' % supply_voltage)
	elif supply_voltage == 0:
		POWER_LED.off()
		bmu_log.info('Supply voltage: %.2f - Power LED off' % supply_voltage)
	else:
		POWER_LED.blink(on_time=0.5,off_time=0.5)
		bmu_log.info('Supply voltage: %.2f - Power LED blinking' % supply_voltage)


# High voltage status indicator LED
HV_LED = LED(17) #17 / 4=LED on CAN board

def hv_led_status(status):
	if status ==0 :
		# Off=Initialising, contactors disconnected, HV battery off
		HV_LED.off() #
	elif status == 1:
		# On=Contactors connected, HV battery on
		HV_LED.on()
	else:
		# Blinking= Critical battery error, HV battery off
		HV_LED.blink(on_time=0.5,off_time=0.5)
		# TODO were does this need to be set?


# Relay 1, controls 12V to all contactor coil positives. When on HV- relay will energise
RELAY_NEG = LED(13)

# Relay 2, when off it connects the negative lead of the pre-charge relay to  ground.
# When on it disconnects the negative of the PC and and instead connects the negative of the HV+ contactor coil to ground.
RELAY_POS = LED(26)

def contactor_shutdown():

	bmu_log.info('Contactor shutdown initiated')
	RELAY_NEG.off()
	RELAY_POS.off()
	
	hv_led_status(0) # turn hv status led off
	bmu_log.info('Contactor shutdown complete')

def contactor_startup():

	bmu_log.info('Contactor startup initiated')

	RELAY_NEG.on()
	# TODO Check current(Amps)
	time.sleep(3) # This is blocking!
	RELAY_POS.on()

	hv_led_status(1) # turn hv status led on
	bmu_log.info('Contactor startup complete...Battery is LIVE')
