from machine import SPI, Pin
import time

import config
from st7789 import ST7789


print()
print("==============================")
print(" ST7789 TFT TEST")
print("==============================")


# =========================================================
# 初始化 SPI
# =========================================================

print("[TFT] Creating SPI...")


spi = SPI(
    2,
    baudrate=10000000,
    polarity=0,
    phase=0,
    sck=Pin(config.TFT_SCK),
    mosi=Pin(config.TFT_MOSI)
)


print("[TFT] SPI OK")


# =========================================================
# 初始化 ST7789
# =========================================================

print("[TFT] Initializing ST7789...")


tft = ST7789(
    config.TFT_WIDTH,
    config.TFT_HEIGHT,
    spi,
    config.TFT_CS,
    config.TFT_DC,
    config.TFT_RST
)


print("[TFT] ST7789 OK")


# =========================================================
# 颜色测试
# =========================================================

colors = [

    ("BLACK", 0x0000),

    ("RED", 0xF800),

    ("GREEN", 0x07E0),

    ("BLUE", 0x001F),

    ("WHITE", 0xFFFF),

    ("CYAN", 0x07FF),

    ("YELLOW", 0xFFE0),

    ("MAGENTA", 0xF81F),

]


for name, color in colors:

    print(
        "[TFT] COLOR:",
        name
    )

    tft.fill(color)

    time.sleep(2)


print()
print("==============================")
print(" TFT TEST FINISHED")
print("==============================")