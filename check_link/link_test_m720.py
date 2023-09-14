"""
Tests the link status on the switch when the M720 is connected.
"""
import csv
import glob
import logging
import re
import socket
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from itertools import repeat
from pathlib import Path
from subprocess import DEVNULL

import click
import paramiko
import requests
from halo import Halo
from paramiko.client import SSHClient, AutoAddPolicy
from paramiko.ssh_exception import AuthenticationException, SSHException, BadHostKeyException

logging.basicConfig(
    format="{message}",
    datefmt="%H:%M:%S",
    style="{",
    level=logging.ERROR,
)

# Data to connect to the switch 1 with SSH
SWITCH1_CONNECTION_DATA = {
    "login": "admin",
    "ip": "192.168.89.101",
    "password": "JRmQ0aTjEeqh",
    "enable_password": None
}

# Data to connect to the switch 2 with SSH
SWITCH2_CONNECTION_DATA = {
    "login": "admin",
    "ip": "192.168.89.93",
    "password": "admin",
    "enable_password": None
}

SWITCH1_NAME = "24fx_copper"

# Dictionary with M720 serial numbers and switch interfaces in which they are inserted
SWITCH1_M720 = {
    591: "1/0/1",
    592: "1/0/2",
    593: "1/0/3",
    594: "1/0/4",
    595: "1/0/5",
    596: "1/0/6",
    597: "1/0/7",
    598: "1/0/8",
    599: "1/0/9",
    600: "1/0/10",
    601: "1/0/11",
    602: "1/0/12",
    603: "1/0/13",
    604: "1/0/14",
    605: "1/0/15",
    606: "1/0/16",
    607: "1/0/17",
    608: "1/0/18",
    609: "1/0/19",
    610: "1/0/20",
    611: "1/0/21",
    612: "1/0/22",
    613: "1/0/23",
    614: "1/0/24"
}

SWITCH2_M720 = {
    591: "1/0/1",
    592: "1/0/2",
    593: "1/0/3",
    594: "1/0/4",
    595: "1/0/5",
    596: "1/0/6",
    597: "1/0/7",
    598: "1/0/8",
    599: "1/0/9",
    600: "1/0/10",
    601: "1/0/11",
    602: "1/0/12",
    603: "1/0/13",
    604: "1/0/14",
    605: "1/0/15",
    606: "1/0/16",
    607: "1/0/17",
    608: "1/0/18",
    609: "1/0/19",
    610: "1/0/20",
    611: "1/0/21",
    612: "1/0/22",
    613: "1/0/23",
    614: "1/0/24"
}

# Test time for power 1,2,3, shutdown and reboot tests
HOURS = 1
MINUTES = 0

# Correlation of optic M720 serial numbers with IP addresses
SN_IP_DICT_OPTIC = {
    "new": {
        2967: "192.168.90.167",
        2968: "192.168.90.168",
        2969: "192.168.90.169",
        2970: "192.168.90.170",
        2971: "192.168.90.171",
        2972: "192.168.90.172",
        2973: "192.168.90.173",
        2974: "192.168.90.174",
        2975: "192.168.90.175",
        2976: "192.168.90.176",
        2977: "192.168.90.177",
        2978: "192.168.90.178",
        2979: "192.168.90.179",
    },
    "old": {
        191: "192.168.90.201",
        199: "192.168.90.202",
        30: "192.168.90.203",
        195: "192.168.90.204",
        194: "192.168.90.205",
        184: "192.168.90.206",
        35: "192.168.90.207",
        197: "192.168.90.208",
        32: "192.168.90.209",
        198: "192.168.90.210",
        169: "192.168.90.211",
        36: "192.168.90.212",
        188: "192.168.90.213",
    }
}

# Correlation of copper M720 serial numbers with IP addresses
SN_IP_DICT_RJ_45 = {
    "copper": {
        591: "192.168.90.181",
        592: "192.168.90.182",
        593: "192.168.90.183",
        594: "192.168.90.184",
        595: "192.168.90.185",
        596: "192.168.90.186",
        597: "192.168.90.187",
        598: "192.168.90.188",
        599: "192.168.90.189",
        600: "192.168.90.190",
        601: "192.168.90.191",
        602: "192.168.90.192",
        603: "192.168.90.193",
        604: "192.168.90.194",
        605: "192.168.90.195",
        606: "192.168.90.196",
        607: "192.168.90.197",
        608: "192.168.90.198",
        609: "192.168.90.199",
        610: "192.168.90.200",
        611: "192.168.90.151",
        612: "192.168.90.152",
        613: "192.168.90.153",
        614: "192.168.90.154",
    },
    "optic": {
    }
}

