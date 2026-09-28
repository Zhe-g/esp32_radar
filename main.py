import time
import network
import machine
from machine import SPI


import config

from servo import Servo
from hcsr04 import HCSR04
from radar import Radar
from st7789 import ST7789
from tcp_server import RadarTCPServer


# =========================================================
# Wi-Fi
# =========================================================

def connect_wifi():

    print("[WIFI] CONNECTING...")


    wlan = network.WLAN(
        network.STA_IF
    )


    wlan.active(True)


    if wlan.isconnected():

        print(
            "[WIFI] ALREADY CONNECTED"
        )

        print(
            "[WIFI] IP:",
            wlan.ifconfig()[0]
        )

        return wlan


    try:

        wlan.connect(
            config.WIFI_SSID,
            config.WIFI_PASSWORD
        )

    except Exception as e:

        print(
            "[WIFI] CONNECT ERROR:",
            e
        )

        return None


    start = time.ticks_ms()


    while not wlan.isconnected():

        if (
            time.ticks_diff(
                time.ticks_ms(),
                start
            )
            >
            config.WIFI_TIMEOUT_S * 1000
        ):

            print(
                "[WIFI] TIMEOUT"
            )

            return None


        print(
            "[WIFI] WAIT..."
        )

        time.sleep_ms(500)


    print(
        "[WIFI] CONNECTED"
    )


    print(
        "[WIFI] IP:",
        wlan.ifconfig()[0]
    )


    return wlan


# =========================================================
# 初始化 TFT
# =========================================================

def create_tft():

    print(
        "[TFT] SPI INIT..."
    )


    # -----------------------------------------------------
    # 关键：
    # 使用保守的 SPI 参数
    # -----------------------------------------------------

    spi = SPI(
        2,

        baudrate=10000000,

        polarity=0,

        phase=0,

        sck=machine.Pin(
            config.TFT_SCK
        ),

        mosi=machine.Pin(
            config.TFT_MOSI
        )
    )


    print(
        "[TFT] SPI OK"
    )


    # -----------------------------------------------------
    # ST7789
    #
    # 注意：
    # 不要使用 reset=xxx
    # 不要调用 tft.init()
    # -----------------------------------------------------

    tft = ST7789(
        config.TFT_WIDTH,
        config.TFT_HEIGHT,

        spi,

        config.TFT_CS,
        config.TFT_DC,
        config.TFT_RST
    )


    print(
        "[TFT] ST7789 OK"
    )


    return tft


# =========================================================
# 主程序
# =========================================================

def main():

    print()
    print("==============================")
    print(" ESP32 RADAR")
    print("==============================")
    print()


    # =====================================================
    # 1. Wi-Fi
    # =====================================================

    wlan = connect_wifi()


    if wlan is None:

        print(
            "[MAIN] WIFI FAILED"
        )

        return


    # =====================================================
    # 2. TFT
    # =====================================================

    print(
        "[MAIN] INIT TFT..."
    )


    tft = create_tft()


    # =====================================================
    # 3. Servo
    # =====================================================

    print(
        "[MAIN] INIT SERVO..."
    )


    servo = Servo(
        config.SERVO_PIN
    )


    # =====================================================
    # 4. HC-SR04
    # =====================================================

    print(
        "[MAIN] INIT HC-SR04..."
    )


    sensor = HCSR04(
        config.TRIG_PIN,
        config.ECHO_PIN,
        config.MAX_DISTANCE_CM
    )


    # =====================================================
    # 5. Radar
    # =====================================================

    print(
        "[MAIN] INIT RADAR..."
    )


    radar = Radar(

        servo=servo,

        sensor=sensor,

        tft=tft,

        min_angle=
            config.MIN_ANGLE,

        max_angle=
            config.MAX_ANGLE,

        step=
            config.SCAN_STEP,

        max_distance=
            config.RADAR_MAX_DISTANCE,

        settle_ms=
            config.SERVO_SETTLE_MS

    )


    # =====================================================
    # 6. TCP
    # =====================================================

    print(
        "[MAIN] INIT TCP..."
    )


    tcp = RadarTCPServer(
        radar,
        config.TCP_PORT
    )


    tcp.start()


    # =====================================================
    # 7. 自动启动
    # =====================================================

    if config.AUTO_START:

        radar.start()


    # =====================================================
    # 8. 主循环
    # =====================================================

    last_send = time.ticks_ms()


    while True:

        # ---------------------------------------------
        # TCP
        # ---------------------------------------------

        tcp.update()


        # ---------------------------------------------
        # 雷达
        # ---------------------------------------------

        radar.scan_once()


        # ---------------------------------------------
        # TCP 数据发送
        # ---------------------------------------------

        now = time.ticks_ms()


        if (
            time.ticks_diff(
                now,
                last_send
            )
            >=
            config.DATA_INTERVAL_MS
        ):

            tcp.send_data()

            last_send = now


# =========================================================
# 启动
# =========================================================

try:

    main()


except KeyboardInterrupt:

    print(
        "[MAIN] STOPPED"
    )


except Exception as e:

    print(
        "[MAIN] FATAL ERROR:",
        e
    )

    raise