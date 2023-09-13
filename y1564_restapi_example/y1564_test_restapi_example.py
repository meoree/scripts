"""
Script demonstrates an example of working with the M720 (Smart SFP) to configure the Y.1564 test
and output the Y.1564 test results using the REST API.
"""
import argparse
import time

import requests

IP_ADDRESS = "192.168.1.1"  # M720 (Smart# SFP) IP address

PROFILE = "profile0"  # configuration profile <profile0 | profile1>

# If you use several services, don't forget to specify their number
# in the y1564_params dictionary in the "service_count" parameter.

y1564_parameters = {
    "service_count": 1,  # service count (1-4)
    "learn_time_ms": 1000,  # learning frames transmission interval (ms). 0 ms - transmission (TX) off.

    # change configuration tests settings
    "conf_duration_useconds": "20000000",  # 20 sec
    "conf_duration_bytes": "0",  # number of bytes
    "conf_duration_packets": "0",  # number of packets

    # rx: analyzer logical interface,
    "topology_rx_enabled": True,
    "topology_rx_port": "porta",  # physical port corresponding to the selected logical interface (porta |  portb)

    # tx: generator logical interface
    "topology_tx_enabled": True,
    "topology_tx_port": "porta",  # physical port corresponding to the selected logical interface

    "cir_enabled": True,  # enable or disable test CIR
    "step_count": 4,  # step count for CIR test (1-10)
    "eir_enabled": True,  # enable or disable test EIR
    "tp_enabled": True,  # enable or disable test Traffic Policing

    "perf_enabled": True,  # enable or disable test PERF
    # performance test duration in bytes, packets or useconds
    "perf_duration_useconds": "20000000",  # 20 sec
    "perf_duration_packets": "0",  # number of bytes
    "perf_duration_bytes": "0",  # # number of packets
}

service0_parameters = {
    # service 0
    "service_number": 0,  # 0 - 3
    "frame_size": 1024,  # frame size in bytes
    "src_ip": "192.168.1.1",  # source IP address for service 0
    "dst_ip": "192.168.1.2",  # destination IP address for service 0
    "src_mac": "00:21:CE:44:00:DA",  # source MAC address for service 0
    "dst_mac": "00:21:CE:44:01:2A",  # destination MAC address for service 0
    "src_udp_port": 60000,  # source UDP port number
    "dst_udp_port": 50000,  # destination UDP port number

    "vlan_count": 0,  # VLAN label count (0 - off, 1 - 3 - on)
    # VLAN identifier and VLAN priority 
    "vlan_id1": 4095,
    "vlan_pri1": 0,
    "vlan_id2": 4094,
    "vlan_pri2": 0,
    "vlan_id3": 4093,
    "vlan_pri3": 0,

    # MPLS
    "mpls_count": 0,  # MPLS label count (0 - off, 1 - 3 - on)

    # QOS settings
    'qos_type': 'diffserv',  # Quality of Service type
    'tos': 0,  # Type of Service value
    'precedence': 0,  # precedence value
    'service_dscp': 0,  # DSCP value

    "cir_rate_value": "100.00000",  # rate value for CIR test
    "cir_rate_units": "mbps",  # rate value in percents, kbps or mbps <percents | kbps | mbps>
    "cir_rate_layer": 3,  # rate layer (1 - 4)

    "eir_rate_value": "100.00000",  # rate value for EIR test
    "eir_rate_units": "mbps",  # rate value in percents, kbps or mbps <percents | kbps | mbps>
    "eir_rate_layer": 3,  # rate layer (1 - 4)

    "tp_rate_value": "100.00000",  # rate value for Traffic Policing test
    "tp_rate_units": "mbps",  # rate value in percents, kbps or mbps <percents | kbps | mbps>
    "tp_rate_layer": 3,  # rate layer (1 - 4)

    # service acceptance criteria
    "sac_delay_variation_ms": "1.00000",  # FDV (Frame Delay Variation) in ms
    "sac_frame_delay_ms": "1.00000",  # FTD (Frame Transfer Delay) in ms
    "sac_loss_percents": "0.10000",  # FLR (Frame Loss Ratio) in %
    "sac_mfactor_mbps": "0.10000",  # M factor value in mbps
    "unordered_percents": "0.00000",  # OOP value in %
}