HOST_DATA = {
    "host_login": "pi",
    "host_password": "raspberry",
    "host_ip": "192.168.90.102",
    "host_path": Path(f"/home/pi/link_test/{SWITCH1_NAME}"),
}

# NET_PING_BASE_URL format: http://<login>:<password>@<ip-address>:<udp-port>
NET_PING_BASE_URL = "http://visor:ping@192.168.90.155:80"

RELAY_NUMBER: int = 1


# ------------ SSH CONNECTION ----------------
class SSHParamiko:
    """
    SSH connection using Paramiko.
    """

    def __init__(self, **device_data):
        self.ip_address = device_data["ip"]
        self.login = device_data["login"]
        self.password = device_data["password"]
        try:
            self.enable_password = device_data["enable_password"]
        except KeyError:
            self.enable_password = None
        try:
            self.root_password = device_data["root_password"]
        except KeyError:
            self.root_password = None
        self.short_sleep = 0.2
        self.long_sleep = 2
        self.max_read = 100000

        logging.info(">>>>> Connection to %s as %s", self.ip_address, self.login)
        try:
            self.client = SSHClient()
            self.client.set_missing_host_key_policy(AutoAddPolicy())
            self.client.connect(
                hostname=self.ip_address,
                username=self.login,
                password=self.password,
                look_for_keys=False,
                allow_agent=False,
                timeout=30,
                disabled_algorithms={'pubkeys': ['rsa-sha2-256', 'rsa-sha2-512']}
            )
            logging.info("Authentication is successful")

            self._shell = self.client.invoke_shell()
            time.sleep(self.short_sleep)
            self._shell.recv(self.max_read)
            if self.enable_password:
                self.send_shell_commands(["enable", self.enable_password])
            if self.root_password:
                self.send_shell_commands(["su", self.root_password])
        except (socket.timeout, socket.error) as error:
            logging.error(f"An error {error} occurred on {self.ip_address}")
        except AuthenticationException as error:
            logging.error(f"Authentication failed, please verify your credentials: {error}")
        except BadHostKeyException as error:
            logging.error(f"Unable to verify server's host key: {error}")
        except SSHException as error:
            logging.error(f"Unable to establish SSH connection: {error}")
        except EOFError:
            logging.error("Try to reconnect")
            self.__init__(**device_data)

    def _formatting_output(self):
        return self._shell.recv(self.max_read).decode("utf-8").replace("\r\n", "\n")

    def _send_line_shell(self, command):
        return self._shell.send(f"{command}\n")

    def send_shell_commands(self, commands, print_output=True):
        """
        Send commands on the device.
        :param commands: string (one command) or list of strings (commands)
        :param print_output: command result output
        :return: command output
        """
        time.sleep(self.long_sleep)
        output = ""
        logging.info(f">>> Send shell command(s) on {self.ip_address}: {commands}")
        try:
            if str == type(commands):
                self._send_line_shell(commands)
                time.sleep(self.long_sleep)
                output = self._formatting_output()
            else:
                for command in commands:
                    self._send_line_shell(command)
                    time.sleep(self.long_sleep)
                    if print_output:
                        output += self._formatting_output()
        except paramiko.SSHException as error:
            logging.error(f"An error {error} occurred on {self.ip_address}")
        return output

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        """
        Close ssh connection.
        """
        self.client.close()


# ------------ ADDITIONAL FUNCTIONS ----------------
def time_for_test():
    """
    Time for test in minutes.
    :return: minutes for test duration
    """
    minutes = HOURS * 60 + MINUTES
    return minutes


def ping_ip_addresses(ip_list):
    """
    Ping M720 IP addresses from the list
    :param ip_list: list of IP addresses
    :return: two lists, pingable_ip containing IP addresses that were ping successfully,
    unpingable_ip otherwise
    """
    pingable_ip = []
    unpingable_ip = []
    processes = []

    for ip_addr in ip_list:
        process = subprocess.Popen(f'ping -c 10 {ip_addr}'.split(), stdout=DEVNULL, stderr=DEVNULL)
        processes.append(process)
    for ip_addr, process in zip(ip_list, processes):
        returncode = process.wait()
        if returncode == 0:
            pingable_ip.append(ip_addr)
        else:
            unpingable_ip.append(ip_addr)
    return pingable_ip, unpingable_ip


