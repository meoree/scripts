<!-- ABOUT THE SCRIPT -->
## About The Script

Script demonstrates an example of working with the M720 (Smart SFP) to configure the Y.1564 test and output the Y.1564 test results using the REST API.
You can only change the test parameters in the script, and the script will automatically configure the Y.1564 test, start/stop it and read the test results.

Before running the script:
* Determine the value of the M720 IP address in the script for connecting to the M720. The IP address of the M720 can be changed in the "IP_ADDRESS" parameter at the beginning of the program.
* If you do not use the login and password parameters by default on the M720, then change these values in the "connection()" function in the "login" and "password" parameters.
* You can change the parameters in the dictionaries "y1564_parameters" and "service 0_parameters" according to the description in the comments in the program code.

<!-- Usage -->
## Usage

You can run the script with 3 arguments:
* **start**

The script will connect to the M720, configure the Y.1564 test settings and service 0 for the Y.1564 test, and run the Y.1564 test.

Launch: `python3 y1564_restapi.py start`

Example:
```
❯ python3 y1564_restapi.py start
Connect to 192.168.89.140
Configure service 0 and y1564 test
Start y1564 test
 
    smart-sfp(admin)(config)# show y1564 results profile0
    Status:        True
    Message:       OK
    Start time:    11:48:59
    Stop time:     00:00:00
    Elapsed time:  00:00:04
    Test           cir
    Part           0
```

* **stop**

The script will connect to the M720 and stop the Y.1564 test.

Launch: `python3 y1564_restapi.py stop`

Example:
```
❯ python3 y1564_restapi.py stop
Connect to 192.168.89.140
Stop y1564 test
 
    smart-sfp(admin)(config)# show y1564 results profile0
   Status:        False
    Message:       OK
    Start time:    11:48:59
    Stop time:     11:49:27
    Elapsed time:  00:00:28
    Test           cir
    Part           1
```

* **show**

The script will connect to the M720 and display information of the Y.1564 test results for service 0.

Launch: `python3 y1564_restapi.py show`

Example:
```
❯ python3 y1564_restapi.py show
Connect to 192.168.89.140
Print y1564 test results
 
    smart-sfp(admin)(config)# show y1564 results profile0
    Status:        False
    Message:       OK
    Start time:    11:50:30
    Stop time:     11:53:06
    Elapsed time:  00:02:35
    Test           perf
    Part           0
 
   
             IR(L2 mbps)  FTD(ms)  FDV(ms)  FLR(%)   OOP(%)  
    cir
    [0]
        min:  25.44435    0.01101 
        avg:  25.44786    0.01101  0.00000 0.00000  0.00000 
        max:  25.45254    0.01106  0.00005
 
    Statistics:
    rx_packets: 62127
    rx_unordered_packets: 0
    tx_packets: 62127
   
             IR(L2 mbps)  FTD(ms)  FDV(ms)  FLR(%)   OOP(%)  
    cir
    [1]
        min:  50.88870    0.01101 
        avg:  50.89485    0.01101  0.00000 0.00000  0.00000 
        max:  50.89690    0.01106  0.00005
 
    Statistics:
    rx_packets: 124254
    rx_unordered_packets: 0
    tx_packets: 124254
   
             IR(L2 mbps)  FTD(ms)  FDV(ms)  FLR(%)   OOP(%)  
    cir
    [2]
        min:  76.34125    0.01101 
        avg:  76.34212    0.01101  0.00000 0.00000  0.00000 
        max:  76.34944    0.01106  0.00005
 
    Statistics:
    rx_packets: 186381
    rx_unordered_packets: 0
    tx_packets: 186381
   
             IR(L2 mbps)  FTD(ms)  FDV(ms)  FLR(%)   OOP(%)  
    cir
    [3]
        min:  101.78560    0.01101 
        avg:  101.78911    0.01101  0.00000 0.00000  0.00000 
        max:  101.79379    0.01106  0.00005
 
    Statistics:
    rx_packets: 248508
    rx_unordered_packets: 0
    tx_packets: 248508
   
             IR(L2 mbps)  FTD(ms)  FDV(ms)  FLR(%)   OOP(%)  
    eir
    [0]
        min:  203.57120    0.01101 
        avg:  203.57852    0.01101  0.00000 0.00000  0.00000 
        max:  203.57939    0.01106  0.00005
 
    Statistics:
    rx_packets: 497017
   rx_unordered_packets: 0
    tx_packets: 497017
   
             IR(L2 mbps)  FTD(ms)  FDV(ms)  FLR(%)   OOP(%)  
    tp
    [0]
        min:  101.78560    0.01101 
        avg:  101.78970    0.01101  0.00000 0.00000  0.00000 
        max:  101.79379    0.01106  0.00005
 
    Statistics:
    rx_packets: 248508
    rx_unordered_packets: 0
    tx_packets: 248508
   
             IR(L2 mbps)  FTD(ms)  FDV(ms)  FLR(%)   OOP(%)  
    perf
    [0]
        min:  101.78560    0.01101 
        avg:  101.78999    0.01101  0.00000 0.00000  0.00000 
        max:  101.79379    0.01106  0.00005
 
    Statistics:
    rx_packets: 248508
    rx_unordered_packets: 0
    tx_packets: 248508
```
