#from kivy.clock import Clock
import asyncio

class BluetoothCon():

    def __init__(self, platform:str = "android"):
        self.platform = platform
        self.connect_ok = False
        self.ble_device = False
        self.ble_client = None
        self.mac_addr = None

    def bl_on(self):
        stat = False
        if self.platform == "android":
            try:
                from jnius import autoclass
                BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
                bt_adapter = BluetoothAdapter.getDefaultAdapter()
                if bt_adapter and bt_adapter.isEnabled():
                    stat = True
            except Exception as e:
                print(f"Error while checking bluetooth on/off status: {e}")
        else: # need to put a logic for linux & windows
            stat = True
        return stat

    def request_enable_bl(self):
        stat = False
        if self.platform == "android":
            bl_on = self.bl_on()
            if bl_on:
                return True
            try:
                from jnius import autoclass
                #from android import activity
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
                REQUEST_ENABLE_BT = 1
                bt_adapter = BluetoothAdapter.getDefaultAdapter()
                enableBtIntent = Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE)
                PythonActivity.mActivity.startActivityForResult(enableBtIntent, REQUEST_ENABLE_BT)
                stat = True
            except Exception as e:
                print(f"Error while turning bluetooth ON: {e}")
        return stat

    def list_devices(self):
        result = []
        if self.platform == "android":
            try:
                from jnius import autoclass
                BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
                bt_adapter = BluetoothAdapter.getDefaultAdapter()
                devices = bt_adapter.getBondedDevices().toArray()
                for dev in devices:
                    name = dev.getName()
                    addr = dev.getAddress()
                    result.append((name, addr))
            except Exception as e:
                print(f"Error in Bluetooth device listing: {e}")
        else:
            from services.bleLinux import get_nearby_devices
            result = asyncio.run(get_nearby_devices())
        return result

    def check_bt_type(self, mac:str):
        """Checks whether the given mac is a BLE device or a classic BT"""
        if self.platform == "android":
            from jnius import autoclass
            BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
            BluetoothDevice = autoclass('android.bluetooth.BluetoothDevice')
            adapter = BluetoothAdapter.getDefaultAdapter()
            device = adapter.getRemoteDevice(mac)
            device_type = device.getType()
            if device_type == BluetoothDevice.DEVICE_TYPE_CLASSIC:
                print(f"{mac} - It's a classic BT")
                self.ble_device = False
            elif device_type == BluetoothDevice.DEVICE_TYPE_LE:
                print(f"{mac} - It's a BLE")
                self.ble_device = True
            elif device_type == BluetoothDevice.DEVICE_TYPE_DUAL:
                print(f"{mac} - It has both classic & BLE")
                self.ble_device = True
            else:
                # Should be classic
                print(f"{mac} - BT type check not in category!")
                self.ble_device = False
        else:
            self.ble_device = True # Only BLE mode is supported on Desktop platforms
        return self.ble_device

    def connect_device(self, mac:str):
        print(f"MAC connect request: {mac}")
        if self.platform == "android":
            try:
                ble_device = self.check_bt_type(mac)
                if ble_device: # BLE device
                    from services.bleAndroid import BLEClient
                    self.ble_client = BLEClient()
                    self.ble_client.connect(mac)
                    self.mac_addr = mac
                    self.connect_ok = True
                else: # classic BT
                    from jnius import autoclass
                    BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
                    UUID = autoclass('java.util.UUID')
                    SPP_UUID = "00001101-0000-1000-8000-00805F9B34FB"
                    bt_adapter = BluetoothAdapter.getDefaultAdapter()
                    device = bt_adapter.getRemoteDevice(mac)
                    socket = device.createRfcommSocketToServiceRecord(
                        UUID.fromString(SPP_UUID)
                    )
                    socket.connect()
                    self.bt_out = socket.getOutputStream()
                    bt_in = socket.getInputStream() # to be implemented with a heartbeat
                    print("Connected to: ", mac)
                    self.mac_addr = mac
                    self.connect_ok = True
            except Exception as e:
                print(f"Error while conencting to ESP32: {e}")
                self.connect_ok = False
        # for Linux OS
        else:
            from services.bleLinux import LinuxBle
            self.ble_client = LinuxBle()
            self.connect_ok = self.ble_client.connect(mac)
            print(f"Connect ok: {self.connect_ok}")

        return self.connect_ok

    def check_bl_stat(self):
        """Check if bluetooth connection is fine: returns Bool"""
        return self.connect_ok

    def send_cmd(self, cmd:str, *args):
        stat = False
        if self.platform == "android" and self.connect_ok:
            try:
                if self.ble_device: # BLE device
                    if self.ble_client:
                        self.ble_client.send(cmd)
                        stat = True
                    else:
                        self.connect_ok = False
                else: # classic device
                    self.bt_out.write(bytearray(cmd + "\n", 'utf-8'))
                    stat = True
            except Exception as e:
                print(f"Error while send msg to ESP: {e}")
                self.connect_ok = False
        # for linux
        elif self.connect_ok:
            stat = self.ble_client.send(cmd)
            if not stat:
                self.connect_ok = False

        return stat
