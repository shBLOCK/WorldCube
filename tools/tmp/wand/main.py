import rotaryio
import board
from time import sleep
import digitalio
import analogio
import adafruit_debouncer
import json

ROTARY_CLK = digitalio.DigitalInOut(board.D2)
ROTARY_DAT = digitalio.DigitalInOut(board.D1)

VRX = analogio.AnalogIn(board.D10)
VRY = analogio.AnalogIn(board.D9)
_BTN = digitalio.DigitalInOut(board.D8)
_BTN.pull = digitalio.Pull.UP
BTN = adafruit_debouncer.Debouncer(_BTN)

def send(type: str, **kwargs):
    kwargs.update(type=type)
    print(json.dumps(kwargs))

tick = 0
last_clk = 0
while True:
    clk = ROTARY_CLK.value
    if not clk and last_clk:
        send("rot", dir=ROTARY_DAT.value * 2 - 1)
    last_clk = clk
    BTN.update()
    if BTN.fell:
        send("btn_pressed")
    if BTN.rose:
        send("btn_released")
    sleep(0.001)
    tick += 1
    if tick == 10:
        tick = 0
        send("joystick", x=VRX.value / 61026 * 2 - 1, y=VRY.value / 61026 * 2 - 1)
