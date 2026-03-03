Hjalpar code 

from machine import Pin, SoftI2C
from neopixel import NeoPixel
import time
from random import randint

# =========================================================
# CONFIG (CHANGE THESE TO MATCH YOUR WIRING)
# =========================================================

# NeoPixel
NEO_PIN = 4
NEO_COUNT = 16

# Where the 4 "steps" appear on each side of the NeoPixel strip
# (same order left->right on both sides)
LEFT_PIXELS  = [0, 1, 2, 3]
RIGHT_PIXELS = [12, 13, 14, 15]   # change if your layout is different

# Big middle buttons (ONE PER SIDE)  <-- YOU MUST SET THESE CORRECTLY
BIG_LEFT_PIN  = 10   # <-- change
BIG_RIGHT_PIN = 11   # <-- change (must be different from left)

# Small color buttons for each player (4 per side)
# Map is: 0=RED, 1=BLUE, 2=GREEN, 3=YELLOW
LEFT_COLOR_PINS  = [41, 38, 36, 48]  # <-- change to your 4 left small buttons
RIGHT_COLOR_PINS = [16, 7, 2, 8]     # <-- change to your 4 right small buttons

# Optional: small LEDs next to buttons (if you have them wired)
# Put None if you don't use them.
LEFT_LED_PINS  = [40, 39, 37, 47]    # matches LEFT_COLOR_PINS order
RIGHT_LED_PINS = [15, 6, 1, 18]      # matches RIGHT_COLOR_PINS order

# LCD I2C pins
LCD_SDA = 14
LCD_SCL = 13

WIN_SCORE = 5
SEQ_LEN = 4          # 4-step sequence each round
SHOW_MS = 3000       # show sequence for 3 seconds
DEBOUNCE_MS = 180

# =========================================================
# COLORS
# =========================================================
RED    = (255, 0, 0)
BLUE   = (0, 0, 255)
GREEN  = (0, 255, 0)
YELLOW = (255, 255, 0)

COLORS = [RED, BLUE, GREEN, YELLOW]
COLOR_NAMES = ["RED", "BLUE", "GREEN", "YELLOW"]

# =========================================================
# SETUP HARDWARE
# =========================================================
np = NeoPixel(Pin(NEO_PIN, Pin.OUT), NEO_COUNT)

big_left  = Pin(BIG_LEFT_PIN, Pin.IN, Pin.PULL_UP)
big_right = Pin(BIG_RIGHT_PIN, Pin.IN, Pin.PULL_UP)

left_btns  = [Pin(p, Pin.IN, Pin.PULL_UP) for p in LEFT_COLOR_PINS]
right_btns = [Pin(p, Pin.IN, Pin.PULL_UP) for p in RIGHT_COLOR_PINS]

left_leds = [(Pin(p, Pin.OUT) if p is not None else None) for p in LEFT_LED_PINS]
right_leds = [(Pin(p, Pin.OUT) if p is not None else None) for p in RIGHT_LED_PINS]

def leds_off(led_list):
    for led in led_list:
        if led is not None:
            led.value(0)

leds_off(left_leds)
leds_off(right_leds)

# =========================================================
# LCD DRIVER (PCF8574 common) + auto address from scan
# =========================================================
i2c = SoftI2C(sda=Pin(LCD_SDA), scl=Pin(LCD_SCL), freq=100000)
scan = i2c.scan()
print("I2C scan:", scan)
if not scan:
    # Game can still run without LCD, but we will print messages
    LCD_ADDR = None
else:
    LCD_ADDR = scan[0]

BL = 0x08
EN = 0x04
RS = 0x01

def lcd_writenibble(nibble, mode):
    if LCD_ADDR is None:
        return
    data = (nibble & 0xF0) | BL | (RS if mode else 0)
    i2c.writeto(LCD_ADDR, bytes([data | EN]))
    time.sleep_us(50)
    i2c.writeto(LCD_ADDR, bytes([data & ~EN]))
    time.sleep_us(50)

def lcd_writebyte(byte, mode=0):
    lcd_writenibble(byte & 0xF0, mode)
    lcd_writenibble((byte << 4) & 0xF0, mode)

def lcd_cmd(cmd):
    lcd_writebyte(cmd, 0)
    if cmd in (0x01, 0x02):
        time.sleep_ms(2)

def lcd_data(ch):
    lcd_writebyte(ch, 1)

