# automatic-charger
Turn on / off your laptop or mobile charger using the threshold values. The smart charger will be equipped  with a ESP32 microcontroller. This application should work on Android, Linux &amp; Windows.

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
