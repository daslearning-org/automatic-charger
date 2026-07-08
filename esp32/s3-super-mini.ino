#include <ArduinoJson.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>
//#include <esp_system.h>

// UUIDs for BLE
#define SERVICE_UUID        "4fafc201-2fb5-459e-8fcc-c5c9c331914b"
#define CHARACTERISTIC_UUID "beb5483e-36e3-2688-b7f5-ea07361b26a8" // this is the write UUID

//** Global variables */
const int chargePin = 4;

// Flags
bool deviceConnected = false;
bool oldDeviceConnected = false;
BLEServer* pServer = nullptr;

// Charger controls
bool modeSelected = false;
String bleValue = "none";

//** Function definitions */

// bluetooth
class MyCallbacks: public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic *pCharacteristic) {
    String value = pCharacteristic->getValue();

    if (value.length() > 0) {
      bleValue = value;
    }
  }
};

class MyServerCallbacks: public BLEServerCallbacks {
  void onConnect(BLEServer* pServer) {
    deviceConnected = true;
    Serial.println("Client Connected");
  }

  void onDisconnect(BLEServer* pServer) {
    deviceConnected = false;
    Serial.println("Client Disconnected");
  }
};

void setup(){
  // Setup the ESP32 board after boot
  Serial.begin(115200);
  Serial.println("Serial started");

  // initialize digital pin led as an output
  pinMode(chargePin, OUTPUT);

  BLEDevice::init("AutoChrgBle");
  pServer = BLEDevice::createServer(); // now global
  pServer->setCallbacks(new MyServerCallbacks());

  BLEService *pService = pServer->createService(SERVICE_UUID);

  BLECharacteristic *pCharacteristic = pService->createCharacteristic(
                                         CHARACTERISTIC_UUID,
                                         BLECharacteristic::PROPERTY_READ |
                                         BLECharacteristic::PROPERTY_WRITE
                                       );

  pCharacteristic->setCallbacks(new MyCallbacks());
  pCharacteristic->setValue("Navigation Indicator");
  pService->start();
  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->start();
  Serial.println("BLE Ready, now you can pair it with bluetooth! \n");

}

void loop(){
  // The main loop

  if(modeSelected){
    digitalWrite(chargePin, HIGH);
  }
  else{
    digitalWrite(chargePin, LOW);
  }

  if (bleValue != "none") { // input from BLE
    bleValue.trim();
    bleValue.toLowerCase();
    Serial.println("Entered text: " + bleValue); // Debug
    if (bleValue == "on"){
      modeSelected = true;
    }
    else if(bleValue == "off"){
      modeSelected = false;
    }
    bleValue = "none";
  }

  // Handle disconnect
  if (!deviceConnected && oldDeviceConnected) {
    Serial.println("Disconnected detected in loop");
    delay(500);  // allow BLE stack to settle
    pServer->startAdvertising();   // Start broadcasting again
    Serial.println("BLE re-advertise started..");
    oldDeviceConnected = deviceConnected;
  }

  // Handle new connection
  if (deviceConnected && !oldDeviceConnected) {
    oldDeviceConnected = deviceConnected;
  }

}
