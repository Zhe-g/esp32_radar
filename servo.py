from machine import Pin, PWM


class Servo:

    def __init__(self, pin):

        self.pwm = PWM(
            Pin(pin),
            freq=50
        )

        self.angle = 90

    def _angle_to_duty(self, angle):

        # 50Hz
        # 周期 = 20ms
        #
        # 这里采用约：
        # 0°   -> 0.5ms
        # 180° -> 2.5ms

        min_us = 500
        max_us = 2500

        pulse_us = (
            min_us
            + (max_us - min_us)
            * angle
            / 180
        )

        duty = int(
            pulse_us
            * 65535
            / 20000
        )

        return duty

    def move(self, angle):

        angle = max(0, min(180, angle))

        duty = self._angle_to_duty(angle)

        self.pwm.duty_u16(duty)

        self.angle = angle

    def get_angle(self):

        return self.angle

    def release(self):

        self.pwm.duty_u16(0)