def create_file_with_results(result_filename, m720_type, porta=False):
    """
    Create a file with results for test.
    :param m720_type: optic ot copper
    :param result_filename: file name
    :param porta: add new column in result file for port a
    :return: file name with date
    """
    timestr = time.strftime("%d_%m_%H_%M")
    file_name = f"{result_filename}_{timestr}.csv"

    headers: list = ["Number of test"]

    if m720_type == "optic":
        headers.extend(["Reachable new s/n", "Unreachable new s/n",
                        "Reachable old s/n", "Unreachable old s/n", "Down interfaces (port B)"])
    elif m720_type == "copper":
        headers.extend(["Reachable copper s/n", "Unreachable copper s/n",
                        "Reachable optic s/n", "Unreachable optic s/n", "Down interfaces (port B)"])
    with open(file_name, "w", encoding="UTF-8") as file:
        file_writer = csv.writer(file, delimiter=";", lineterminator="\r")
        if porta:
            headers.append("Down interfaces (port A)")
        file_writer.writerow(headers)
    return file_name


def get_results(m720_ip_addresses):
    """
    Processes the results of pinged and non-pinged IP addresses for a table
    :param m720_ip_addresses:
    :return: list of results
    """
    reach_ip, unreach_ip = ping_ip_addresses(m720_ip_addresses)

    sn_reach_new = []
    sn_reach_old = []

    for ip in reach_ip:
        for s_n, ip_addr in SN_IP_DICT_OPTIC['new'].items():
            if ip_addr == ip:
                sn_reach_new.append(str(s_n))
        for s_n, ip_addr in SN_IP_DICT_OPTIC['old'].items():
            if ip_addr == ip:
                sn_reach_old.append(str(s_n))
        for s_n, ip_addr in SN_IP_DICT_RJ_45['copper'].items():
            if ip_addr == ip:
                sn_reach_new.append(str(s_n))
        for s_n, ip_addr in SN_IP_DICT_RJ_45['optic'].items():
            if ip_addr == ip:
                sn_reach_old.append(str(s_n))

    sn_unreach_new = []
    sn_unreach_old = []

    for ip in unreach_ip:
        for s_n, ip_addr in SN_IP_DICT_OPTIC['new'].items():
            if ip_addr == ip:
                sn_unreach_new.append(str(s_n))
        for s_n, ip_addr in SN_IP_DICT_OPTIC['old'].items():
            if ip_addr == ip:
                sn_unreach_old.append(str(s_n))
        for s_n, ip_addr in SN_IP_DICT_RJ_45['copper'].items():
            if ip_addr == ip:
                sn_unreach_new.append(str(s_n))
        for s_n, ip_addr in SN_IP_DICT_RJ_45['optic'].items():
            if ip_addr == ip:
                sn_unreach_old.append(str(s_n))

    reachable_new = ", ".join(sn_reach_new)
    unreachable_new = ", ".join(sn_unreach_new)
    reachable_old = ", ".join(sn_reach_old)
    unreachable_old = ", ".join(sn_unreach_old)

    result = [reachable_new, unreachable_new, reachable_old, unreachable_old]
    return result


def check_link_on_switch(switch_intf, switch_connection_data=None):
    """
    Function to check the link on a switch interfaces

    :param switch_intf: list of switch interfaces
    :param switch_connection_data: data to connect to switch
    :return: string with down switch interfaces
    """
    if switch_connection_data is None:
        switch_connection_data = SWITCH1_CONNECTION_DATA
    with SSHParamiko(**switch_connection_data) as ssh_connection:
        output = ssh_connection.send_shell_commands(
            ["terminal length 0", "show interface ethernet status"])
    intf_list = []
    result = ""
    for intf in switch_intf:
        try:
            match = re.search(rf"{intf}\s+(\S+)", output)
            if "down" in match.group().lower():
                intf_list.append(intf)
        except AttributeError:
            logging.critical(f"No such interface - {intf} on the switch. "
                             f"Check switch_connection_data")
    if intf_list:
        result = ", ".join(intf_list)
    return result


def reboot_switch():
    """
    Send a reboot command to the switch.
    """
    with SSHParamiko(**SWITCH1_CONNECTION_DATA) as sw_connection:
        sw_connection.send_shell_commands(["reload", "yes"], print_output=False)


def shutdown_switch_interfaces():
    """
    Start test with shutdown switch interfaces.
    """
    regex = r"\S/\d+\s+(\S+)\s+"
    with SSHParamiko(**SWITCH1_CONNECTION_DATA) as sw_connection:
        sw_connection.send_shell_commands(
            ["terminal length 0", "conf t", "int eth 1/0/1-28", "shutdown", "exit"])
        output = sw_connection.send_shell_commands(["show interface ethernet status"])
        result = re.findall(regex, output)
        for element in result:
            if "down" not in element.lower():
                return False
        sw_connection.send_shell_commands(
            ["int eth 1/0/1-28", "no shutdown", ""])
        time.sleep(60)
    return True


