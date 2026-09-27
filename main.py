# =========================================================
# ESP32 WiFi Radar - main.py
# =========================================================

import time
import machine
from machine import SPI

import config
from servo import Servo
from hcsr04 import HCSR04
from st7789 import ST7789
from radar import Radar
from web import WebServer


# =========================================================
# 工具函数
# =========================================================

def boot_log(message):
    print(message)


def show_tft(tft, line1="", line2="", line3="", line4=""):
    """
    在 TFT 上显示启动状态。
    你的 ST7789 驱动只支持 ASCII，所以这里不要使用中文。
    """
    try:
        tft.fill(0x0000)

        if line1:
            tft.text(line1, 5, 10, 0xFFFF, 2)

        if line2:
            tft.text(line2, 5, 40, 0x07E0, 1)

        if line3:
            tft.text(line3, 5, 60, 0x07E0, 1)

        if line4:
            tft.text(line4, 5, 80, 0x07E0, 1)

    except Exception as e:
        print("TFT STATUS ERROR:", e)


# =========================================================
# STEP 1 - SPI
# =========================================================

boot_log("")
boot_log("================================")
boot_log(" ESP32 WIFI RADAR")
boot_log(" BOOTING")
boot_log("================================")
boot_log("")

boot_log("[BOOT] STEP 1 - SPI")

try:

    spi = SPI(
        2,
        baudrate=config.TFT_BAUDRATE,
        polarity=1,
        phase=1,
        sck=machine.Pin(config.TFT_SCK),
        mosi=machine.Pin(config.TFT_MOSI)
    )

    boot_log("[BOOT] SPI OK")

except Exception as e:

    boot_log("FATAL SPI ERROR: {}".format(e))
    raise


# =========================================================
# STEP 2 - TFT
# =========================================================

boot_log("[BOOT] STEP 2 - TFT")

try:

    # -----------------------------------------------------
    # 注意：
    # 你的 ST7789.py 构造函数是：
    #
    # ST7789(
    #     width,
    #     height,
    #     spi,
    #     cs,
    #     dc,
    #     rst
    # )
    #
    # 所以这里必须按照这个顺序传参数。
    # -----------------------------------------------------

    tft = ST7789(
        config.TFT_WIDTH,
        config.TFT_HEIGHT,
        spi,
        config.TFT_CS,
        config.TFT_DC,
        config.TFT_RST
    )

    # 你的 ST7789 驱动在 __init__() 中
    # 已经自动完成：
    #
    # _reset()
    # _init_display()
    #
    # 所以这里不需要 tft.init()

    tft.fill(0x0000)

    boot_log("[BOOT] TFT OK")

    show_tft(
        tft,
        "ESP32 RADAR",
        "STEP 1 SPI OK",
        "STEP 2 TFT OK",
        "STARTING..."
    )

    time.sleep_ms(500)

except Exception as e:

    boot_log("FATAL TFT ERROR: {}".format(e))
    raise


# =========================================================
# STEP 3 - SERVO
# =========================================================

boot_log("[BOOT] STEP 3 - SERVO")

try:

    servo = Servo(
        config.SERVO_PIN
    )

    # 先移动到中间位置
    servo.move(90)

    time.sleep_ms(500)

    boot_log("[BOOT] SERVO OK")

    show_tft(
        tft,
        "ESP32 RADAR",
        "SPI OK",
        "TFT OK",
        "SERVO OK"
    )

    time.sleep_ms(500)

except Exception as e:

    boot_log("FATAL SERVO ERROR: {}".format(e))
    raise


# =========================================================
# STEP 4 - HC-SR04
# =========================================================

boot_log("[BOOT] STEP 4 - HC-SR04")

try:

    sensor = HCSR04(
        config.TRIG_PIN,
        config.ECHO_PIN,
        config.MAX_DISTANCE_CM
    )

    # 做一次测试测距
    test_distance = sensor.distance_cm()

    boot_log(
        "[BOOT] HC-SR04 OK, distance={}".format(
            test_distance
        )
    )

    show_tft(
        tft,
        "ESP32 RADAR",
        "SERVO OK",
        "HC-SR04 OK",
        "DIST: {}".format(test_distance)
    )

    time.sleep_ms(500)

except Exception as e:

    boot_log("FATAL HC-SR04 ERROR: {}".format(e))
    raise


# =========================================================
# STEP 5 - RADAR
# =========================================================

boot_log("[BOOT] STEP 5 - RADAR")

try:

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

    boot_log("[BOOT] RADAR OK")

    show_tft(
        tft,
        "ESP32 RADAR",
        "SERVO OK",
        "SENSOR OK",
        "RADAR OK"
    )

    time.sleep_ms(500)