service1_parameters = {
    # service 1
    "service_number": 1,  # 0 - 3
    "frame_size": 1500,  # frame size in bytes
    "src_ip": "192.168.1.1",  # source IP address for service 0
    "dst_ip": "192.168.1.2",  # destination IP address for service 0
    "src_mac": "00:21:CE:44:00:DA",  # source MAC address for service 0
    "dst_mac": "00:21:CE:44:01:2A",  # destination MAC address for service 0
    "src_udp_port": 60000,  # source UDP port number
    "dst_udp_port": 50000,  # destination UDP port number

    "vlan_count": 0,  # VLAN label count (0 - off, 1 - 3 - on)
    # VLAN identifier and VLAN priority for the selected VLAN number
    "vlan_id1": 4095,
    "vlan_pri1": 0,
    "vlan_id2": 4094,
    "vlan_pri2": 0,
    "vlan_id3": 4093,
    "vlan_pri3": 0,

    # MPLS
    "mpls_count": 0,  # MPLS label count (0 - off, 1 - 3 - on)

    # QOS settings
    'qos_type': 'diffserv',  # Quality of Service type
    'tos': 0,  # Type of Service value
    'precedence': 0,  # precedence value
    'service_dscp': 0,  # DSCP value

    "cir_rate_value": "100.00000",  # rate value for CIR test
    "cir_rate_units": "mbps",  # rate value in percents, kbps or mbps <percents | kbps | mbps>
    "cir_rate_layer": 3,  # rate layer (1 - 4)

    "eir_rate_value": "100.00000",  # rate value for EIR test
    "eir_rate_units": "mbps",  # rate value in percents, kbps or mbps <percents | kbps | mbps>
    "eir_rate_layer": 3,  # rate layer (1 - 4)

    "tp_rate_value": "100.00000",  # rate value for Traffic Policing test
    "tp_rate_units": "mbps",  # rate value in percents, kbps or mbps <percents | kbps | mbps>
    "tp_rate_layer": 3,  # rate layer (1 - 4)

    # service acceptance criteria
    "sac_delay_variation_ms": "1.00000",  # FDV (Frame Delay Variation) in ms
    "sac_frame_delay_ms": "1.00000",  # FTD (Frame Transfer Delay) in ms
    "sac_loss_percents": "0.10000",  # FLR (Frame Loss Ratio) in %
    "sac_mfactor_mbps": "0.10000",  # M factor value in mbps
    "unordered_percents": "0.00000",  # OOP value in %
}

service2_parameters = {
    # service 2
    "service_number": 2,  # 0 - 3
    "frame_size": 1500,  # frame size in bytes
    "src_ip": "192.168.1.1",  # source IP address for service 0
    "dst_ip": "192.168.1.2",  # destination IP address for service 0
    "src_mac": "00:21:CE:44:00:DA",  # source MAC address for service 0
    "dst_mac": "00:21:CE:44:01:2A",  # destination MAC address for service 0
    "src_udp_port": 60000,  # source UDP port number
    "dst_udp_port": 50000,  # destination UDP port number

    "vlan_count": 0,  # VLAN label count (0 - off, 1 - 3 - on)
    # VLAN identifier and VLAN priority for the selected VLAN number
    "vlan_id1": 4095,
    "vlan_pri1": 0,
    "vlan_id2": 4094,
    "vlan_pri2": 0,
    "vlan_id3": 4093,
    "vlan_pri3": 0,

    # MPLS
    "mpls_count": 0,  # MPLS label count (0 - off, 1 - 3 - on)

    # QOS settings
    'qos_type': 'diffserv',  # Quality of Service type
    'tos': 0,  # Type of Service value
    'precedence': 0,  # precedence value
    'service_dscp': 0,  # DSCP value

    "cir_rate_value": "100.00000",  # rate value for CIR test
    "cir_rate_units": "mbps",  # rate value in percents, kbps or mbps <percents | kbps | mbps>
    "cir_rate_layer": 3,  # rate layer (1 - 4)

    "eir_rate_value": "100.00000",  # rate value for EIR test
    "eir_rate_units": "mbps",  # rate value in percents, kbps or mbps <percents | kbps | mbps>
    "eir_rate_layer": 3,  # rate layer (1 - 4)

    "tp_rate_value": "100.00000",  # rate value for Traffic Policing test
    "tp_rate_units": "mbps",  # rate value in percents, kbps or mbps <percents | kbps | mbps>
    "tp_rate_layer": 3,  # rate layer (1 - 4)

    # service acceptance criteria
    "sac_delay_variation_ms": "1.00000",  # FDV (Frame Delay Variation) in ms
    "sac_frame_delay_ms": "1.00000",  # FTD (Frame Transfer Delay) in ms
    "sac_loss_percents": "0.10000",  # FLR (Frame Loss Ratio) in %
    "sac_mfactor_mbps": "0.10000",  # M factor value in mbps
    "unordered_percents": "0.00000",  # OOP value in %
}

