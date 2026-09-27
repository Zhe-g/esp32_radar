# =========================================================
# ESP32 Radar Main
# =========================================================

import time
import machine
from machine import SPI

import config

from st7789 import ST7789
from servo import Servo
from hcsr04 import HCSR04
from radar import Radar
from web import WebServer


# =========================================================
# Global
# =========================================================

tft = None
servo = None
sensor = None
radar = None
web = None


# =========================================================
# Serial log
# =========================================================

def log(text):

    print(
        "[BOOT] " + str(text)
    )


# =========================================================
# TFT helper
# =========================================================

def tft_text(
    text,
    x=5,
    y=5,
    color=0xFFFF
):

    try:

        tft.text(
            text,
            x,
            y,
            color
        )

    except Exception as e:

        print(
            "[TFT]",
            e
        )


def tft_clear():

    try:

        tft.fill(
            0x0000
        )

    except Exception:
        pass


def show_boot_screen():

    tft_clear()

    tft_text(
        "ESP32 RADAR",
        5,
        5,
        0x07E0
    )

    tft_text(
        "SYSTEM BOOT",
        5,
        20,
        0xFFFF
    )


def show_step(
    number,
    total,
    name,
    status="INIT..."
):

    log(
        "[{}/{}] {} - {}".format(
            number,
            total,
            name,
            status
        )
    )

    try:

        # 清理状态区域
        tft.fill_rect(
            0,
            45,
            config.TFT_WIDTH,
            80,
            0x0000
        )

        tft_text(
            "[{}/{}]".format(
                number,
                total
            ),
            5,
            45,
            0x07E0
        )

        tft_text(
            name,
            5,
            65,
            0xFFFF
        )

        tft_text(
            status,
            5,
            85,
            0xFFFF
        )

    except Exception as e:

        print(
            "[TFT BOOT ERROR]",
            e
        )


def show_ok():

    log("OK")

    try:

        tft.fill_rect(
            0,
            85,
            config.TFT_WIDTH,
            20,
            0x0000
        )

        tft_text(
            "OK",
            5,
            85,
            0x07E0
        )

    except Exception:
        pass


def show_error(error):

    print(
        "ERROR:",
        error
    )

    try:

        tft.fill_rect(
            0,
            85,
            config.TFT_WIDTH,
            50,
            0x0000
        )

        tft_text(
            "ERROR",
            5,
            85,
            0xF800
        )

        tft_text(
            str(error)[:30],
            5,
            105,
            0xF800
        )

    except Exception:
        pass


# =========================================================
# WiFi callback
# =========================================================

def wifi_progress(
    status,
    message
):

    print(
        "[WIFI]",
        status,
        message
    )

    try:

        # WiFi 是第 6 步
        tft.fill_rect(
            0,
            45,
            config.TFT_WIDTH,
            100,
            0x0000
        )

        tft_text(
            "[6/7]",
            5,
            45,
            0x07E0
        )

        tft_text(
            "WIFI",
            5,
            65,
            0xFFFF
        )


        if status == "CONNECTING":

            tft_text(
                "CONNECTING",
                5,
                85,
                0xFFFF
            )

            tft_text(
                message,
                5,
                105,
                0xFFFF
            )


        elif status == "CONNECTED":

            tft_text(
                "CONNECTED",
                5,
                85,
                0x07E0
            )

            tft_text(
                "IP:",
                5,
                105,
                0xFFFF
            )

            tft_text(
                message[:24],
                5,
                120,
                0xFFFF
            )


        elif status == "TIMEOUT":

            tft_text(
                "TIMEOUT",
                5,
                85,
                0xF800
            )

            tft_text(
                "SKIP WIFI",
                5,
                105,
                0xFFFF
            )


        elif status == "ERROR":

            tft_text(
                "ERROR",
                5,
                85,
                0xF800
            )

            tft_text(
                str(message)[:24],
                5,
                105,
                0xF800
            )

    except Exception as e:

        print(
            "[WIFI TFT ERROR]",
            e
        )


# =========================================================
# STEP 1
# SPI
# =========================================================

print()
print("================================")
print(" ESP32 WIFI RADAR")
print(" BOOTING")
print("================================")
print()


try:

    log("STEP 1 - SPI")

    spi = SPI(
        2,

        baudrate=config.TFT_BAUDRATE,

        polarity=1,
        phase=1,

        sck=machine.Pin(
            config.TFT_SCK
        ),

        mosi=machine.Pin(
            config.TFT_MOSI
        )
    )

    log("SPI OK")

except Exception as e:

    print(
        "FATAL SPI ERROR:",
        e
    )

    while True:
        time.sleep(1)


# =========================================================
# STEP 2
# TFT
# =========================================================

try:

    log("STEP 2 - TFT")

    tft = ST7789(
        spi,
        config.TFT_WIDTH,
        config.TFT_HEIGHT,

        reset=machine.Pin(
            config.TFT_RST
        ),

        dc=machine.Pin(
            config.TFT_DC
        ),

        cs=machine.Pin(
            config.TFT_CS
        )
    )

    tft.init()

    show_boot_screen()

    show_step(
        2,
        7,
        "TFT",
        "INIT..."
    )

    time.sleep_ms(300)

    show_ok()

    time.sleep_ms(300)

except Exception as e:

    print(
        "FATAL TFT ERROR:",
        e
    )

    while True:
        time.sleep(1)


# =========================================================
# STEP 3
# Servo
# =========================================================

