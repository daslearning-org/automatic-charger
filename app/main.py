import os
os.environ['KIVY_GL_BACKEND'] = 'sdl2'
import sys
from threading import Thread
import json
import logging
logging.getLogger("bleak").setLevel(logging.ERROR)

from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.navigationdrawer import MDNavigationDrawerMenu
from kivymd.uix.menu import MDDropdownMenu
#from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.label import MDLabel
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDFloatingActionButton

from kivy.clock import Clock
from kivy.utils import platform
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty, ObjectProperty, BooleanProperty

# IMPORTANT: Set this property for keyboard behavior
Window.softinput_mode = "below_target"

## Global definitions
__version__ = "0.0.1" # App version

# Determine the base path for your application's resources
if getattr(sys, 'frozen', False):
    # Running as a PyInstaller bundle
    base_path = sys._MEIPASS
else:
    # Running in a normal Python environment
    base_path = os.path.dirname(os.path.abspath(__file__))
kv_file_path = os.path.join(base_path, 'main_layout.kv')

# import local screens
from screens.setting import SettingsBox
from screens.init_screen import ConfigInput
from screens.control_scr import MainAppBox
from services.bluControl import BluetoothCon


# imprt local APIs / platform specific modules
if platform == "android":
    # local APIs are managed in service
    from jnius import autoclass
else:
    import psutil
    from services.chrgService import charge_svc_thread

## define custom kivymd classes
class ContentNavigationDrawer(MDNavigationDrawerMenu):
    screen_manager = ObjectProperty()
    nav_drawer = ObjectProperty()

class MainScreenBox(MDBoxLayout):
    top_pad = NumericProperty(0)
    bottom_pad = NumericProperty(0)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if platform == "android":
            try:
                from android.display_cutout import get_height_of_bar
                self.top_pad = int(get_height_of_bar('status'))
                self.bottom_pad = int(get_height_of_bar('navigation'))
            except Exception as e:
                print(f"Failed android 15 padding: {e}")
                self.top_pad = 32
                self.bottom_pad = 48