service3_parameters = {
    # service 3
    "service_number": 3,  # 0 - 3
    "frame_size": 1500,  # frame size in bytes
    "src_ip": "192.168.1.1",  # source IP address for service 0
    "dst_ip": "192.168.1.2",  # destination IP address for service 0
    "src_mac": "00:21:CE:44:00:DA",  # source MAC address for service 0
    "dst_mac": "00:21:CE:44:01:2A",  # destination MAC address for service 0
    "src_udp_port": 60000,  # source UDP port number
    "dst_udp_port": 50000,  # destination UDP port number

    "vlan_count": 0,  # VLAN label count (0 - off, 1 - 3 - on)
    # VLAN identifier and VLAN priority for the selected VLAN number
    "vlan_id1": 4095,
    "vlan_pri1": 0,
    "vlan_id2": 4094,
    "vlan_pri2": 0,
    "vlan_id3": 4093,
    "vlan_pri3": 0,

    # MPLS
    "mpls_count": 0,  # MPLS label count (0 - off, 1 - 3 - on)

    # QOS settings
    'qos_type': 'diffserv',  # Quality of Service type
    'tos': 0,  # Type of Service value
    'precedence': 0,  # precedence value
    'service_dscp': 0,  # DSCP value

    "cir_rate_value": "100.00000",  # rate value for CIR test
    "cir_rate_units": "mbps",  # rate value in percents, kbps or mbps <percents | kbps | mbps>
    "cir_rate_layer": 3,  # rate layer (1 - 4)

    "eir_rate_value": "100.00000",  # rate value for EIR test
    "eir_rate_units": "mbps",  # rate value in percents, kbps or mbps <percents | kbps | mbps>
    "eir_rate_layer": 3,  # rate layer (1 - 4)

    "tp_rate_value": "100.00000",  # rate value for Traffic Policing test
    "tp_rate_units": "mbps",  # rate value in percents, kbps or mbps <percents | kbps | mbps>
    "tp_rate_layer": 3,  # rate layer (1 - 4)

    # service acceptance criteria
    "sac_delay_variation_ms": "1.00000",  # FDV (Frame Delay Variation) in ms
    "sac_frame_delay_ms": "1.00000",  # FTD (Frame Transfer Delay) in ms
    "sac_loss_percents": "0.10000",  # FLR (Frame Loss Ratio) in %
    "sac_mfactor_mbps": "0.10000",  # M factor value in mbps
    "unordered_percents": "0.00000",  # OOP value in %
}


def connection(ip_addr):
    login = "admin"  # change if you have another login
    password = "PleaseChangeTheAdminPassword"  # change if you have another password
    connection = requests.post(
        f"http://{ip_addr}/api", json=
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "call",
            "params":
                ["00000000000000000000000000000000", "session", "login",
                 {
                     "username": login, "password": password, "timeout": 300
                 }
                 ]
        })
    return connection.json()["result"][1]["ubus_rpc_session"]


