#import subprocess
from bleak import BleakClient, BleakScanner

async def get_nearby_devices():
    """
    This function will get the list of paired Bletooth devices on Linux.

    Args: 
        None

    Returns:
        list(touple): list of paired devices like (bt_name, mac)
    """

    bt_list = []
    try:
        devices = await BleakScanner.discover()
        for device in devices:
            if len(device) >= 17 and device.count(":") >= 5:
                mac = device[0:17]
                first_space = device.find(" ")
                name = device[first_space+1:]
                bt_list.append((name, mac))

    except Exception as e:
       print(f"Error executing ble list: {e}")
    return bt_list

class LinuxBle:

    def __init__(self):
        self.mac_addr = None
        self.client = None
        self.char_uuid = None

    async def connect(self, mac:str):
        try:
            device = await BleakScanner.find_device_by_address(mac, timeout=10.0)
            if not device:
                print(f"Your device {mac} is not found under Bluetooth range!")
                return False

            self.client = BleakClient(mac, disconnected_callback=self.handle_disconnect)
            await self.client.connect()
            self.mac_addr = mac

            for service in self.client.services:
                for char in service.characteristics:
                    if char.uuid.startswith("beb5483e"):
                        self.char_uuid = char.uuid
                        return True
        except Exception as e:
            print(f"BLE Linux connection error: {e}")
        # if loop cannot find the correct uuid
        return False

    def handle_disconnect(self):
        print("BLE disconnected")
        self.mac_addr = None
        self.client = None
        self.char_uuid = None

    async def send(self, message:str):
        if self.client and self.char_uuid:
            try:
                msg_byte = message.encode('utf-8')
                await self.client.write_gatt_char(self.char_uuid, msg_byte, response=True)
                return True
            except Exception as e:
                print(f"BLE message send error: {e}")
        else:
            print("The BLE connection is not proper, please connect the device again")
        return False

