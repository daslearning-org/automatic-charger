# from kivy/kivymd world
from kivy.utils import platform

# python's modules
from os.path import join, abspath, exists, dirname
#from threading import Thread
import time
import sys
import json

# imprt local APIs / platform specific modules
if platform == "android":
    # local APIs are managed in service
    from jnius import autoclass
    # set path
    try:
        service = autoclass('org.kivy.android.PythonService').mService
        context = service.getApplicationContext()
        android_path = context.getExternalFilesDir(None).getAbsolutePath()
        config_dir = join(android_path, 'config')
        #Log = autoclass('android.util.Log')
    except Exception as e:
        config_dir = abspath("/storage/emulated/0/Android/data/in.daslearning.autocharge/files/config/")
        print(f"Error while accessing app internal path: {e}")
else:
    import psutil
    import logging
    logging.getLogger("bleak").setLevel(logging.ERROR)
    # Determine the base path for your application's resources
    if getattr(sys, 'frozen', False):
        # Running as a PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # Running in a normal Python environment
        base_path = dirname(abspath(__file__))
    config_dir = join(base_path, 'config')
config_file = join(config_dir, "config.json")
resp_file = join(config_dir, "resp.json")

# local imports
from services.bluControl import BluetoothCon

# objects / vars
bluCon = BluetoothCon(platform)
blue_conn_stat = False
bt_connecting = False
auto_mode = False
mac_set = None
last_cmd = "none"
min_charge = 30
max_charge = 85
config_data = {}
resp_template = {
    "bt": "none",
    "auto_mode": "none",
    "batt": "none",
}

#### functions ####

def fire_few_off_commands():
    """ This will fire few OFF commands to the bt/ble device. It will be helpful for BLE devices. """
    bt_check = bluCon.check_bl_stat()
    if not bt_check and mac_set:
        connect_bluetooth(mac_set)
    for i in range(3):
        bluCon.send_cmd("off")
        time.sleep(0.5)

def fire_few_on_commands():
    """ This will fire few ON commands to the bt/ble device. It will be helpful for BLE devices. """
    bt_check = bluCon.check_bl_stat()
    if not bt_check and mac_set:
        connect_bluetooth(mac_set)
    for i in range(3):
        bluCon.send_cmd("on")
        time.sleep(0.5)

def connect_bluetooth(mac_addr:str):
    global blue_conn_stat
    global resp_template
    global mac_set
    global bt_connecting
    bt_check = False
    if len(mac_addr) == 17:
        mac_set = mac_addr
        bt_connecting = True
        blue_conn_stat = bluCon.connect_device(mac_addr)
        for i in range(7):
            time.sleep(0.5)
            bt_check = bluCon.check_bl_stat()
            if bt_check:
                blue_conn_stat = bt_check
                resp_template["bt"] = "connected"
                break
        if not bt_check:
            resp_template["bt"] = "failed"
        write_resp()
    bt_connecting = False

def get_battery_details():
    battery_pct = 0
    # OS specific setups
    if platform == "android":
        # get battery details
        PythonService = autoclass('org.kivy.android.PythonService')
        IntentFilter = autoclass('android.content.IntentFilter')
        BatteryManager = autoclass('android.os.BatteryManager')
        context = PythonService.mService 
        intent = context.registerReceiver(
            None,
            IntentFilter('android.intent.action.BATTERY_CHANGED')
        )
        level = intent.getIntExtra(BatteryManager.EXTRA_LEVEL, -1)
        scale = intent.getIntExtra(BatteryManager.EXTRA_SCALE, -1)
        battery_pct = (level / float(scale)) * 100
        print(f"Battery: {battery_pct:.2f}%")
        # check if charging is happening
        plugged = intent.getIntExtra(BatteryManager.EXTRA_PLUGGED, -1)
        is_usb = plugged == BatteryManager.BATTERY_PLUGGED_USB
        is_ac = plugged == BatteryManager.BATTERY_PLUGGED_AC
        is_wireless = plugged == BatteryManager.BATTERY_PLUGGED_WIRELESS
        power_plugged = is_usb or is_ac or is_wireless
        print("Plugged:", power_plugged)
        print("USB:", is_usb, "AC:", is_ac, "Wireless:", is_wireless)
        #another method
        status = intent.getIntExtra(BatteryManager.EXTRA_STATUS, -1)
        is_charging = (
            status == BatteryManager.BATTERY_STATUS_CHARGING or
            status == BatteryManager.BATTERY_STATUS_FULL
        )
        print("Plugged (alternative): ", is_charging)
    else:
        # Get battery details
        battery = psutil.sensors_battery()
        if battery:
            battery_pct = battery.percent
            power_plugged = battery.power_plugged
            # Simple output
            print(f"Battery Percentage: {battery_pct}%")
            print(f"Power Plugged: {'Yes' if power_plugged else 'No'}")
        else:
            print("Battery information could not be retrieved.")
    return battery_pct, power_plugged

def read_config_file():
    """ Read the command file from file (Instrunctions from main app). """
    global config_data
    if exists(config_file):
        try:
            with open(config_file, "r") as cf:
                config_data = json.load(cf)
        except Exception as e:
            print(f"Error while reading config from svc: {e}")

def write_resp():
    """ Write the response json on file. """
    global resp_template
    with open(resp_file, "w") as rf:
        json.dump(resp_template, rf)

def charge_svc_thread():
    global auto_mode
    global config_file
    global resp_file
    global blue_conn_stat
    global min_charge
    global max_charge
    global last_cmd

    write_resp()

    # keep alive the service & check for requests
    while True:
        read_config_file()

        # handle bluetooth connect
        mac_addr = config_data.get("mac", "")
        bt_req = config_data.get("bt", "")
        if not blue_conn_stat and not bt_connecting and len(mac_addr) == 17 and bt_req == "connect":
            connect_bluetooth(mac_addr)

        # auto control
        control = config_data.get("auto_mode", "")
        if control == "start" and not auto_mode:
            auto_mode = True
        elif control == "stop" and auto_mode:
            auto_mode = False

        # set min/max charge
        tmp_min_charge = int(config_data.get("min_charge", 30))
        tmp_max_charge = int(config_data.get("max_charge", 85))
        if tmp_min_charge != min_charge:
            min_charge = tmp_min_charge
        if tmp_max_charge != max_charge:
            max_charge = tmp_max_charge

        # check battery & take action
        if auto_mode:
            battery_pct, plugged_in = get_battery_details()
            resp_template["batt"] = f"Battery: {battery_pct}, plugged in: {'Yes' if plugged_in else 'No'}"
            print(resp_template["batt"]) # debug
            if battery_pct >= max_charge and plugged_in:
                fire_few_off_commands()
            elif battery_pct <= min_charge and not plugged_in:
                fire_few_on_commands()
            write_resp()

        # manucal command
        command = config_data.get("cmd", "none")
        if command == "on" and command != last_cmd:
            last_cmd= command
            fire_few_on_commands()
        if command == "off" and command != last_cmd:
            last_cmd= command
            fire_few_off_commands()

        # put a sleep
        time.sleep(2)

if __name__ == "__main__":
    # start the main thread
    charge_svc_thread()