def configure_y1564(ip_addr, connection_id, y1564_params):
    r = requests.post(f"http://{ip_addr}/api", json=
    {
        "jsonrpc": "2.0",
        "id": 1, "method": "call",
        "params":
            [
                connection_id, "y1564", "setprm",
                {
                    "ids": {
                        "profile": PROFILE
                    },
                    "parameters": {
                        "y1564": {
                            "service_count": y1564_params['service_count'],
                            "step_count": y1564_params['step_count'],
                            "conf_duration": {
                                "type": "useconds",
                                "useconds": y1564_params['conf_duration_useconds'],
                                "packets": y1564_params['conf_duration_packets'],
                                "bytes": y1564_params['conf_duration_bytes'],
                            },
                            "perf_duration": {
                                "type": "useconds",
                                "useconds": y1564_params['perf_duration_useconds'],
                                "packets": y1564_params['perf_duration_packets'],
                                "bytes": y1564_params['perf_duration_bytes'],
                            },
                            "cir_enabled": y1564_params['cir_enabled'],
                            "eir_enabled": y1564_params['eir_enabled'],
                            "tp_enabled": y1564_params['tp_enabled'],
                            "perf_enabled": y1564_params['perf_enabled']
                        },
                        "trial": {
                            "ifaces": {
                                "rx": {
                                    "name": y1564_params['topology_rx_port'],
                                    "disabled": not y1564_params['topology_rx_enabled']
                                },
                                "tx": {
                                    "name": y1564_params['topology_tx_port'],
                                    "disabled": not y1564_params['topology_tx_enabled']
                                }
                            },
                            "learn_time_ms": y1564_params['learn_time_ms']
                        }
                    }
                }
            ]
    })
    return r.json()


def configure_y1564_service(ip_addr, connection_id, service_params):
    r = requests.post(f"http://{ip_addr}/api", json=
    {
        "jsonrpc": "2.0",
        "id": 1, "method": "call",
        "params":
            [
                connection_id, "y1564", "setprm",
                {
                    "ids": {
                        "profile": PROFILE,
                        "service": service_params['service_number']
                    },
                    "parameters": {
                        "frame_size": service_params['frame_size'],
                        "header": {
                            "src": {
                                "mac": service_params['src_mac'],
                                "ip": service_params['src_ip'],
                                "udp_port": service_params['src_udp_port']
                            },
                            "dst": {
                                "mac": service_params['dst_mac'],
                                "ip": service_params['dst_ip'],
                                "udp_port": service_params['dst_udp_port']
                            },
                            "vlan": {
                                "count": service_params['vlan_count'],
                                "tags": [
                                    {
                                        "pri": service_params['vlan_pri1'],
                                        "id": service_params['vlan_id1']
                                    },
                                    {
                                        "pri": service_params['vlan_pri2'],
                                        "id": service_params['vlan_id2']
                                    },
                                    {
                                        "pri": service_params['vlan_pri3'],
                                        "id": service_params['vlan_id3']
                                    }
                                ]},
                            "mpls": {
                                "count": service_params['mpls_count'],
                                "labels": [{
                                    "value": 128,
                                    "tc": 0,
                                    "ttl": 0},
                                    {
                                        "value": 128,
                                        "tc": 0,
                                        "ttl": 0
                                    },
                                    {
                                        "value": 128,
                                        "tc": 0,
                                        "ttl": 0}
                                ]},
                            "qos_type": service_params['qos_type'],
                            "dscp": service_params['service_dscp'],
                            "tos": service_params['tos'],
                            "precedence": service_params['precedence']
                        },
                        "sac": {
                            "loss_percents": service_params['sac_loss_percents'],
                            "frame_delay_ms": service_params['sac_frame_delay_ms'],
                            "delay_variation_ms": service_params['sac_delay_variation_ms'],
                            "mfactor_mbps": service_params['sac_mfactor_mbps'],
                            "unordered_percents": service_params['unordered_percents']
                        },
                        "bandwidth": {
                            "cir_rate": {
                                "value": service_params['cir_rate_value'],
                                "units": service_params['cir_rate_units'],
                                "layer": service_params['cir_rate_layer']},
                            "eir_rate": {
                                "value": service_params['eir_rate_value'],
                                "units": service_params['eir_rate_units'],
                                "layer": service_params['eir_rate_layer']},
                            "tp_rate": {
                                "value": service_params['tp_rate_value'],
                                "units": service_params['tp_rate_units'],
                                "layer": service_params['tp_rate_layer']}
                        }
                    }
                }
            ]})
    return r.json()


