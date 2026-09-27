import math
import time


# =========================
# RGB565 colors
# =========================

BLACK = 0x0000
GREEN = 0x07E0
DARK_GREEN = 0x0320
RED = 0xF800
WHITE = 0xFFFF
CYAN = 0x07FF
DARK_CYAN = 0x03EF
YELLOW = 0xFFE0
GRAY = 0x8410
DARK_GRAY = 0x4208


class Radar:

    def __init__(
        self,
        servo,
        ultrasonic,
        tft,
        min_angle=10,
        max_angle=170,
        step=3,
        max_distance=200,
        settle_ms=30
    ):

        self.servo = servo
        self.ultrasonic = ultrasonic
        self.tft = tft

        self.min_angle = min_angle
        self.max_angle = max_angle
        self.step = step

        self.max_distance = max_distance
        self.settle_ms = settle_ms

        # Current servo angle
        self.angle = min_angle

        # 1 = increasing
        # -1 = decreasing
        self.direction = 1

        self.scanning = False

        self.last_distance = -1

        self.nearest_distance = -1
        self.nearest_angle = -1

        # Current sweep data
        self.points = []

        # Radar geometry
        self.center_x = 120
        self.center_y = 200

        self.radius = 100

        # Previous scan line
        self.previous_line = None

        # Used for display update
        self.background_ready = False

    # =========================
    # Start
    # =========================

    def start(self):

        self.scanning = True

        self.points = []

        self.nearest_distance = -1
        self.nearest_angle = -1

        self.angle = self.min_angle
        self.direction = 1

        self.previous_line = None

        self.servo.move(self.angle)

        # Draw complete radar once
        self.draw_background()

        self.draw_dynamic()

    # =========================
    # Stop
    # =========================

    def stop(self):

        self.scanning = False

        self.draw_dynamic()

    # =========================
    # Radar background
    # =========================

    def draw_background(self):

        tft = self.tft

        # Clear screen ONCE
        tft.fill(BLACK)

        # Radar circles
        #
        # We intentionally use only 3 circles.
        # Fewer SPI operations.
        for ratio in (
            0.33,
            0.66,
            1.0
        ):

            tft.circle(
                self.center_x,
                self.center_y,
                int(self.radius * ratio),
                DARK_GRAY
            )

        # Horizontal 180° / 0° line
        tft.hline(
            self.center_x - self.radius,
            self.center_y,
            self.radius * 2 + 1,
            DARK_GRAY
        )

        # Vertical 90° line
        tft.vline(
            self.center_x,
            self.center_y - self.radius,
            self.radius + 1,
            DARK_GRAY
        )

        # Distance labels
        tft.text(
            "50",
            5,
            118,
            GRAY,
            1
        )

        tft.text(
            "100",
            5,
            92,
            GRAY,
            1
        )

        tft.text(
            "150",
            5,
            65,
            GRAY,
            1
        )

        tft.text(
            "200",
            5,
            39,
            GRAY,
            1
        )

        # Static title
        tft.text(
            "ESP32 RADAR",
            70,
            5,
            WHITE,
            1
        )

        self.background_ready = True

    # =========================
    # Convert polar coordinate
    # =========================

    def _polar(
        self,
        angle,
        distance
    ):

        if distance <= 0:
            return None

        distance = min(
            distance,
            self.max_distance
        )

        r = (
            distance
            / self.max_distance
            * self.radius
        )

        rad = math.radians(angle)

        x = int(
            self.center_x
            - math.cos(rad) * r
        )

        y = int(
            self.center_y
            - math.sin(rad) * r
        )

        return x, y

    # =========================
    # Current scan line
    # =========================

    def _scan_line(self, angle):

        rad = math.radians(angle)

        x = int(
            self.center_x
            - math.cos(rad)
            * self.radius
        )

        y = int(
            self.center_y
            - math.sin(rad)
            * self.radius
        )

        return (
            self.center_x,
            self.center_y,
            x,
            y
        )

    # =========================
    # Scan once
    # =========================

    def scan_once(self):

        if not self.scanning:
            return

        # Move servo
        self.servo.move(
            self.angle
        )

        # Short settling time
        time.sleep_ms(
            self.settle_ms
        )

        # Measure
        distance = (
            self.ultrasonic
            .distance_cm()
        )

        self.last_distance = distance

        # Save point
        self.points.append({
            "angle": self.angle,
            "distance": distance
        })

        # Limit memory
        if len(self.points) > 70:
            self.points.pop(0)

        # Nearest object
        if distance > 0:

            if (
                self.nearest_distance < 0
                or distance < self.nearest_distance
            ):

                self.nearest_distance = distance

                self.nearest_angle = (
                    self.angle
                )

        # Update TFT immediately
        self.draw_dynamic()

        # Calculate next angle
        next_angle = (
            self.angle
            + self.direction * self.step
        )

        # Right edge
        if next_angle >= self.max_angle:

            self.angle = self.max_angle

            self.direction = -1

        # Left edge
        elif next_angle <= self.min_angle:

            self.angle = self.min_angle

            self.direction = 1

            # Start new sweep
            self.points = []

            self.nearest_distance = -1

            self.nearest_angle = -1

        else:

            self.angle = next_angle

    # =========================
    # Draw dynamic elements
    # =========================

    def draw_dynamic(self):

        if not self.background_ready:
            self.draw_background()

        tft = self.tft

        # ---------------------
        # Draw all detected dots
        # ---------------------

        for p in self.points:

            pos = self._polar(
                p["angle"],
                p["distance"]
            )

            if pos is None:
                continue

            x, y = pos

            if (
                p["distance"] <= 30
            ):
                color = RED
            else:
                color = GREEN

            # 3x3 point
            tft.fill_rect(
                x - 1,
                y - 1,
                3,
                3,
                color
            )

        # ---------------------
        # Scan line
        # ---------------------

        x0, y0, x1, y1 = (
            self._scan_line(
                self.angle
            )
        )

        # Draw current scan line.
        #
        # We intentionally don't erase
        # the previous sweep completely.
        # This creates a radar-style
        # persistence effect.
        tft.line(
            x0,
            y0,
            x1,
            y1,
            CYAN
        )

        # Center
        tft.fill_rect(
            self.center_x - 2,
            self.center_y - 2,
            5,
            5,
            YELLOW
        )

        # ---------------------
        # Header
        # ---------------------

        # Clear only header area
        tft.fill_rect(
            0,
            0,
            240,
            28,
            BLACK
        )

        tft.text(
            "A:" + str(self.angle),
            5,
            5,
            WHITE,
            1
        )

        if self.last_distance > 0:

            dist_text = (
                "D:"
                + str(self.last_distance)
            )

        else:

            dist_text = "D:--"

        tft.text(
            dist_text,
            70,
            5,
            WHITE,
            1
        )

        if self.nearest_distance > 0:

            near_text = (
                "N:"
                + str(
                    self.nearest_distance
                )
            )

        else:

            near_text = "N:--"

        if (
            self.nearest_distance > 0
            and self.nearest_distance <= 30
        ):
            near_color = RED
        else:
            near_color = WHITE

        tft.text(
            near_text,
            145,
            5,
            near_color,
            1
        )

        # Status
        status = (
            "SCAN"
            if self.scanning
            else "STOP"
        )

        tft.text(
            status,
            5,
            18,
            GREEN
            if self.scanning
            else YELLOW,
            1
        )

    # =========================
    # Web data
    # =========================

    def get_data(self):

        return {
            "angle": self.angle,

            "distance": self.last_distance,

            "scanning": self.scanning,

            "nearest_distance":
                self.nearest_distance,

            "nearest_angle":
                self.nearest_angle,

            "points": self.points
        }