def power_off_switch():
    """
    Changing the control source, as well as manually turning the relay on and off: relay.cgi?rn=s
    After ?r the number of the relay is indicated,
    after = the number of the mode (control source) is indicated.
    where: n – relay number
    s – relay operation mode:
       0 – Manual off
       1 – Manual on
    """
    power_off_url = f'{NET_PING_BASE_URL}/relay.cgi?r{RELAY_NUMBER}=0'
    power_on_url = f'{NET_PING_BASE_URL}/relay.cgi?r{RELAY_NUMBER}=1'

    try:
        requests.get(power_off_url, timeout=30)
        time.sleep(15)
        requests.get(power_on_url, timeout=30)
        time.sleep(160)
    except requests.ConnectionError as err:
        logging.error('Error connecting: %s', err)
    except requests.exceptions.HTTPError as err:
        logging.error('Invalid HTTP request: %s', err)
    except requests.RequestException as err:
        logging.error('General error: %s', err)


def create_rc_local(ip_address):
    """
    Create rc.local file on M720.
    :param ip_address: M720 IP address
    :return: filename on M720
    """
    m720_connection_data = {
        "login": "user",
        "ip": ip_address,
        "password": "PleaseChangeTheUserPassword",
        "root_password": "PleaseChangeTheRootPassword"
    }

    serial_number = 0
    for s_n, ip_addr in SN_IP_DICT_OPTIC['new'].items():
        if ip_addr == ip_address:
            serial_number = s_n
    for s_n, ip_addr in SN_IP_DICT_OPTIC['old'].items():
        if ip_addr == ip_address:
            serial_number = s_n
    for s_n, ip_addr in SN_IP_DICT_RJ_45['copper'].items():
        if ip_addr == ip_address:
            serial_number = s_n
    for s_n, ip_addr in SN_IP_DICT_RJ_45['optic'].items():
        if ip_addr == ip_address:
            serial_number = s_n

    timestr = time.strftime("%d_%m_%H_%M")
    clk_ctl_filename = f"{serial_number}_test_clock_{timestr}.csv"
    content = f'#!/bin/sh -e\nmount -o rw,remount /\nclk_ctl.py -f {clk_ctl_filename}\nexit 0\n'
    with SSHParamiko(**m720_connection_data) as ssh:
        ssh.send_shell_commands(
            ["", "mount -o rw,remount /", "rm /etc/rc.local",
             f"printf '{content}' >> /etc/rc.local", "chmod +x /etc/rc.local",
             "cd /home/user/", "rm *.csv", "ls", 'cat /etc/rc.local', "reboot"])
    return clk_ctl_filename


def get_results_from_m720(ip_address_m720):
    """
    Connect to the M720 via SSH and copy results to the host.
    :param ip_address_m720: M720 IP address
    """
    m720_connection_data = {
        "login": "user",
        "ip": ip_address_m720,
        "password": "PleaseChangeTheUserPassword",
        "root_password": "PleaseChangeTheRootPassword"
    }
    # Data for connecting via scp to the device from which the script is started.
    host_login = HOST_DATA["host_login"]
    host_password = HOST_DATA["host_password"]
    host_ip = HOST_DATA["host_ip"]
    host_path = HOST_DATA["host_path"]

    with SSHParamiko(**m720_connection_data) as ssh:
        output = ssh.send_shell_commands(["scp /home/user/*.csv "
                                          f"{host_login}@{host_ip}:{host_path}"])
        if "(yes/no)" in output:
            ssh.send_shell_commands(["yes", host_password])
        else:
            ssh.send_shell_commands(host_password)


