# EyeLights New Year's Eve Countdown

Display a countdown to the new year on AdaFruit EyeLights LED Glasses.

There are two different countdown modes:

# Time sync

In order to get the current time, this program expects to be paired with a GATT CurrentTimeService.  Handily, the AdaFruit BlueFruit mobile app provides a way to do this.  The EyeLights should show up in the device list as something starting with `CIRCUITPY` and just connecting to that device is enough to sync the time. When the program starts it waits for a BLE connection and once it gets one it adjusts for the difference between its local clock (which starts on 1/1/2000) and the actual current time.  A connection does not have to be maintained after the initial offset is found, although it would likely be more accurate to keep getting the current time since who knows how much drift the onboard clock has.  Still, for a short new year's countdown it's probably good enough.

# Fixed

If you can't set the time from a BLE device, you can start a fixed 10 second countdown by pressing the button on control board of the glasses.
