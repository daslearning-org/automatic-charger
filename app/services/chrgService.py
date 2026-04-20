# from kivy/kivymd world
from kivy.utils import platform

# python's modules
from os.path import join, abspath, exists, dirname
from threading import Thread
import time

# local imports
from services.bluControl import BluetoothCon

# objects / vars
bluCon = BluetoothCon()
blue_conn_stat = False
bt_connecting = False
auto_mode_stat = False
mac_set = None
resp_template = {
    "bt": "none",
    "auto_mode": "none",
}

#### functions ####

def fire_few_off_commands():
    """ This will fire few off commands to the bt/ble device. It will be helpful for BLE devices. """
    for i in range(3):
        bluCon.send_cmd("off")
        time.sleep(0.5)

def connect_bluetooth(mac_addr:str):
    global blue_conn_stat
    global resp_template
    global mac_set
    global bt_connecting
    if len(mac_addr) == 17:
        bt_connecting = True
        blue_conn_stat = bluCon.connect_device(mac_addr)
        if blue_conn_stat:
            resp_template["bt"] = "connected"
            mac_set = mac_addr
        else:
            resp_template["bt"] = "failed"
    bt_connecting = False