def show_y1564_settings(ip_addr, connection_id):
    r = requests.post(f"http://{ip_addr}:80/api", json=
    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "call",
        "params": [connection_id, "y1564", "getprm",
                   {
                       "ids": {
                           "profile": PROFILE,
                       }
                   }
                   ]
    }
                      )
    return r.json()


def show_service_settings(ip_addr, connection_id, service=0):
    r = requests.post(f"http://{ip_addr}:80/api", json=
    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "call",
        "params": [connection_id, "y1564", "getprm",
                   {
                       "ids": {
                           "profile": PROFILE,
                           "service": service
                       }
                   }
                   ]
    }
                      )
    return r.json()


def show_y1564_results(ip_addr, connection_id):
    template = """
    smart-sfp(admin)(config)# show y1564 results {}
    Status:        {}
    Message:       {} 
    Start time:    {}
    Stop time:     {} 
    Elapsed time:  {}
    Test           {} 
    Part           {}

    """
    r = requests.post(f"http://{ip_addr}:80/api", json=
    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "call",
        "params": [connection_id, "y1564", "getsts",
                   {
                       "ids": {
                           "profile": PROFILE
                       }
                   }
                   ]
    }
                      )
    output = r.json()['result'][1]['answer'][0]['statuses']
    status = output['status']
    message = output['retmsg']
    start_time = time.strftime("%H:%M:%S", time.gmtime(int(output['sys_time']['start_us']) / 1000000))
    stop_time = time.strftime("%H:%M:%S", time.gmtime(int(output['sys_time']['stop_us']) / 1000000))
    elapsed_time = time.strftime("%H:%M:%S", time.gmtime(int(output['sys_time']['elapsed_us']) / 1000000))
    test = output['cur_test']
    part = output['cur_part']
    return template.format(PROFILE, status, message, start_time, stop_time, elapsed_time, test, part)


def show_service_tests_results(ip_addr, connection_id, service=0, test="cir", part=0):
    template = ""
    template_empty = """
             IR(L2 mbps)  FTD(ms)  FDV(ms)  FLR(%)   OOP(%)   
    {}
    [{}]
        min:  {}    {}  
        avg:  {}    {}  {} {}  {}  
        max:  {}    {}  {}

    Statistics:
    rx_packets: {}
    rx_unordered_packets: {}
    tx_packets: {}
    """
    if part > 0:
        for part in range(0, part):
            r = requests.post(f"http://{ip_addr}:80/api", json=
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "call",
                "params": [connection_id, "y1564", "getsts",
                           {
                               "ids": {
                                   "profile": PROFILE,
                                   "test": test,
                                   "part": part,
                                   "service": service
                               }}]})
            output = r.json()['result'][1]['answer'][0]['statuses']['flows'][0]
            rate_min = output['info_rate']['min_mbps']
            rate_avg = output['info_rate']['average_mbps']
            rate_max = output['info_rate']['max_mbps']
            ftd_min = output['frame_delay']['min_ms']
            ftd_avg = output['frame_delay']['average_ms']
            ftd_max = output['frame_delay']['max_ms']
            fdv_avg = output['delay_variation']['average_ms']
            fdv_max = output['delay_variation']['max_ms']
            flr = output['loss_percents']
            oop = output['unordered_percents']
            stats_rx = output['stat']['rx_pkts']
            stats_rx_o = output['stat']['rx_unordered_pkts']
            stats_tx = output['stat']['tx_pkts']
            template = template + template_empty.format(
                test, part, rate_min, ftd_min, rate_avg, ftd_avg, fdv_avg, flr,
                oop, rate_max, ftd_max, fdv_max, stats_rx, stats_rx_o, stats_tx
            )
    else:
        r = requests.post(f"http://{ip_addr}:80/api", json=
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "call",
            "params": [connection_id, "y1564", "getsts",
                       {
                           "ids": {
                               "profile": PROFILE,
                               "test": test,
                               "service": service,
                               "part": 0
                           }}]})
        output = r.json()['result'][1]['answer'][0]['statuses']['flows'][0]
        rate_min = output['info_rate']['min_mbps']
        rate_avg = output['info_rate']['average_mbps']
        rate_max = output['info_rate']['max_mbps']
        ftd_min = output['frame_delay']['min_ms']
        ftd_avg = output['frame_delay']['average_ms']
        ftd_max = output['frame_delay']['max_ms']
        fdv_avg = output['delay_variation']['average_ms']
        fdv_max = output['delay_variation']['max_ms']
        flr = output['loss_percents']
        oop = output['unordered_percents']
        stats_rx = output['stat']['rx_pkts']
        stats_rx_o = output['stat']['rx_unordered_pkts']
        stats_tx = output['stat']['tx_pkts']
        template = template + template_empty.format(
            test, part, rate_min, ftd_min, rate_avg, ftd_avg, fdv_avg, flr,
            oop, rate_max, ftd_max, fdv_max, stats_rx, stats_rx_o, stats_tx
        )
    return template