def create_total_results(sn_list, results_filename, m720_type, porta=False):
    """
    Create file with total results including M720 clocks and format for filtering.
    :param m720_type: copper or optic m720
    :param sn_list: M720 serial number list
    :param results_filename: file name of the results
    :param porta: True if power test 2 otherwise
    """
    match = re.search(r"link_test_[a-z]+_(\w+)_(\d+_\d+_\d+_\d+).csv", results_filename).groups()
    switch_in_filename, date_in_filename = match
    search_date = date_in_filename[:-2]

    first_list = []
    second_list = ["Number of test"]

    for serial_number in sn_list:
        if m720_type == "optic":
            if porta:
                first_list.extend(repeat(serial_number, 6))
                second_list.extend([
                    "New/Old", "CN0", "CN1", "Down intf port b", "Down intf port a", "Result"]
                )
            else:
                first_list.extend(repeat(serial_number, 5))
                second_list.extend(["New/Old", "CN0", "CN1", "Down intf port b", "Result"])
        elif m720_type == "copper":
            if porta:
                first_list.extend(repeat(serial_number, 6))
                second_list.extend(
                    ["Copper/Optic", "CN0", "CN1", "Down intf port b", "Down intf port a", "Result"]
                )
            else:
                first_list.extend(repeat(serial_number, 5))
                second_list.extend(["Copper/Optic", "CN0", "CN1", "Down intf port b", "Result"])

    first_headers = ["", *first_list]
    second_headers = second_list

    try:
        with open(f"total_link_test_power_{switch_in_filename}_"
                  f"{date_in_filename}.csv", "w+", encoding="UTF-8") as total:
            writer = csv.writer(total, delimiter=";")
            writer.writerow(first_headers)
            writer.writerow(second_headers)

        with open(results_filename, "r", encoding="UTF-8") as file1:
            reader1 = csv.reader(file1, delimiter=";")
            next(reader1)
            for row1 in reader1:
                if porta:
                    number, reach_new, unreach_new, reach_old, \
                        unreach_old, down_interfaces_b, down_interfaces_a = row1
                else:
                    number, reach_new, unreach_new, reach_old, \
                        unreach_old, down_interfaces_b = row1
                result_raw = [number]
                for serial_number in sn_list:
                    new_old = sn_b_down = sn_a_down = result = cn0 = cn1 = None
                    if str(serial_number) in reach_new.split(', '):
                        result = 1
                        if m720_type == "optic":
                            new_old = "new"
                        elif m720_type == "copper":
                            new_old = "copper"
                    elif str(serial_number) in unreach_new.split(', '):
                        result = 0
                        if m720_type == "optic":
                            new_old = "new"
                        elif m720_type == "copper":
                            new_old = "copper"
                    elif str(serial_number) in reach_old.split(', '):
                        result = 1
                        if m720_type == "optic":
                            new_old = "old"
                        elif m720_type == "copper":
                            new_old = "optic"
                    elif str(serial_number) in unreach_old.split(', '):
                        result = 0
                        if m720_type == "optic":
                            new_old = "old"
                        elif m720_type == "copper":
                            new_old = "optic"
                    if down_interfaces_b:
                        for down_intf1 in down_interfaces_b.split(', '):
                            if SWITCH1_M720[serial_number] == down_intf1:
                                result = 0
                                sn_b_down = down_intf1
                    if porta and down_interfaces_a:
                        for down_intf2 in down_interfaces_a.split(', '):
                            if SWITCH2_M720[serial_number] == down_intf2:
                                result = 0
                                sn_a_down = down_intf2
                    try:
                        sn_filename = glob.glob(f"{serial_number}_test_clock_{search_date}*.csv")[0]
                        with open(sn_filename, 'r', encoding="UTF-8") as file2:
                            reader2 = csv.reader(file2, delimiter=";")
                            try:
                                next(reader2)
                                for row2 in reader2:
                                    if row2[0] == number:
                                        cn0 = row2[1]
                                        cn1 = row2[2]
                                        break
                            except StopIteration:
                                logging.error(f"File {sn_filename} is empty")
                                continue
                    except IndexError:
                        logging.error(
                            f"No such file - {serial_number}_test_clock_{search_date}*.csv"
                        )
                    if porta:
                        result_raw.extend([new_old, cn0, cn1, sn_b_down, sn_a_down, result])
                    else:
                        result_raw.extend([new_old, cn0, cn1, sn_b_down, result])
                with open(f"total_link_test_power_{switch_in_filename}_"
                          f"{date_in_filename}.csv", "a", encoding="UTF-8") as total:
                    writer = csv.writer(total, delimiter=";")
                    writer.writerow(result_raw)
    except IndexError:
        logging.error(f"No such file - {results_filename}")


def get_clocks_from_m720(ip_address_m720):
    m720_connection_data = {
        "login": "user",
        "ip": ip_address_m720,
        "password": "PleaseChangeTheUserPassword",
        "root_password": "PleaseChangeTheRootPassword"
    }
    serial_number = 0
    for s_n, ip_addr in SN_IP_DICT_OPTIC['new'].items():
        if ip_addr == ip_address_m720:
            serial_number = s_n
    for s_n, ip_addr in SN_IP_DICT_OPTIC['old'].items():
        if ip_addr == ip_address_m720:
            serial_number = s_n
    for s_n, ip_addr in SN_IP_DICT_RJ_45['copper'].items():
        if ip_addr == ip_address_m720:
            serial_number = s_n
    for s_n, ip_addr in SN_IP_DICT_RJ_45['optic'].items():
        if ip_addr == ip_address_m720:
            serial_number = s_n

    sn_filename = glob.glob(f"{serial_number}_test_clock_*.csv")[0]
    with SSHParamiko(**m720_connection_data) as ssh:
        output = ssh.send_shell_commands(["clk_ctl.py -t 1"])
        cnt0 = re.search(r"CNT 0:\s+(\d+)", output).groups()[0]
        cnt1 = re.search(r"CNT 1:\s+(\d+)", output).groups()[0]
        if cnt0 and cnt1:
            with open(sn_filename, 'r', encoding="utf-8") as file:
                reader = list(csv.reader(file, delimiter=";", lineterminator="\r"))
                final_line = reader[-1]
            with open(sn_filename, 'a', encoding="utf-8") as file:
                file_writer = csv.writer(file, delimiter=";", lineterminator="\r")
                if "Number" in final_line[0]:
                    i = 1
                else:
                    i = int(final_line[0]) + 1
                file_writer.writerow([str(i), cnt0, cnt1])


