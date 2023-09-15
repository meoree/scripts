<!-- ABOUT THE SCRIPT -->
## About The Script

The script is used to test M720 modules (Smart SFP) in switches. During the test, the modules are rebooted and the link status on the switch is checked. 

1. Use reboot to run a switch reboot test using the "reload" command.
As a result of the test, a csv report of the form Number Of Test,
Reachable IP address, Unreachable IP address.

2. Use shutdown will be generated to run the test with shutdown of interfaces
on the switch using "shutdown".
The test will generate a csv report like Number Of Test, Reachable IP address,
Unreachable IP address.

3. Use power to run a power off test on the switch using a controlled outlet (NetPing).
As a result of the test, a csv report will be generated with information on whether the modules
were pinged or not, which interfaces were in the down state, which clocks were on the M720.

4. Use manual to run a manual test with manually removing M720 modules from the switch and inserting them back. 

Before running the script, change the values:
* SWITCH1_CONNECTION_DATA, SWITCH2_CONNECTION_DATA - network parameters for connecting to the switch via ssh.
* SWTICH1_M720, SWTICH2_M720, - dictionary with M720 serial numbers and switch interfaces in which they are inserted.
* SN_IP_DICT_OPTIC, SN_IP_DICT_RJ45 - dictionary with M720 serial numbers and their IP addresses.
* RELAY_NUMBER - number of the relay to which the switch is powered by NetPing.
* HOURS and MINUTES - test time
* HOST_DATA - data for copying the clocks results to the host device
<!-- Usage -->
## Usage

The script must be run with the --type option: `python3 link_test_m720.py --type optic --power 1`

The --type option is introduced for correct generation of a file with results for optical and copper modules. If copper modules are tested, then copper, if optical, then optic.

* **reboot**

Start the switch reboot function using the reload command. It is necessary to set the correct values in the variable before starting the script execution 
SWITCH1_CONNECTION_DATA for connecting to the switch.

Launch: `python3 link_test_m720.py --reboot --type optic`

* **shutdown**

Start the function of disabling the switch interfaces using the shutdown command. It is necessary to set the correct values in the SWITCH1_CONNECTION_DATA variable to connect to the switch before starting the script execution.

Launch: `python3 link_test_m720.py --reboot --type optic`

* **power 1**

Start the switch overload function using a smart NetPing outlet. It is necessary to set the correct values in the SWITCH1_CONNECTION_DATA variable to connect to the switch, since this function does not connect to the switch. It is necessary to set the correct value of RELAY_NUMBER so that NetPing disables and enables the relay to which the switch is connected.

Launch: `python3 link_test_m720.py  --power 1 --type copper`

* **power 2**

Start the switch overload function using the NetPing smart socket. It is necessary to set the correct values in the SWITCH1_CONNECTION_DATA variable to connect to the switch in which the M720 modules are installed by port B, SWITCH2_CONNECTION_DATA to connect to the switch in which the M720 modules are installed by port A. It is necessary to set the correct value of RELAY_NUMBER so that NetPing disables and enables the relay to which the SWITCH1 switch is connected.

Launch: `python3 link_test_m720.py  --power 2 --type copper`

* **power 3**

Start the switch overload function using the NetPing smart socket. It is necessary to set the correct values in the SWITCH1_CONNECTION_DATA variable to connect to the switch in which the M720 modules are installed by port B, SWITCH2_CONNECTION_DATA to connect to the switch in which the M720 modules are installed by port A. It is necessary to set the correct value of RELAY_NUMBER so that NetPing disables and enables the relay to which the SWITCH2 switch is connected.

Launch: `python3 link_test_m720.py  --power 3 --type optic`

* **manual**

Start the manual test function with manual recovery of modules from the switch. It is necessary to set the correct values in the SWITCH1_CONNECTION_DATA variable to connect to the switch in which the M720 modules are installed by port B, SWITCH2_CONNECTION_DATA to connect to the switch in which the M720 modules are installed by port A.

Launch: `python3 link_test_m720.py  --manual --type copper`