except Exception as e:

    boot_log("FATAL RADAR ERROR: {}".format(e))
    raise


# =========================================================
# STEP 6 - WIFI
# =========================================================

boot_log("[BOOT] STEP 6 - WIFI")

web = None
wifi_ok = False


def wifi_progress(message):

    print("[WIFI]", message)

    try:

        # 连接过程中的文字必须使用 ASCII
        if message == "CONNECTING":

            show_tft(
                tft,
                "ESP32 RADAR",
                "RADAR OK",
                "WIFI CONNECTING",
                "PLEASE WAIT..."
            )

        elif message == "CONNECTED":

            show_tft(
                tft,
                "ESP32 RADAR",
                "RADAR OK",
                "WIFI CONNECTED",
                "WEB ONLINE"
            )

        elif message == "TIMEOUT":

            show_tft(
                tft,
                "ESP32 RADAR",
                "WIFI TIMEOUT",
                "SKIP WIFI",
                "LOCAL MODE"
            )

        elif message == "ERROR":

            show_tft(
                tft,
                "ESP32 RADAR",
                "WIFI ERROR",
                "SKIP WIFI",
                "LOCAL MODE"
            )

    except Exception as e:

        print("WIFI TFT ERROR:", e)


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

    if wifi_ok:

        boot_log("[BOOT] WIFI CONNECTED")

        try:

            web.start()

            boot_log("[BOOT] WEB SERVER STARTED")

        except Exception as e:

            boot_log(
                "[BOOT] WEB SERVER ERROR: {}".format(e)
            )

            wifi_ok = False

    else:

        boot_log(
            "[BOOT] WIFI FAILED - LOCAL MODE"
        )

except Exception as e:

    boot_log(
        "[BOOT] WIFI INIT ERROR: {}".format(e)
    )

    wifi_ok = False


# =========================================================
# STEP 7 - READY
# =========================================================

boot_log("")
boot_log("================================")
boot_log(" SYSTEM READY")
boot_log("================================")

if wifi_ok:

    boot_log("[BOOT] WIFI: ONLINE")

    try:

        ip = web.get_ip()

        boot_log(
            "[BOOT] IP: {}".format(ip)
        )

        boot_log(
            "[BOOT] WEB: http://{}".format(ip)
        )

    except Exception as e:

        boot_log(
            "[BOOT] IP INFO ERROR: {}".format(e)
        )

else:

    boot_log("[BOOT] WIFI: OFFLINE")
    boot_log("[BOOT] RADAR: LOCAL MODE")


# =========================================================
# TFT READY SCREEN
# =========================================================

try:

    tft.fill(0x0000)

    tft.text(
        "ESP32 RADAR",
        45,
        15,
        0x07E0,
        2
    )

    tft.text(
        "SYSTEM READY",
        55,
        50,
        0xFFFF,
        1
    )

    if wifi_ok:

        tft.text(
            "WIFI ONLINE",
            60,
            70,
            0x07E0,
            1
        )

    else:

        tft.text(
            "WIFI OFFLINE",
            55,
            70,
            0xF800,
            1
        )

        tft.text(
            "LOCAL MODE",
            65,
            90,
            0xFFFF,
            1
        )

    time.sleep_ms(1000)

except Exception as e:

    print("READY SCREEN ERROR:", e)


# =========================================================
# AUTO START
# =========================================================

if config.AUTO_START:

    boot_log("[BOOT] AUTO START RADAR")

    try:

        radar.start()

        boot_log("[BOOT] RADAR SCAN STARTED")

    except Exception as e:

        boot_log(
            "[BOOT] RADAR START ERROR: {}".format(e)
        )

else:

    boot_log("[BOOT] AUTO START DISABLED")


# =========================================================
# MAIN LOOP
# =========================================================

boot_log("")
boot_log("[MAIN] ENTER MAIN LOOP")
boot_log("")


while True:

    try:

        # -------------------------------------------------
        # Web server
        # -------------------------------------------------

        if web is not None and wifi_ok:

            try:

                web.handle()

            except Exception as e:

                print(
                    "[WEB] HANDLE ERROR:",
                    e
                )

        # -------------------------------------------------
        # Radar
        # -------------------------------------------------

        if radar.scanning:

            radar.scan_once()

        else:

            time.sleep_ms(5)

    except KeyboardInterrupt:

        print("")
        print("================================")
        print(" RADAR STOPPED")
        print("================================")

        try:
            servo.release()
        except:
            pass

        break

    except Exception as e:

        print("")
        print("[MAIN LOOP ERROR]", e)

        time.sleep_ms(100)