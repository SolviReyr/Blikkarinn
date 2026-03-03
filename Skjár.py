from machine import Pin, SoftI2C
import time


i2c = SoftI2C(sda=Pin(14), scl=Pin(13), freq=400000)

print("I2C scan:", i2c.scan())

LCD_ADDR = 39 


def lcd_write(cmd, mode=0):
    high = mode | (cmd & 0xF0) | 0x08
    low  = mode | ((cmd << 4) & 0xF0) | 0x08
    i2c.writeto(LCD_ADDR, bytes([high, high | 0x04, high]))
    i2c.writeto(LCD_ADDR, bytes([low, low | 0x04, low]))

def lcd_cmd(cmd):
    lcd_write(cmd, 0)

def lcd_data(data):
    lcd_write(data, 1)

def lcd_init():
    time.sleep_ms(20)
    lcd_cmd(0x33)
    lcd_cmd(0x32)
    lcd_cmd(0x28)
    lcd_cmd(0x0C)
    lcd_cmd(0x06)
    lcd_cmd(0x01)
    time.sleep_ms(2)

def lcd_move(col, row):
    addr = col + (0x40 * row)
    lcd_cmd(0x80 | addr)

def lcd_puts(text):
    for c in text:
        lcd_data(ord(c))


lcd_init()

lcd_move(0, 0)
lcd_puts("BLIKARINN")

lcd_move(0, 1)
lcd_puts("")