def create_clocks_file(serial_number):
    timestr = time.strftime("%d_%m_%H_%M")
    file_name = f"{serial_number}_test_clock_{timestr}.csv"
    with open(file_name, "w", encoding="utf-8") as file:
        file_writer = csv.writer(file, delimiter=";", lineterminator="\r")
        file_writer.writerow(["Number of test", "CNT 0", "CNT 1"])


# ------------ TEST FUNCTIONS ----------------
def reboot_switch_test(m720_ip_list, m720_type):
    """
    Start test with reboot switch.

    :type m720_type: copper or optic m720
    :param m720_ip_list: M720 IP addresses list
    :return: file name with result
    """
    result_filename = f"link_test_reboot_{SWITCH1_NAME}"
    file_name = create_file_with_results(result_filename, m720_type)

    one_test_time = 4  # minutes
    count_of_tests = time_for_test() // one_test_time

    for i in range(1, count_of_tests + 1):
        reboot_switch()
        result: list = get_results(m720_ip_list)
        final = [i] + result
        with open(file_name, "a", encoding="UTF-8") as file:
            file_writer = csv.writer(file, delimiter=";", lineterminator="\r")
            file_writer.writerow(final)
    return file_name


def shutdown_interfaces_test(m720_ip_list, m720_type):
    """
    Start test with shutdown interfaces on the switch.
    :param m720_type: copper or optic m720
    :param m720_ip_list: M720 IP addresses list
    :return: file name with result
    """
    result_filename = f"link_test_shutdown_{SWITCH1_NAME}"
    file_name = create_file_with_results(result_filename, m720_type)

    one_test_time = 3  # minutes
    count_of_tests = time_for_test() // one_test_time

    for i in range(1, count_of_tests + 1):
        shutdown_switch_interfaces()
        result: list = get_results(m720_ip_list)
        final = [i] + result
        with open(file_name, "a", encoding="UTF-8") as file:
            file_writer = csv.writer(file, delimiter=";", lineterminator="\r")
            file_writer.writerow(final)
    return file_name


def power_off_test_1_2(m720_ip_list, switch1_intf_list, m720_type, m720_clocks=True,
                       check_m720_porta=False, switch2_intf_list=None):
    """
    Start test with power off switch.

    :param m720_type: copper or optic m720
    :param m720_ip_list: M720 IP addresses
    :param switch1_intf_list: interfaces on the switch1 (port b M720)
    :param m720_clocks: runs part of the code for collecting information on clocks
    by creating rc.local and the clk_ctl script on the M720 itself.
    That is, the M720 must have the clk_ctl script before starting the test.
    :param switch2_intf_list: interfaces on the switch2 (port a M720)
    :param check_m720_porta: True if test power 2, false otherwise
    :return: file name with results
    """
    # Check if the M720 is available
    _, not_ping = ping_ip_addresses(m720_ip_list)
    if not_ping:
        sys.exit(f"There are {not_ping} IP addresses that are not pinged when starting the test")
    result_filename = f"link_test_power_{SWITCH1_NAME}"

    # Create file on the device from which the script is run in the same directory.
    rpi_file = create_file_with_results(result_filename, m720_type, porta=check_m720_porta)

    if m720_clocks:
        # Create rc.local file on all M720
        with ThreadPoolExecutor(max_workers=5) as ex:
            ex.map(create_rc_local, m720_ip_list)

    # Wait until M720 is loaded
    time.sleep(60)

    one_test_time = 4  # minutes, minimum = 4 minutes
    count_of_tests = time_for_test() // one_test_time

    for i in range(1, count_of_tests + 1):
        power_off_switch()
        result: list = get_results(m720_ip_list)
        intf_b: str = check_link_on_switch(switch1_intf_list)
        final = [i, *result, intf_b]
        if check_m720_porta and switch2_intf_list:
            intf_a: str = check_link_on_switch(
                switch2_intf_list, switch_connection_data=SWITCH2_CONNECTION_DATA
            )
            final.append(intf_a)
        with open(rpi_file, "a", encoding="UTF-8") as file:
            file_writer = csv.writer(file, delimiter=";", lineterminator="\r")
            file_writer.writerow(final)

    if m720_clocks:
        # Copy csv files from M720 after testing on the device that started the script
        # It should be possible to copy files to the device from which the script is run using scp.
        # That is, it should be possible to connect to the device via ssh with a login and password.
        with ThreadPoolExecutor(max_workers=5) as ex:
            ex.map(get_results_from_m720, m720_ip_list)

    return rpi_file


