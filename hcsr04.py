from machine import Pin, time_pulse_us
import time


class HCSR04:

    def __init__(
        self,
        trig_pin,
        echo_pin,
        max_distance_cm=200
    ):

        self.trig = Pin(
            trig_pin,
            Pin.OUT
        )

        self.echo = Pin(
            echo_pin,
            Pin.IN
        )

        self.max_distance_cm = \
            max_distance_cm

        self.trig.value(0)

        time.sleep_ms(100)


    def distance_cm(self):

        self.trig.value(0)

        time.sleep_us(2)

        self.trig.value(1)

        time.sleep_us(10)

        self.trig.value(0)


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


        distance = (
            duration
            * 0.0343
            / 2
        )


        if (
            distance <= 0
            or
            distance > self.max_distance_cm
        ):

            return -1


        return round(
            distance,
            1
        )