# 🔋 Automatic Charger for Mobile & Computer 🔌
Turn on / off your laptop or mobile charger using the threshold values. The smart charger will be equipped with an ESP32 microcontroller. This application should work on Android, Linux &amp; Windows.

## 💰 Sponsor Me
You can buy me a coffee via [this link](https://www.paypal.com/paypalme/soomnathsdas) or tap on below image. Thank you 🙏. <br>
<a href="https://www.paypal.com/paypalme/soomnathsdas"><img src="./docs/images/donate.svg" height="40"></a>

## 📽️ Demo
Demo is coming soon...

## 🧑‍💻 Quickstart Guide
Follow this Quick Guide to setup your Automatic Charger.
If wish to get the purchase links & more details, check the [official blog](https://blog.daslearning.in/microcontroller/esp32/automatic-charger.html)

### 🦾 ESP32 Setup
We are using `BLE` (low energy) to communicate from android device to an ESP32 controlled smart charger (DIY).

#### 📦 Arduino Setup
If you want to learn about setting up your ESP32 environment in `Arduino IDE`, you may follow this [fantastic guide](https://randomnerdtutorials.com/installing-the-esp32-board-in-arduino-ide-windows-instructions/).

1. Connect your ESP32 board to your computer with a USB cable.

2. Select proper ESP32 board type from `Tools` > `Boards` selection.

3. Select your USB Serial port in `Tools` > `Port`.

#### 🖧 ESP32 Setup
Diagram will be added soon. Only one GPIO pin will be enough.

1. Upload this [sketch](./esp32/autoCharge.ino) on your ESP32 from `Arduino IDE`. You should check & use GPIO pin depending on chosen model.

### 📱 Automatic Charger on Android

1. Download the [latest apk](https://github.com/daslearning-org/automatic-charger/releases) and install.

2. After launching the app, grant the permissions that are prompted on screen.

3. Turn ON `Bluetooth` on your phone & just pair `AutoChrgBle` (ESP32 should be on).

4. Now you can list the paired devices from the app & choose the above one & Connect.

5. Set your minimum & maximum charge values to on & off the charger accordingly. Then click on Proceed.

6. Check if you are able to turn on/off using the manual button. If yes, then you can turn on the `Auto Mode`, if it doesn't work, relaunch the app & try to connect the device.

### 💻 Automatic Charger on Windows or Linux

1. Download the [latest app](https://github.com/daslearning-org/automatic-charger/releases) and run/install it. (.exe for windows & the file named Linux for Linux)

2. Turn on bluetooth on your computer.

3. Now you can list the paired devices from the app, select `AutoChrgBle` & Connect.

4. Set your minimum & maximum charge values to on & off the charger accordingly. Then click on Proceed.

5. Check if you are able to turn on/off using the manual button. If yes, then you can turn on the `Auto Mode`.

### 🐍 Run with Python
You can also directly use `Python` on your computer & skip the installation process. Steps remain same as above.

1. Clone the repo
```bash
git clone https://github.com/daslearning-org/automatic-charger.git
```

2. Run the application
```bash
cd automatic-charger/app/
pip install -r requirements.txt # virtual environment is recommended
python main.py
```

---

## Troubleshoot

1. Get the app processes
```bash
adb shell ps | grep autoc
u0_a83       17299  1116    9378680 230596 0                   0 S in.daslearning.autocharge
u0_a83       17537  1116    8806568 115372 0                   0 S in.daslearning.autocharge:service_autochrgsvc
```

2. Log details for any PID
```bash
adb logcat --pid=17537
```

## 🤝 Contributing to this project
I would really love to get more contributors on this project. <br>
I know many improvements can be done & also limitations can be minimized. 