def lcd_init():
    if LCD_ADDR is None:
        return
    time.sleep_ms(50)
    lcd_writenibble(0x30, 0); time.sleep_ms(5)
    lcd_writenibble(0x30, 0); time.sleep_ms(1)
    lcd_writenibble(0x30, 0); time.sleep_ms(1)
    lcd_writenibble(0x20, 0); time.sleep_ms(1)
    lcd_cmd(0x28)
    lcd_cmd(0x0C)
    lcd_cmd(0x06)
    lcd_cmd(0x01)

def lcd_move(col, row):
    if LCD_ADDR is None:
        return
    addr = col + (0x40 if row else 0x00)
    lcd_cmd(0x80 | addr)

def lcd_clear():
    if LCD_ADDR is None:
        return
    lcd_cmd(0x01)

def lcd_puts(text):
    if LCD_ADDR is None:
        return
    for c in text:
        lcd_data(ord(c))

def lcd_show(line1="", line2=""):
    if LCD_ADDR is None:
        # fallback to serial prints
        print(line1)
        print(line2)
        return
    lcd_clear()
    lcd_move(0, 0)
    lcd_puts((line1 + " " * 16)[:16])
    lcd_move(0, 1)
    lcd_puts((line2 + " " * 16)[:16])

lcd_init()
lcd_show("BLIKARINN", "Ready")

# =========================================================
# GAME HELPERS
# =========================================================
def np_clear():
    np.fill((0, 0, 0))
    np.write()

def show_sequence_all_at_once(seq):
    """
    Show 4-step sequence as 4 pixels on each side at once, for 3 seconds.
    """
    np_clear()
    for i in range(SEQ_LEN):
        col = COLORS[seq[i]]
        np[LEFT_PIXELS[i]] = col
        np[RIGHT_PIXELS[i]] = col
    np.write()
    time.sleep_ms(SHOW_MS)
    np_clear()

def wait_big_button():
    """
    Wait until either left or right big button is pressed.
    Returns 0 for LEFT player, 1 for RIGHT player.
    """
    while True:
        if big_left.value() == 0:
            time.sleep_ms(DEBOUNCE_MS)
            while big_left.value() == 0:
                pass
            return 0
        if big_right.value() == 0:
            time.sleep_ms(DEBOUNCE_MS)
            while big_right.value() == 0:
                pass
            return 1

def wait_color_press(player):
    """
    Wait for a color button press from the active player.
    Returns 0..3 (RED/BLUE/GREEN/YELLOW).
    """
    btns = left_btns if player == 0 else right_btns
    leds = left_leds if player == 0 else right_leds

    while True:
        for idx, b in enumerate(btns):
            if b.value() == 0:
                # debounce + wait release
                time.sleep_ms(DEBOUNCE_MS)
                while b.value() == 0:
                    pass

                # optional feedback LED
                if leds[idx] is not None:
                    leds[idx].value(1)
                    time.sleep_ms(120)
                    leds[idx].value(0)

                return idx

def show_scores(scoreL, scoreR):
    lcd_show("L:{}  R:{}".format(scoreL, scoreR), "First to {}".format(WIN_SCORE))

def player_name(p):
    return "LEFT" if p == 0 else "RIGHT"

# =========================================================
# MAIN GAME LOOP (auto restarts after a win)
# =========================================================
while True:
    scoreL = 0
    scoreR = 0
    show_scores(scoreL, scoreR)
    time.sleep_ms(800)

    while scoreL < WIN_SCORE and scoreR < WIN_SCORE:
        # 1) Make a new random 4-color sequence
        seq = [randint(0, 3) for _ in range(SEQ_LEN)]

        lcd_show("Watch sequence", "...")
        show_sequence_all_at_once(seq)

        # 2) Wait for which player starts (big button)
        lcd_show("Press BIG btn", "to start turn")
        turn_player = wait_big_button()

        lcd_show(player_name(turn_player) + " TURN", "Repeat colors")
        time.sleep_ms(300)

        # 3) Player repeats with 4 small buttons
        ok = True
        for i in range(SEQ_LEN):
            guess = wait_color_press(turn_player)
            if guess != seq[i]:
                ok = False
                break

        # 4) Score + next
        if ok:
            if turn_player == 0:
                scoreL += 1
            else:
                scoreR += 1

            lcd_show("Correct!", "L:{} R:{}".format(scoreL, scoreR))
            time.sleep_ms(1200)
        else:
            lcd_show("Wrong!", "Next turn...")
            time.sleep_ms(1200)

        show_scores(scoreL, scoreR)
        time.sleep_ms(500)

    # 5) Win + new game
    winner = "LEFT" if scoreL >= WIN_SCORE else "RIGHT"
    lcd_show(winner + " WINS!", "New game...")
    np_clear()
    time.sleep_ms(2500)

