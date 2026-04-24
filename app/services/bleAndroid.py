from jnius import autoclass, PythonJavaClass, java_method
import time

BLEHelperPy = autoclass('in.daslearning.autocharge.BLEHelper')
print("BLE-AC Loaded:", BLEHelperPy)

class BLEClient:

    def __init__(self):
        self.helper = BLEHelperPy()
        self.mac_addr = None

    def connect(self, mac):
        PythonService = autoclass('org.kivy.android.PythonService')
        service = PythonService.mService
        context = service.getApplicationContext()
        self.helper.connect(context, mac)
        time.sleep(0.5)
        stat = self.helper.checkConnectStat()
        if stat:
            self.mac_addr = mac
        return True # not to retry multiple

    def send(self, msg):
        stat = self.helper.send(msg)
        return stat