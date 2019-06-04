# LeafBMU
Nissan Leaf HV Battery Control by PiCAN Python

This program is designed to control a Nissan Leaf G1/2 HV battery in place of the car's own computers.
It runs on Python 3(.?) on a Pi3 and PiCAN2 Duo CAN board.

It is designed to:
Interrogates the Local Battery Computer (LBC / BMS) within the Leaf battery.
Checks the values it finds are within safe limits.
If OK enables the main contactors (via a pre-charge sequence) which connects the battery to its output and makes it 'live'.
If NOK or becomes NOK it opens the contactors and isolates the battery.
If approaching the limits it provides a warning that limits are being approached.
Create log of battery parameters.

Control.py is the code which you run and which then calls in the others it needs.

To do first:
1/ Test limits are being checked continuously and acted on.
2/ Enable/Disable HV with a switch (while retaining limit checks)
In limit_checks.py 
turn_hv_on =  False
is the remote/switched request
This version does not include my attempts at getting a button working. GPIO 23/pin16 is where I'd like the button read from.

Future work:
Create MODBUS integration for remote control and reporting of parameters
create integration for various loads (solar inverters, EV motor controllers)