def start_y1564(ip_addr, connection_id):
    r = requests.post(f"http://{ip_addr}:80/api", json=
    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "call",
        "params": [connection_id, "y1564", "start",
                   {
                       "ids": {
                           "profile": PROFILE
                       }}]})
    return r.json()


def stop_y1564(ip_addr, connection_id):
    r = requests.post(f"http://{ip_addr}:80/api", json=
    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "call",
        "params": [connection_id, "y1564", "stop",
                   {
                       "ids": {
                           "profile": PROFILE
                       }}]})
    return r.json()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Connect to M720 using REST API. Configure, start and stop y1564 test on M720.')
    parser.add_argument('action', help='Use start/stop/show commands')
    args = parser.parse_args()

    if args.action == "start":
        print(f"Connect to {IP_ADDRESS}")
        connection_json_id = connection(IP_ADDRESS)
        print("Configure service 0 and y1564 test")
        y1564_config = configure_y1564(IP_ADDRESS, connection_json_id, y1564_parameters)
        service0_config = configure_y1564_service(IP_ADDRESS, connection_json_id, service0_parameters)
        print("Start y1564 test")
        start_y1564(IP_ADDRESS, connection_json_id)
        result_common_y1564 = show_y1564_results(IP_ADDRESS, connection_json_id)
        print(result_common_y1564)
    elif args.action == "stop":
        print(f"Connect to {IP_ADDRESS}")
        connection_json_id = connection(IP_ADDRESS)
        print("Stop y1564 test")
        stop_y1564(IP_ADDRESS, connection_json_id)
        result_common_y1564 = show_y1564_results(IP_ADDRESS, connection_json_id)
        print(result_common_y1564)
    elif args.action == "show":
        print(f"Connect to {IP_ADDRESS}")
        connection_json_id = connection(IP_ADDRESS)
        print("Print y1564 test results")
        result_common_y1564 = show_y1564_results(IP_ADDRESS, connection_json_id)
        result_cir_service0 = show_service_tests_results(IP_ADDRESS, connection_json_id, service=0, test="cir",
                                                         part=y1564_parameters['step_count'])
        result_eir_service0 = show_service_tests_results(IP_ADDRESS, connection_json_id, service=0, test="eir")
        result_tp_service0 = show_service_tests_results(IP_ADDRESS, connection_json_id, service=0, test="tp")
        result_perf_service0 = show_service_tests_results(IP_ADDRESS, connection_json_id, service=0, test="perf")
        print(
            result_common_y1564 + result_cir_service0 + result_eir_service0 +
            result_tp_service0 + result_perf_service0
        )
    else:
        print("Invalid argument. Use start, stop or show parameter.")