try:

    show_step(
        3,
        7,
        "SERVO",
        "INIT..."
    )

    servo = Servo(
        config.SERVO_PIN
    )

    # 移到中间
    servo.move(90)

    time.sleep_ms(500)

    show_ok()

except Exception as e:

    show_error(e)

    while True:
        time.sleep(1)


# =========================================================
# STEP 4
# HC-SR04
# =========================================================

try:

    show_step(
        4,
        7,
        "HC-SR04",
        "INIT..."
    )

    sensor = HCSR04(
        config.TRIG_PIN,
        config.ECHO_PIN,
        config.MAX_DISTANCE_CM
    )

    time.sleep_ms(200)

    show_ok()

except Exception as e:

    show_error(e)

    while True:
        time.sleep(1)


# =========================================================
# STEP 5
# Radar
# =========================================================

try:

    show_step(
        5,
        7,
        "RADAR",
        "INIT..."
    )

    radar = Radar(
        servo,
        sensor,
        tft,

        min_angle=config.MIN_ANGLE,
        max_angle=config.MAX_ANGLE,

        step=config.SCAN_STEP,

        max_distance=config.RADAR_MAX_DISTANCE,

        settle_ms=config.SERVO_SETTLE_MS
    )

    time.sleep_ms(200)

    show_ok()

except Exception as e:

    show_error(e)

    while True:
        time.sleep(1)


# =========================================================
# STEP 6
# WiFi
# =========================================================

show_step(
    6,
    7,
    "WIFI",
    "START..."
)


wifi_ok = False


# 如果配置为 0，直接跳过
if config.WIFI_TIMEOUT_S <= 0:

    log(
        "WiFi disabled by config"
    )

    wifi_progress(
        "TIMEOUT",
        "SKIP WIFI"
    )

else:

    try:

        web = WebServer(
            radar,
            config.WIFI_SSID,
            config.WIFI_PASSWORD,
            config.WEB_PORT
        )

        wifi_ok = web.connect_wifi(
            timeout_s=config.WIFI_TIMEOUT_S,
            progress_callback=wifi_progress
        )

    except Exception as e:

        print(
            "WiFi exception:",
            e
        )

        wifi_ok = False

        wifi_progress(
            "ERROR",
            str(e)
        )


# =========================================================
# Web Server
# =========================================================

if wifi_ok:

    log(
        "Starting web server..."
    )

    try:

        if web.start():

            log(
                "Web server OK"
            )

        else:

            log(
                "Web server skipped"
            )

    except Exception as e:

        print(
            "Web server error:",
            e
        )


else:

    log(
        "WiFi unavailable."
    )

    log(
        "Radar will run OFFLINE."
    )


# =========================================================
# STEP 7
# Radar background
# =========================================================

try:

    show_step(
        7,
        7,
        "RADAR",
        "DRAWING..."
    )

    radar.draw_background()

    time.sleep_ms(300)

    show_ok()

    time.sleep_ms(500)

except Exception as e:

    show_error(e)

    while True:
        time.sleep(1)


# =========================================================
# SYSTEM READY
# =========================================================

log("")
log("================================")
log(" SYSTEM READY")
log("================================")

if wifi_ok:

    log(
        "WEB: http://{}".format(
            web.ip
        )
    )

else:

    log(
        "WEB: OFFLINE"
    )


# =========================================================
# READY SCREEN
# =========================================================

try:

    tft.fill(
        0x0000
    )

    tft_text(
        "ESP32 RADAR",
        5,
        20,
        0x07E0
    )

    tft_text(
        "SYSTEM READY",
        5,
        45,
        0x07E0
    )

    if wifi_ok:

        tft_text(
            "WIFI: ONLINE",
            5,
            70,
            0x07E0
        )

        tft_text(
            "IP:",
            5,
            90,
            0xFFFF
        )

        tft_text(
            str(web.ip)[:24],
            5,
            105,
            0xFFFF
        )

    else:

        tft_text(
            "WIFI: OFFLINE",
            5,
            75,
            0xF800
        )

        tft_text(
            "RADAR LOCAL MODE",
            5,
            100,
            0xFFFF
        )


    tft_text(
        "STARTING SCAN...",
        5,
        130,
        0xFFFF
    )

    time.sleep_ms(1000)

except Exception as e:

    print(
        "Ready screen error:",
        e
    )


# =========================================================
# START RADAR
# =========================================================

if config.AUTO_START:

    log(
        "Starting radar..."
    )

    try:

        radar.start()

    except Exception as e:

        print(
            "Radar start error:",
            e
        )

        try:

            tft.fill(
                0x0000
            )

            tft_text(
                "RADAR ERROR",
                5,
                50,
                0xF800
            )

            tft_text(
                str(e)[:30],
                5,
                75,
                0xF800
            )

        except Exception:
            pass

        while True:
            time.sleep(1)


# =========================================================
# MAIN LOOP
# =========================================================

print()
print("================================")
print(" MAIN LOOP")
print("================================")
print()


while True:

    try:

        # 如果 WiFi 正常
        # 才处理网页
        if web is not None:

            web.handle()


        # 雷达扫描
        if radar.scanning:

            radar.scan_once()

        else:

            time.sleep_ms(5)


    except Exception as e:

        print(
            "MAIN LOOP ERROR:",
            e
        )

        # 不让一个网页/扫描异常直接死机
        time.sleep_ms(100)