def power_off_test_3(
        m720_ip_list: list, switch1_intf_list: list, current_sn_list: list, m720_type: str,
        m720_clocks: bool = True, check_m720_porta: bool = False, switch2_intf_list: object = None
) -> str:
    """
       Start test with power off switch.

       :param m720_type: copper or optic M720
       :param current_sn_list:
       :param m720_ip_list: M720 IP addresses
       :param switch1_intf_list: interfaces on the switch1 (port b M720)
       :param m720_clocks: runs part of the code for collecting information on clocks
       by creating rc.local and the clk_ctl script on the M720 itself.
       That is, the M720 must have the clk_ctl script before starting the test.
       :param switch2_intf_list: interfaces on the switch2 (port a M720)
       :param check_m720_porta: True if test power 2, false otherwise
       :return: file name with results
       """
    # Check if the M720 is available
    _, not_ping = ping_ip_addresses(m720_ip_list)
    if not_ping:
        sys.exit(f"There are {not_ping} IP addresses that are not pinged when starting the test")
    result_filename = f"link_test_power_{SWITCH1_NAME}"

    # Create file on the device from which the script is run in the same directory.
    rpi_file = create_file_with_results(result_filename, m720_type, porta=check_m720_porta)
    if m720_clocks:
        with ThreadPoolExecutor(max_workers=5) as ex:
            ex.map(create_clocks_file, current_sn_list)

    one_test_time = 4  # minutes, minimum = 4 minutes
    count_of_tests = time_for_test() // one_test_time

    for i in range(1, count_of_tests + 1):
        power_off_switch()
        result: list = get_results(m720_ip_list)
        intf_b: str = check_link_on_switch(switch1_intf_list)
        final = [i, *result, intf_b]
        if check_m720_porta and switch2_intf_list:
            intf_a: str = check_link_on_switch(
                switch2_intf_list, switch_connection_data=SWITCH2_CONNECTION_DATA
            )
            final.append(intf_a)
        with open(rpi_file, "a", encoding="UTF-8") as file:
            file_writer = csv.writer(file, delimiter=";", lineterminator="\r")
            file_writer.writerow(final)
        if m720_clocks:
            with ThreadPoolExecutor(max_workers=5) as ex:
                ex.map(get_clocks_from_m720, m720_ip_list)

    return rpi_file


def manual_test(m720_ip_list: list, switch1_intf_list: list, m720_type: str,
                check_m720_porta: bool = False, switch2_intf_list: list = None) -> str:
    """
    Start manual test.

    :param m720_type: copper or optic M720
    :param m720_ip_list: M720 IP addresses
    :param switch1_intf_list: interfaces on the switch1 (port b M720)
    :param switch2_intf_list: interfaces on the switch2 (port a M720)
    :param check_m720_porta: True if test power 2, false otherwise
    :return: file name with results
    """
    test_continue = True
    i = 1

    # Check if M720 is available
    _, not_ping = ping_ip_addresses(m720_ip_list)
    if not_ping:
        sys.exit(f"There are {not_ping} IP addresses that are not pinged when starting the test")
    result_filename = f"link_test_manual_{SWITCH1_NAME}"

    # Create file on the device from which the script is run in the same directory.
    local_file = create_file_with_results(result_filename, m720_type, porta=True)

    # Create rc.local file on all M720
    with ThreadPoolExecutor(max_workers=2) as ex:
        ex.map(create_rc_local, m720_ip_list)

    # Wait until M720 is loaded
    time.sleep(30)

    print(
        "When the modules are removed and inserted back into the switch, "
        "and wait until the modules load, then press the enter. "
        "If the test is finished input 'end'."
    )

    while test_continue:
        input_info = input(
            f"{i}. Re-insert the modules and when the modules are loaded, press enter.\n"
        )
        if input_info == "end":
            test_continue = False
        else:
            spinner = Halo(text='Loading', spinner='moon')
            spinner.start()

            # Check ping and interface status
            result: list = get_results(m720_ip_list)
            intf_b: str = check_link_on_switch(switch1_intf_list)
            final = [i, *result, intf_b]
            if check_m720_porta and switch2_intf_list:
                intf_a: str = check_link_on_switch(
                    switch2_intf_list, switch_connection_data=SWITCH2_CONNECTION_DATA
                )
                final.append(intf_a)
            with open(local_file, "a", encoding="UTF-8") as file:
                file_writer = csv.writer(file, delimiter=";", lineterminator="\r")
                file_writer.writerow(final)
            i = i + 1
            spinner.stop()

    # / Copy csv files from M720 after testing on the device that started the script
    # It should be possible to copy files to the device from which the script is run using scp.
    # That is, it should be possible to connect to the device via ssh with a login and password.
    with ThreadPoolExecutor(max_workers=2) as ex:
        ex.map(get_results_from_m720, m720_ip_list)

    return local_file


