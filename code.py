# SPDX-FileCopyrightText: 2021 Phil Burgess for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
New Year countdown for Adafruit EyeLights (LED Glasses + Driver).
"""

import time
import board
import digitalio
from busio import I2C
import adafruit_is31fl3741
from adafruit_is31fl3741.adafruit_ledglasses import LED_Glasses
from eyelights_anim import EyeLightsAnim
import adafruit_ble
from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService
from adafruit_ble.advertising.standard import SolicitServicesAdvertisement
from adafruit_ble.services.standard import CurrentTimeService

gamma = 2.6  # For color adjustment. Leave as-is.
def gammify(color):
    """Given an (R,G,B) color tuple, apply gamma correction and return
    a packed 24-bit RGB integer."""
    rgb = [int(((color[x] / 255) ** gamma) * 255 + 0.5) for x in range(3)]
    return (rgb[0] << 16) | (rgb[1] << 8) | rgb[2]

# HARDWARE SETUP -----------------------

i2c = I2C(board.SCL, board.SDA, frequency=1000000)
button = digitalio.DigitalInOut(board.SWITCH)
button.switch_to_input(pull=digitalio.Pull.UP)

radio = adafruit_ble.BLERadio()
a = SolicitServicesAdvertisement()
a.complete_name = "TimePlease"
a.solicited_services.append(CurrentTimeService)
radio.start_advertising(a)


# Initialize the IS31 LED driver, buffered for smoother animation
glasses = LED_Glasses(i2c, allocate=adafruit_is31fl3741.MUST_BUFFER)
glasses.show()  # Clear any residue on startup
glasses.global_current = 20  # Just middlin' bright, please
zero = [
    (b"\x01\x01\x01"),
    (b"\x01\x00\x01"),
    (b"\x01\x00\x01"),
    (b"\x01\x00\x01"),
    (b"\x01\x01\x01"),
]
one = [
    (b"\x00\x00\x01"),
    (b"\x00\x00\x01"),
    (b"\x00\x00\x01"),
    (b"\x00\x00\x01"),
    (b"\x00\x00\x01"),
]
two = [
    (b"\x01\x01\x01"),
    (b"\x00\x00\x01"),
    (b"\x01\x01\x01"),
    (b"\x01\x00\x00"),
    (b"\x01\x01\x01"),
]
three = [
    (b"\x01\x01\x01"),
    (b"\x00\x00\x01"),
    (b"\x01\x01\x01"),
    (b"\x00\x00\x01"),
    (b"\x01\x01\x01"),
]
four = [
    (b"\x01\x00\x01"),
    (b"\x01\x00\x01"),
    (b"\x01\x01\x01"),
    (b"\x00\x00\x01"),
    (b"\x00\x00\x01"),
]
five = [
    (b"\x01\x01\x01"),
    (b"\x01\x00\x00"),
    (b"\x01\x01\x01"),
    (b"\x00\x00\x01"),
    (b"\x01\x01\x01"),
]
six = [
    (b"\x01\x01\x01"),
    (b"\x01\x00\x00"),
    (b"\x01\x01\x01"),
    (b"\x01\x00\x01"),
    (b"\x01\x01\x01"),
]
seven = [
    (b"\x01\x01\x01"),
    (b"\x00\x00\x01"),
    (b"\x00\x00\x01"),
    (b"\x00\x00\x01"),
    (b"\x00\x00\x01"),
]
eight = [
    (b"\x01\x01\x01"),
    (b"\x01\x00\x01"),
    (b"\x01\x01\x01"),
    (b"\x01\x00\x01"),
    (b"\x01\x01\x01"),
]
nine = [
    (b"\x01\x01\x01"),
    (b"\x01\x00\x01"),
    (b"\x01\x01\x01"),
    (b"\x00\x00\x01"),
    (b"\x01\x01\x01"),
]

ring_color = gammify((75, 75, 75))

def digit(n):
    if n > 9:
        return zero
    if n == 0:
        return zero
    if n == 1:
        return one
    if n == 2:
        return two
    if n == 3:
        return three
    if n == 4:
        return four
    if n == 5:
        return five
    if n == 6:
        return six
    if n == 7:
        return seven
    if n == 8:
        return eight
    if n == 9:
        return nine

def digits(n):
    return [n // 10 % 10, n % 10]
    
def digits_full(n):
    return [n // 100000 % 10, n // 10000 % 10, n // 1000 % 10, n // 100 % 10, n // 10 % 10, n % 10]

def display(num, offset):
    for y in range(5):
        for x in range(3):
            glasses.pixel(x+offset, y, num[y][x]*100)

def display_digits_full(ds):
    ring_val = ds[0]*10 + ds[1]
    glasses.left_ring.fill(0)
    if ring_val > 0:
        for r in range(6, ring_val+6):
            glasses.left_ring[r] = gammify((75, 75, 75))
    display(digit(ds[2]), 1)
    display(digit(ds[3]), 4)
    display(digit(ds[4]), 11)
    display(digit(ds[5]), 14)
    
def display_digits(ds):
    display_left(ds)
    display_right(ds)

def display_left(ds):
    offset = 1
    for d in ds:
        display(digit(d), offset)
        offset = offset + 3
def display_right(ds):
    offset = 11
    for d in ds:
        display(digit(d), offset)
        offset = offset + 3

# MAIN LOOP ----------------------------


count = 60
start_time = 0
end_time = 0
clock_adjustment = 0
done = False
NEW_YEAR = time.mktime(time.struct_time((2022, 1, 1, 0, 0, 0, 5, 1, 0)))
# test with a different time
# NEW_YEAR = time.mktime(time.struct_time((2021, 12, 30, 22, 21, 0, 3, 1, 0)))
while True:
    # wait for a connection to sync the time
    if radio.connected:
        for connection in radio.connections:
            if not connection.paired:
                connection.pair()
                print("paired")
            cts = connection[CurrentTimeService]
            clock_adjustment = time.mktime(cts.current_time) - time.time()
            print("seconds until new year")
            print(NEW_YEAR - (time.time() + clock_adjustment))
            connection.disconnect()
        end_time = NEW_YEAR
        break
    # allow a button press to bypass time sync and just start a fixed countdown
    if not button.value:
        start_time = time.time()
        end_time = start_time + 10
        break 
        
while True:
    if done:
        glasses.left_ring.fill(ring_color)
        glasses.right_ring.fill(ring_color)
        display_left(digits(20))
        display_right(digits(22))
        glasses.show()
        continue
    if end_time == (time.time() + clock_adjustment):
        done = True

    count = end_time - (time.time() + clock_adjustment)

    # TODO: switch colors and double display once value is below 60
    #display_digits(digits(count%60))
    if count < 60:
        display_digits(digits(count))
    else:
        display_digits_full(digits_full(count))
    glasses.show()  #   Update LED matrix
    time.sleep(0.2)