### Main App
class AutoChargeApp(MDApp):
    is_auto_mode_on = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.txt_dialog = None
        self.wake_lock = None
        self.config_template = {
            "mac": "",
            "min_charge": 30,
            "max_charge": 85,
            "auto_mode": "stop",
            "bt": "none",
            "cmd": "none",
            "alive": "true",
        }

    def build(self):
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.accent_palette = "Orange"
        return Builder.load_file(kv_file_path)

    def on_start(self):
        # OS specific setups
        if platform == "android":
            # permissions
            from android.permissions import check_permission, request_permissions, Permission
            self.sdk_version = 28
            try:
                VERSION = autoclass('android.os.Build$VERSION')
                self.sdk_version = VERSION.SDK_INT
                print(f"Android SDK: {self.sdk_version}")
            except Exception as e:
                print(f"Could not check the android SDK version: {e}")
            permissions = [
                            Permission.BLUETOOTH, 
                            Permission.BLUETOOTH_ADMIN, 
                            Permission.BLUETOOTH_CONNECT, 
                            Permission.WAKE_LOCK, 
                            Permission.FOREGROUND_SERVICE,
                            Permission.POST_NOTIFICATIONS,
                        ]
            try:
                request_permissions(permissions)
            except Exception as e:
                print(f"Error during permission grant: {e}")
            # paths on android
            context = autoclass('org.kivy.android.PythonActivity').mActivity
            android_path = context.getExternalFilesDir(None).getAbsolutePath()
            self.config_dir = os.path.join(android_path, 'config')
            self.internal_storage = android_path
            try:
                Environment = autoclass("android.os.Environment")
                self.external_storage = Environment.getExternalStorageDirectory().getAbsolutePath()
            except Exception:
                self.external_storage = os.path.abspath("/storage/emulated/0/")
            # start the listner service on Android
            try:
                self.start_service()
            except Exception as e:
                print(f"Error while starting android service: {e}")

        # for other platforms (non android)
        else:
            self.internal_storage = os.path.expanduser("~")
            self.external_storage = os.path.expanduser("~")
            self.config_dir = os.path.join(base_path, 'services', 'config')
            # start the bluetooth service
            Thread(target=charge_svc_thread, daemon=True).start()

        # all other setups
        os.makedirs(self.config_dir, exist_ok=True)
        self.config_path = os.path.join(self.config_dir, 'config.json')
        self.resp_path = os.path.join(self.config_dir, 'resp.json')
        # get existing config details
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as cf:
                old_config = json.load(cf)
            self.config_template["mac"] = old_config.get("mac", "")
            self.config_template["min_charge"] = old_config.get("min_charge", 30)
            self.config_template["max_charge"] = old_config.get("max_charge", 85)
        # initial clean other config values
        with open(self.config_path, "w") as cf:
            json.dump(self.config_template, cf)

        # local API callings
        self.bluCon = BluetoothCon(platform)
        self.blu_ok = False

        # the UI elements
        bt_mac_inp = self.root.ids.init_screen.ids.bt_mac_inp
        min_charge = self.root.ids.init_screen.ids.min_charge
        max_charge = self.root.ids.init_screen.ids.max_charge
        bt_mac_inp.text = self.config_template["mac"]
        min_charge.text = str(self.config_template["min_charge"])
        max_charge.text = str(self.config_template["max_charge"])
        self.result_txt = self.root.ids.app_box.ids.result_text

        # Threaded steps
        #Thread(target=self.battery_loop, daemon=True).start()
        Thread(target=self.dir_resp_checker, daemon=True).start()

    def start_service(self):
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        mActivity = PythonActivity.mActivity
        service = autoclass('in.daslearning.autocharge.ServiceAutochrgsvc')
        #argument = ''
        argument = os.environ.get('PYTHON_SERVICE_ARGUMENT', '')
        print(f"PYTHON_SERVICE_ARGUMENT: {argument}")
        #service.start(mActivity, argument)
        service.start(mActivity, 'icon', 'Auto Charger', 'Service Running' , argument)

    def stop_service(self):
        service = autoclass('in.daslearning.autocharge.ServiceAutochrgsvc')
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        mActivity = PythonActivity.mActivity
        service.stop(mActivity)

    def dir_resp_checker(self):
        import time
        while True:
            resp = None
            if os.path.exists(self.resp_path):
                with open(self.resp_path, "r") as rf:
                    resp = json.load(rf)
                if resp:
                    batt = resp.get("batt", "")
                    self.result_txt.text = batt
            time.sleep(2)

    def write_config(self):
        with open(self.config_path, "w") as cf:
            json.dump(self.config_template, cf)

    def connect_esp_bt(self): # an auto connection logic to be set later
        bt_mac_inp = self.root.ids.init_screen.ids.bt_mac_inp
        tmp_mac = str(bt_mac_inp.text)
        tmp_mac = tmp_mac.strip()
        if len(tmp_mac) == 17: # also a : check to be added
            self.config_template["mac"] = tmp_mac
            self.config_template["bt"] = "connect"
            self.write_config()
            Thread(target=self.bt_connect_checker, daemon=True).start()
        else:
            self.show_toast_msg("Please enter a valid BT MAC or choose one from Paired Devices!", is_error=True)

    def bt_connect_checker(self):
        import time
        time.sleep(2)
        resp = None
        if os.path.exists(self.resp_path):
            with open(self.resp_path, "r") as rf:
                resp = json.load(rf)
            if resp:
                resp_bt = resp.get("bt", "")
                if resp_bt == "connected":
                    Clock.schedule_once(lambda dt: self.show_toast_msg("Bluetooth is connected"))
                    self.blu_ok = True
                elif resp_bt == "failed":
                    Clock.schedule_once(lambda dt: self.show_toast_msg("Bluetooth connection failed!", is_error=True))
                elif resp_bt == "none":
                    Clock.schedule_once(lambda dt: self.show_toast_msg("Connection is not yet complete...", is_error=True, duration=2))
                    #self.bt_connect_checker()

    def list_bl_devices(self, button):
        is_bl_on = self.bluCon.bl_on()
        if is_bl_on:
            devices_list = self.bluCon.list_devices()
            if len(devices_list) >= 1:
                menu_items = [
                    {
                        "text": f"{name}, {addr}",
                        "leading_icon": "bluetooth",
                        "on_release": lambda x=addr: self.set_bl_mac(x),
                        "font_size": sp(36)
                    } for name, addr in devices_list
                ]
                self.bl_list_menu = MDDropdownMenu(
                    items=menu_items,
                )
                caller_inst = self.root.ids.init_screen.ids.bt_list_btn_lbl
                self.bl_list_menu.caller = caller_inst
                self.bl_list_menu.open()
            else:
                self.show_toast_msg("No Paired BT devices found!", is_error=True)
        else:
            self.bluCon.request_enable_bl()

    def set_bl_mac(self, mac:str = ""):
        if self.bl_list_menu:
            self.bl_list_menu.dismiss()
        bt_mac_inp = self.root.ids.init_screen.ids.bt_mac_inp
        if len(mac) == 17:
            bt_mac_inp.text = mac
            self.config_template["mac"] = mac

    def goto_charge_mgr(self, confirm=False, instance=None):
        if confirm or self.blu_ok:
            try:
                min_charge = int(self.root.ids.init_screen.ids.min_charge.text)
                max_charge = int(self.root.ids.init_screen.ids.max_charge.text)
                if max_charge > min_charge:
                    self.config_template["min_charge"] = min_charge
                    self.config_template["max_charge"] = max_charge
                    Thread(target=self.write_config, daemon=True).start() # write the values
                else:
                    self.show_toast_msg("Maximum charge percentage should be greater than Minimum!", is_error=True)
                    self.txt_dialog_closer(instance)
                    return
            except Exception as e:
                self.show_toast_msg(f"Error setting max/min charge value, default will be used.", is_error=True)
            self.root.ids.screen_manager.current = "mainAppScr"
            self.txt_dialog_closer(instance)
        else:
            buttons = [
                MDFlatButton(
                    text="Cancel",
                    theme_text_color="Custom",
                    text_color=self.theme_cls.primary_color,
                    on_release=self.txt_dialog_closer
                ),
                MDFlatButton(
                    text="GO",
                    theme_text_color="Custom",
                    text_color="green",
                    on_release=self.goto_charge_mgr
                ),
            ]
            self.show_text_dialog(
                "No ESP Connected!", # subject
                "ESP Navigation module is not connected. Do you still want to proceed?", # body
                buttons
            )

    def toggle_auto_mode(self):
        toggle_btn = self.root.ids.app_box.ids.start_listener_btn
        if self.is_auto_mode_on:
            self.config_template["auto_mode"] = "stop"
            self.write_config()
            self.is_auto_mode_on = False
            toggle_btn.text = "Sart Auto Mode"
            toggle_btn.icon = "play"
            toggle_btn.md_bg_color = "gray"
        else:
            self.config_template["auto_mode"] = "start"
            self.write_config()
            self.is_auto_mode_on = True
            toggle_btn.text = "Stop Auto Mode"
            toggle_btn.icon = "stop"
            toggle_btn.md_bg_color = "orange"

    def get_battery_details(self):
        battery_pct = 0
        # OS specific setups
        if platform == "android":
            # get battery details
            activity = autoclass('org.kivy.android.PythonActivity').mActivity
            IntentFilter = autoclass('android.content.IntentFilter')
            BatteryManager = autoclass('android.os.BatteryManager')
            intent = activity.registerReceiver(
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

    def battery_loop(self):
        import time
        while True:
            battery_pct, plugged_in = self.get_battery_details()
            self.result_txt.text = f"Battery: {battery_pct}, plugged in: {'Yes' if plugged_in else 'No'}"
            time.sleep(2)

    def show_toast_msg(self, message, is_error=False, duration=3):
        from kivymd.uix.snackbar import MDSnackbar
        bg_color = (0.2, 0.6, 0.2, 1) if not is_error else (0.8, 0.2, 0.2, 1)
        MDSnackbar(
            MDLabel(
                text = message,
                font_style = "Subtitle1"
            ),
            md_bg_color=bg_color,
            y=dp(24),
            pos_hint={"center_x": 0.5},
            duration=duration
        ).open()

    def show_text_dialog(self, title, text="", buttons=[]):
        self.txt_dialog = MDDialog(
            title=title,
            text=text,
            buttons=buttons
        )
        self.txt_dialog.open()

    def txt_dialog_closer(self, instance):
        if self.txt_dialog:
            self.txt_dialog.dismiss()

    def open_link(self, instance, url):
        import webbrowser
        webbrowser.open(url)

    def update_link_open(self, instance):
        self.txt_dialog_closer(instance)
        self.open_link(instance=instance, url="https://github.com/daslearning-org/navigation-indicator/releases")

    def update_checker(self, instance=None):
        buttons = [
            MDFlatButton(
                text="Cancel",
                theme_text_color="Custom",
                text_color=self.theme_cls.primary_color,
                on_release=self.txt_dialog_closer
            ),
            MDFlatButton(
                text="Releases",
                theme_text_color="Custom",
                text_color="green",
                on_release=self.update_link_open
            ),
        ]
        self.show_text_dialog(
            "Check for update",
            f"Your version: {__version__}",
            buttons
        )

    ## run on app exit
    def on_stop(self):
        print("Exiting the app...")
        if platform == "android":
            self.stop_service()

if __name__ == '__main__':
    AutoChargeApp().run()