@click.command()
@click.option('--reboot', is_flag=True, help="Test with switch reboot.")
@click.option('--shutdown', is_flag=True, help="Test with interfaces shutdown on the switch.")
@click.option(
    '--power', type=click.Choice(['1', '2', '3']), help="Test with power off on the switch.")
@click.option('--type', type=click.Choice(['optic', 'copper']), help="Type of M720")
@click.option('--manual', is_flag=True, help="Manual test with injecting M720 from the switch.")
def main(reboot, shutdown, power, type, manual):
    """
    Testing the link up on the switch when connecting M720 modules.

    More info here - http://wiki.ddg/pages/viewpage.action?pageId=82710068.

    --power option parameters:
    1 - test 1 with power off on switch and checking only m720 port b
    2 - test 2 with power off on switch1 and checking m720 port a and port b
    3 - test 3 with power off on switch2 and checking m720 port a and port b
    """
    m720_type = type

    optic_ip_list = []
    optic_sn_list = []
    copper_sn_list = []
    copper_ip_list = []

    current_sn_list = []
    current_intf_list = []
    current_intf2_list = []
    current_ip_list = []

    for serial_number, interface in SWITCH1_M720.items():
        optic_sn_list.append(serial_number)
        copper_sn_list.append(serial_number)
        current_intf_list.append(interface)

    for serial_number in optic_sn_list:
        for _, value in SN_IP_DICT_OPTIC.items():
            try:
                optic_ip_list.append(value[serial_number])
            except KeyError:
                pass

    for serial_number in copper_sn_list:
        for _, value in SN_IP_DICT_RJ_45.items():
            try:
                copper_ip_list.append(value[serial_number])
            except KeyError:
                pass

    if m720_type == "optic":
        current_ip_list = optic_ip_list
        current_sn_list = optic_sn_list
    elif m720_type == "copper":
        current_ip_list = copper_ip_list
        current_sn_list = copper_sn_list

    if m720_type:
        if reboot:
            reboot_switch_test(current_ip_list, m720_type)
        elif shutdown:
            shutdown_interfaces_test(current_ip_list, m720_type)
        elif power == "1":
            # The result will be a simple, conveniently readable file with general information
            # (without information about clocks on the M720).
            filename = power_off_test_1_2(current_ip_list, current_intf_list, m720_type)
            # To get a large table with all the data, you need to call create_total_results.
            create_total_results(current_sn_list, filename, m720_type)
        elif power == "2":
            # The result will be a simple, conveniently readable file with general information
            # (without information about clocks on the M720).
            for _, interface in SWITCH2_M720.items():
                current_intf2_list.append(interface)

            filename = power_off_test_1_2(
                current_ip_list, current_intf_list, m720_type,
                check_m720_porta=True, switch2_intf_list=current_intf2_list
            )
            # To get a large table with all the data, you need to call create_total_results.
            create_total_results(current_sn_list, filename, m720_type, porta=True)
        elif power == "3":
            for _, interface in SWITCH2_M720.items():
                current_intf2_list.append(interface)

            filename = power_off_test_3(
                current_ip_list, current_intf_list, optic_sn_list, m720_type,
                check_m720_porta=True, switch2_intf_list=current_intf2_list
            )
            # To get a large table with all the data, you need to call create_total_results.
            create_total_results(current_sn_list, filename, m720_type, porta=True)
        elif manual:
            for _, interface in SWITCH2_M720.items():
                current_intf2_list.append(interface)

            # The result will be a simple, conveniently readable file with general information
            # (without information about clocks).
            file_name = manual_test(
                current_ip_list, current_intf_list, m720_type,
                check_m720_porta=True, switch2_intf_list=current_intf2_list
            )
            # To get a large table with all the data, you need to call create_total_results.
            create_total_results(current_sn_list, file_name, m720_type, porta=True)
    else:
        ctx = click.get_current_context()
        click.echo(ctx.get_help())
        ctx.exit()


if __name__ == "__main__":
    main()
