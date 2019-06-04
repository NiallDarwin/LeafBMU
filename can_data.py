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

# import local modules
import bmu_gpio, data_to_csv, limit_checks

# Utility functions
def bytearray_to_str(ba):
	return ' '.join(format(b, '02x') for b in ba)

def bytearray_to_int(ba):
	return int.from_bytes(ba, byteorder='big', signed=False)

# Extract Battery Voltage and Current
counter_1DB = 0
def data1DB(data):
	global counter_1DB
	if counter_1DB < 30:
		counter_1DB = counter_1DB + 1
	else:
		counter_1DB = 0

		# Amps Battery
		bA = bin(bytearray_to_int(data[0:2]))

		# Volts Battery
		bV = bin(bytearray_to_int(data[2:4]))

		print('%s %s %s' % (
				bytearray_to_str(data),
				int(str(bA).replace('b','').zfill(16)[:11],2)/2,
				int(str(bV).replace('b','').zfill(16)[:11],2)/2
				)
			)

		#Amps Batt		0x1db	1	10 / 11 bits? 1 LSB = 0.5A
		#Volts Batt	*10	0x1db	16	10 / 10 bits; 1 LSB = 0.5V

		# 00 24 C1 63 4C 00 03 05 0000000000100100  1100000101_100011
		# 00 44 c1 a3 4d 00 03 2a 0000000001000100  1100000110_100011
		# 00 64 C1 A2 D4 00 00 20 0000000001100100  1100000110_100011
		# 00 64 >> 00000000 01_100100
		# c1 A2 >> 11000001 10_100010


# Extract values from group 1 message data
def group1(data):
	# Total Voltage
	volt_total = bytearray_to_int(data[21:23])
	#bmu_log.debug('Total Voltage: %.3f V (%s)' % (volt_total['int']/100, volt_total['str']))
	print('G1 volts: %.2f' % (volt_total/100))

	# Acc Voltage
	volt_acc = bytearray_to_int(data[23:25])/1000
	#bmu_log.debug('Acc Voltage: %.3f V (%s)' % (volt_acc['int']/1024, volt_acc['str']))
	bmu_gpio.power_led_status(volt_acc)

	# Battery Health
	bat_health = bytearray_to_int(data[29:31])
	#bmu_log.debug('Battery Health: %.2f %% (%s)' % (bat_health['int']/100, bat_health['str']))
	#bmu_log.debug('Battery Health (Hx?): %.2f %%' % (bat_health['int']/1024*10))

	# SOC - State of Charge
	soc = bytearray_to_int(data[32:35])
	#bmu_log.debug('State of Charge (SOC): %.3f %% (%s)' % (soc['int']/10000, soc['str']))

	# Capacity (Ah)
	amp_hrs = bytearray_to_int(data[36:39])
	#bmu_log.debug('Capacity: %.3f Ah (%s)' % (amp_hrs['int']/10000, amp_hrs['str']))

	# SOH - State of Health
	#bmu_log.debug('SOH: %.3f %% (calc)' % (amp_hrs['int']/65.5/100))

	data_to_csv.log_to_csv({
		'voltage':volt_total/100,
		'hx':bat_health/1024*10,
		'soc':soc/10000,
		'capacity':amp_hrs/10000,
		'soh':amp_hrs/65.5/100
		})

# Cell voltages
def group2(data):
	cells = {}
	for x in range(0, 96):
		cell = int.from_bytes(
			data[3+(x*2):3+(x*2+2)],
			byteorder='big',
			signed=False)
		key = 'cell%d' % (x+1)
		cells[key] = cell/1000
	data_to_csv.log_to_csv(cells)

# Vmin and Vmax
def group3(data):
	vmax = bytearray_to_int(data[13:15])/1000
	#bmu_log.debug('V max: %.3f V (%s)' % (vmax['int']/1000, vmax['str']))

	vmin = bytearray_to_int(data[15:17])/1000
	#bmu_log.debug('V min: %.3f V (%s)' % (vmin['int']/1000, vmin['str']))

	#vavg = volt_total['int']/96/100
	#bmu_log.debug('V avg: %.3f V (calc)' % vavg)

	vdelta = (vmax-vmin)/1000
	#bmu_log.debug('V delta: %.3f V (calc)' % vdelta)

	# log_to_csv({'cell_max':vmax,'cell_min':vmin,'cell_delta':vdelta})
	#'cell_min', 'cell_max', 'cell_delta'

	limit_checks.check_warnings(v_max=vmax,v_min=vmin,v_delta=vdelta)

# Pack temperatures
def group4(data):
	t1 = bytearray_to_int(data[5:6])
	t2 = bytearray_to_int(data[8:9])
	t3 = bytearray_to_int(data[11:12])
	t4 = bytearray_to_int(data[14:15])

	temps = [t1,t2,t4]
	if t3 != 255:
		temps.append(t3)

	limit_checks.check_warnings(t_min=min(temps),t_max=max(temps))
	data_to_csv.log_to_csv({'t1':t1,'t2':t2,'t3':t3,'t4':t4})