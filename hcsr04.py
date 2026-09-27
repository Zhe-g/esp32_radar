from machine import Pin, time_pulse_us
import time


class HCSR04:

    def __init__(
        self,
        trig_pin,
        echo_pin,
        max_distance=200
    ):

        self.trig = Pin(
            trig_pin,
            Pin.OUT
        )

        self.echo = Pin(
            echo_pin,
            Pin.IN
        )

        self.max_distance = max_distance

        self.trig.value(0)

        time.sleep_ms(100)

    def distance_cm(self):

        # 发送触发脉冲

        self.trig.value(0)

        time.sleep_us(2)

        self.trig.value(1)

        time.sleep_us(10)

        self.trig.value(0)

        # 等待 Echo

        try:

            duration = time_pulse_us(
                self.echo,
                1,
                30000
            )

        except Exception:

            return -1

        if duration < 0:

            return -1

        # 声速：
        # 343 m/s
        #
        # 距离：
        # t * 0.0343 / 2

        distance = (
            duration * 0.0343
        ) / 2

        if distance <= 0:

            return -1

        if distance > self.max_distance:

            return self.max_distance

        return round(distance, 1)