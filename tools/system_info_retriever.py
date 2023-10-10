import getpass
import os
import platform

import requests
from scapy.layers.l2 import ARP, Ether
from scapy.sendrecv import srp

from tools.code_execution import run_cmd_command


class System:
    def __init__(self):
        # It is not needed to create variables
        pass

    @staticmethod
    def talked_to_these_ips():
        # Now we are using the arp -a in the CMD to retrieve the last talked ips
        print('\n\nRetrieving last IP addresses...')
        arp_response = run_cmd_command('arp -a')
        return (f"Talked to these IP's recently:\n\n"
                f"{arp_response}\n"
                f"-----------------------------------\n")



    @staticmethod
    def get_system_info():
        """
        Retrieve system information and format it as a string.

        Returns:
            str: System information as a formatted string.
        """
        system_info = {}
        string = 'System Information:\n\n'

        # Get system information using platform module
        system_info['System'] = platform.system()
        system_info['Node Name'] = platform.node()
        system_info['User'] = getpass.getuser()
        system_info['User Directory'] = os.path.expanduser('~')
        system_info['Release'] = platform.release()
        system_info['Version'] = platform.version()
        system_info['Machine'] = platform.machine()
        system_info['Processor'] = platform.processor()

        # Format system information as a string
        for key, value in system_info.items():
            string += f"{key}: {value}\n"

        string += '\n-----------------------------------\n'

        return string

    @staticmethod
    def scan_network(ip_range='192.168.1.0/24', iface='wlan0'):
        """
        Scan the network to discover devices and their IP addresses.

        Args:
            ip_range (str): The IP range to scan (e.g., '192.168.1.0/24').
            iface (str): The network interface to use for sending ARP requests.

        Returns:
            list: List of dictionaries containing device information.
        """
        devices = []

        print('Scanning network...')
        splitted_ip, subnet_mask = ip_range.split('/')
        subnet_mask = int(subnet_mask)
        base_ip = '.'.join(splitted_ip.split('.')[:-1])  # Extract base IP without the last octet

        # Calculate the number of IP addresses in the subnet
        num_addresses = 2 ** (32 - subnet_mask)

        # Loop through possible IP addresses in the subnet
        for i in range(1, num_addresses - 1):  # Exclude network and broadcast addresses
            target_ip = f"{base_ip}.{i}"
            print(f"Scanning IP: {target_ip}")

            response = srp(Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=target_ip), timeout=2, verbose=False, iface=iface)[
                0]
            answered_list = response[0]

            # Extract device information from responses
            for element in answered_list:
                device_info = {"ip": element[1].psrc, "mac": element[1].hwsrc}
                devices.append(device_info)

        print('Scan completed.')

        return devices


    @staticmethod
    def get_ip_location():
        """
        Retrieve IP address and its location information and format it as a string.

        Returns:
            str: IP address and location information as a formatted string.
        """
        ip_info = {}
        string = 'Agent Location Data:\n\n'

        # Retrieve public IP using ipify.org
        response = requests.get('https://api.ipify.org?format=json')
        ip_info['IP'] = response.json()['ip']

        # Retrieve IP location using ip-api.com
        response = requests.get(f"http://ip-api.com/json/{ip_info['IP']}")
        location_data = response.json()
        if response.status_code == 200 and location_data['status'] == 'success':
            ip_info['Country'] = location_data['country']
            ip_info['State'] = location_data['regionName']
            ip_info['City'] = location_data['city']
        else:
            print("Failed to retrieve IP location information.")

        # Format IP and location information as a string
        for key, value in ip_info.items():
            string += f"{key}: {value}\n"
        string += '\n-----------------------------------\n'

        return string
