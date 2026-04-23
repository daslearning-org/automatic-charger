#import subprocess
from bleak import BleakClient, BleakScanner
import asyncio
from threading import Thread

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
            bt_list.append((device.name, device.address))
    except Exception as e:
       print(f"Error executing ble list: {e}")
    return bt_list

class LinuxBle:

    def __init__(self):
        self.mac_addr = None
        self.client = None
        self.char_uuid = None
        self.loop = asyncio.new_event_loop()
        self.thread = Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def run_task(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self.loop)

    def connect(self, mac:str):
        if self.client and self.client.is_connected:
            return True
        return asyncio.run_coroutine_threadsafe(
            self._connect(mac), self.loop
        ).result()

    async def _connect(self, mac:str):
        try:
            self.client = BleakClient(mac, disconnected_callback=self.handle_disconnect)
            await self.client.connect()
            self.mac_addr = mac

            for service in self.client.services:
                for char in service.characteristics:
                    if char.uuid.startswith("beb5483e"):
                        self.char_uuid = char.uuid
                        print(f"BLE connected with UUID: {self.char_uuid}")
                        return True
        except Exception as e:
            print(f"BLE Linux connection error: {e}")
        # if loop cannot find the correct uuid
        return False

    def handle_disconnect(self, instance=None):
        print("BLE disconnected")
        self.mac_addr = None
        self.client = None
        self.char_uuid = None

    def send(self, message:str):
        return asyncio.run_coroutine_threadsafe(
            self._send(message), self.loop
        ).result()

    async def _send(self, message:str):
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

