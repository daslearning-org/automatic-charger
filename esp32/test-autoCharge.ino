#include <FastLED.h>
#include <ArduinoJson.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>
//#include <esp_system.h>

#include "LittleFS.h"

#define NUM_LEDS 1
#define DATA_PIN 48 // on esp32-s3 super mini
#define SERVICE_UUID        "4fafc201-2fb5-459e-8fcc-c5c9c331914b"
#define CHARACTERISTIC_UUID "beb5483e-36e3-4688-b7f5-ea07361b26a8"

//** Global variables */

// configs
const char* CONFIG_FILE = "/config.json";

struct Config {
  String ssid;
  String wifipass;
  String stearing;
  String mode;
};
Config appConfig;

// Flags
bool ledState = false;
bool deviceConnected = false;
bool oldDeviceConnected = false;
BLEServer* pServer = nullptr;

// LED controls
CRGB leds[NUM_LEDS];
bool modeSelected = false;
String bleValue = "none";

// timer
unsigned long previousMillis = 0;
int interval = 800; // Can be changed programatically

//** Function definitions */

// Initialize the LittleFS
void initFS(){
  if (!LittleFS.begin()) {
  Serial.println("An error has occurred while mounting LittleFS!");
  }
  else{
  Serial.println("LittleFS mounted successfully");
  }
}

// Function to read the configuration from LittleFS
bool readConfigFile() {
  File configFile = LittleFS.open(CONFIG_FILE, "r");
  if (!configFile) {
    Serial.println("Failed to open config file for reading. File might not exist.");
    return false;
  }

  size_t size = configFile.size();
  if (size == 0) {
    Serial.println("Config file is empty.");
    configFile.close();
    return false;
  }

  StaticJsonDocument<256> doc; // Adjust size based on your JSON's complexity

  // Deserialize the JSON document
  DeserializationError error = deserializeJson(doc, configFile);
  configFile.close(); // Close the file after reading

  if (error) {
    Serial.print(F("deserializeJson() failed: "));
    Serial.println(error.f_str());
    return false;
  }

  // Extract values from the JSON document
  appConfig.ssid = doc["ssid"] | "";
  appConfig.wifipass = doc["wifipass"] | "";
  appConfig.stearing = doc["stearing"] | "right";
  appConfig.mode = doc["mode"] | "";

  return true;
}

// Function to save the configuration to LittleFS
bool saveConfigFile() {
  File configFile = LittleFS.open(CONFIG_FILE, "w"); // Open in write mode, will create if not exists or overwrite
  if (!configFile) {
    Serial.println("Failed to open config file for writing.");
    return false;
  }

  StaticJsonDocument<256> doc; // Adjust size based on your JSON's complexity

  // Populate the JSON document from the config struct
  doc["ssid"] = appConfig.ssid;
  doc["wifipass"] = appConfig.wifipass;
  doc["stearing"] = appConfig.stearing;
  doc["mode"] = appConfig.mode;

  // Serialize JSON to file
  if (serializeJson(doc, configFile) == 0) {
    Serial.println(F("Failed to write to file"));
    configFile.close();
    return false;
  }
  configFile.close();
  return true;
}

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

void stopLED(){ // turn of the display
  FastLED.clear();
  FastLED.show();
}

void setup(){
  // Setup the ESP32 board after boot
  Serial.begin(115200);
  Serial.println("Serial started");
  FastLED.addLeds<WS2812,DATA_PIN,GRB>(leds,NUM_LEDS);
  FastLED.clear();
  FastLED.setBrightness(10); // : default
  initFS();
  BLEDevice::init("EspMiniBle");
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
  if(readConfigFile()){
    Serial.println("App config: " + appConfig.mode); // to be used when config is needed
  }
}

void loop(){
  // The main loop

  // This will get replaced by simple on off via GPIO PIN.
  if (modeSelected && ledState){
    leds[0] = CRGB::Green;
    FastLED.show();
  }
  else{
    stopLED();
  }

  if (bleValue != "none") { // input from BLE
    bleValue.trim();
    bleValue.toLowerCase();
    Serial.println("Entered text: " + bleValue); // Debug
    if (bleValue == "on"){
      stopLED();
      modeSelected = true;
    }
    else if(bleValue == "off"){
      stopLED();
      modeSelected = false;
    }
  }

  // Timer loop (not needed for actual use case)
  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;
    ledState = !ledState;
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
