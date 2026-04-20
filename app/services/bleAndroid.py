from jnius import autoclass, PythonJavaClass, java_method
#from android import mActivity

BLEHelperPy = autoclass('in.daslearning.autocharge.BLEHelper')
print("Loaded:", BLEHelperPy)

#class MyBLEListener(PythonJavaClass):
#    __javainterfaces__ = ['in/daslearning/navindi/BLEListener']
#
#    def __init__(self):
#        super().__init__()
#
#    @java_method('()V')
#    def onConnected(self):
#        print("Connected to ESP32")
#
#    @java_method('()V')
#    def onReady(self):
#        print("BLE ready (write characteristic found)")
#
#    @java_method('(Ljava/lang/String;)V')
#    def onMessage(self, msg):
#        print("Received:", msg)


class BLEClient:

    def __init__(self):
        self.helper = BLEHelperPy()
        self.mac_addr = None

    def connect(self, mac):
        PythonService = autoclass('org.kivy.android.PythonService')
        service = PythonService.mService
        context = service.getApplicationContext()
        self.helper.connect(context, mac)
        self.mac_addr = mac

    def send(self, msg):
        self.helper.send(msg)