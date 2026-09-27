import math
import time


class Radar:

    # =========================================================
    # Colors RGB565
    # =========================================================

    BLACK = 0x0000
    WHITE = 0xFFFF

    GRID_COLOR = 0x03EF

    SCAN_COLOR = 0x07FF

    TARGET_COLOR = 0xF800

    CENTER_COLOR = 0x07E0

    # =========================================================
    # Constructor
    # =========================================================

    def __init__(
        self,
        servo,
        sensor,
        tft,
        min_angle=10,
        max_angle=170,
        step=5,
        max_distance=200,
        settle_ms=10
    ):

        self.servo = servo
        self.sensor = sensor
        self.tft = tft

        self.min_angle = min_angle
        self.max_angle = max_angle

        self.step = step

        self.max_distance = max_distance

        self.settle_ms = settle_ms

        # =====================================================
        # Radar center
        # =====================================================

        self.cx = self.tft.width // 2

        self.cy = self.tft.height - 15

        self.radius = min(
            self.tft.width // 2 - 5,
            self.tft.height - 30
        )

        # =====================================================
        # Scan state
        # =====================================================

        self.angle = self.min_angle

        self.direction = 1

        self.scanning = False

        # =====================================================
        # Current scan targets
        #
        # 只保存当前这一轮扫描
        # =====================================================

        self.targets = []

        # =====================================================
        # Statistics
        # =====================================================

        self.scan_count = 0

        self.last_distance = -1

        # 上一次扫描线角度
        self.last_line_angle = None

    # =========================================================
    # Start
    # =========================================================

    def start(self):

        self.scanning = True

        self.angle = self.min_angle

        self.direction = 1

        self.targets = []

        self.scan_count = 0

        self.last_distance = -1

        self.last_line_angle = None

        # 绘制初始雷达
        self.draw_background()

        # 舵机移动到起点
        self.servo.move(
            self.angle
        )

        print("[RADAR] START")

    # =========================================================
    # Polar -> XY
    #
    # 0°   左
    # 90°  上
    # 180° 右
    # =========================================================

    def polar_to_xy(
        self,
        angle,
        distance
    ):

        rad = math.radians(angle)

        x = int(
            self.cx +
            math.cos(rad) * distance
        )

        y = int(
            self.cy -
            math.sin(rad) * distance
        )

        return x, y

    # =========================================================
    # Draw radar background
    # =========================================================

    def draw_background(self):

        # 整个屏幕清黑
        self.tft.fill(
            self.BLACK
        )

        # =====================================================
        # Radar circles
        # =====================================================

        self.tft.circle(
            self.cx,
            self.cy,
            self.radius,
            self.GRID_COLOR
        )

        self.tft.circle(
            self.cx,
            self.cy,
            int(self.radius * 0.75),
            self.GRID_COLOR
        )

        self.tft.circle(
            self.cx,
            self.cy,
            int(self.radius * 0.50),
            self.GRID_COLOR
        )

        self.tft.circle(
            self.cx,
            self.cy,
            int(self.radius * 0.25),
            self.GRID_COLOR
        )

        # =====================================================
        # Angle lines
        # =====================================================

        angles = (
            self.min_angle,
            30,
            60,
            90,
            120,
            150,
            self.max_angle
        )

        for angle in angles:

            x, y = self.polar_to_xy(
                angle,
                self.radius
            )

            self.tft.line(
                self.cx,
                self.cy,
                x,
                y,
                self.GRID_COLOR
            )

        # =====================================================
        # Center
        # =====================================================

        self.tft.fill_rect(
            self.cx - 2,
            self.cy - 2,
            5,
            5,
            self.CENTER_COLOR
        )

    # =========================================================
    # 判断像素是不是雷达网格
    # =========================================================

    def background_pixel(
        self,
        x,
        y
    ):

        dx = x - self.cx

        dy = self.cy - y

        distance = math.sqrt(
            dx * dx +
            dy * dy
        )

        # 超出雷达范围
        if distance > self.radius + 1:
            return self.BLACK

        # =====================================================
        # 圆弧
        # =====================================================

        circles = (
            self.radius,
            self.radius * 0.75,
            self.radius * 0.50,
            self.radius * 0.25
        )

        for r in circles:

            if abs(distance - r) <= 1.0:

                return self.GRID_COLOR

        # =====================================================
        # 角度线
        # =====================================================

        if distance > 2:

            angle = math.degrees(
                math.atan2(
                    dy,
                    dx
                )
            )

            if angle < 0:
                angle += 360

            angles = (
                self.min_angle,
                30,
                60,
                90,
                120,
                150,
                self.max_angle
            )

            for a in angles:

                if abs(angle - a) <= 0.6:

                    return self.GRID_COLOR

        # =====================================================
        # Center
        # =====================================================

        if (
            abs(dx) <= 2 and
            abs(dy) <= 2
        ):

            return self.CENTER_COLOR

        return self.BLACK

    # =========================================================
    # Restore one pixel
    # =========================================================

    def restore_pixel(
        self,
        x,
        y
    ):

        if x < 0:
            return

        if x >= self.tft.width:
            return

        if y < 0:
            return

        if y >= self.tft.height:
            return

        color = self.background_pixel(
            x,
            y
        )

        self.tft.pixel(
            x,
            y,
            color
        )

    # =========================================================
    # Erase previous scan line
    #
    # 不再简单使用黑线。
    #
    # 而是恢复成雷达背景。
    # =========================================================

    def erase_scan_line(self):

        if self.last_line_angle is None:
            return

        angle = self.last_line_angle

        # 使用和 line() 一样的 Bresenham 算法
        # 保证擦除的像素和之前画线的像素完全一致。

        x1, y1 = self.polar_to_xy(
            angle,
            self.radius
        )

        x0 = self.cx
        y0 = self.cy

        dx = abs(x1 - x0)

        sx = 1 if x0 < x1 else -1

        dy = -abs(y1 - y0)

        sy = 1 if y0 < y1 else -1

        err = dx + dy

        while True:

            self.restore_pixel(
                x0,
                y0
            )

            if (
                x0 == x1 and
                y0 == y1
            ):
                break

            e2 = 2 * err

            if e2 >= dy:

                err += dy
                x0 += sx

            if e2 <= dx:

                err += dx
                y0 += sy

        # =====================================================
        # 恢复目标点
        # =====================================================

        self.redraw_targets()

    # =========================================================
    # Draw current scan line
    # =========================================================

    def draw_scan_line(self):

        x, y = self.polar_to_xy(
            self.angle,
            self.radius
        )

        self.tft.line(
            self.cx,
            self.cy,
            x,
            y,
            self.SCAN_COLOR
        )

        self.last_line_angle = self.angle

    # =========================================================
    # Add target
    # =========================================================

    def add_target(
        self,
        angle,
        distance
    ):

        # 当前轮扫描中保存
        self.targets.append(
            (
                angle,
                distance
            )
        )

        # 当前轮最多 30 个
        if len(self.targets) > 30:

            self.targets.pop(0)

    # =========================================================
    # Draw target
    # =========================================================

    def draw_target(
        self,
        angle,
        distance
    ):

        if distance <= 0:
            return

        if distance > self.max_distance:
            return

        # 实际距离 -> 雷达半径
        display_distance = int(
            distance /
            self.max_distance *
            self.radius
        )

        x, y = self.polar_to_xy(
            angle,
            display_distance
        )

        # 边界检查
        if x < 3:
            return

        if x >= self.tft.width - 3:
            return

        if y < 3:
            return

        if y >= self.tft.height - 3:
            return

        # 5x5 红点
        self.tft.fill_rect(
            x - 2,
            y - 2,
            5,
            5,
            self.TARGET_COLOR
        )

    # =========================================================
    # Redraw targets
    # =========================================================

    def redraw_targets(self):

        for angle, distance in self.targets:

            self.draw_target(
                angle,
                distance
            )

    # =========================================================
    # Clear all targets
    #
    # 通过重新绘制背景彻底删除
    # =========================================================

    def clear_targets(self):

        self.targets = []

        # 重新画完整雷达
        self.draw_background()

        # 当前扫描线重新画回来
        if self.scanning:

            self.draw_scan_line()

    # =========================================================
    # Scan once
    # =========================================================

    def scan_once(self):

        if not self.scanning:
            return

        # =====================================================
        # 1. 删除上一条扫描线
        # =====================================================

        self.erase_scan_line()

        # =====================================================
        # 2. Servo
        # =====================================================

        self.servo.move(
            self.angle
        )

        # =====================================================
        # 3. Wait
        # =====================================================

        if self.settle_ms > 0:

            time.sleep_ms(
                self.settle_ms
            )

        # =====================================================
        # 4. Ultrasonic measurement
        # =====================================================

        distance = (
            self.sensor.distance_cm()
        )

        self.last_distance = distance

        # =====================================================
        # 5. Target
        # =====================================================

        if (
            distance > 0 and
            distance <= self.max_distance
        ):

            self.add_target(
                self.angle,
                distance
            )

        # =====================================================
        # 6. Draw current scan line
        # =====================================================

        self.draw_scan_line()

        # =====================================================
        # 7. Draw newest target
        # =====================================================

        if (
            distance > 0 and
            distance <= self.max_distance
        ):

            self.draw_target(
                self.angle,
                distance
            )

        # =====================================================
        # 8. Next angle
        # =====================================================

        self.angle += (
            self.direction *
            self.step
        )

        # =====================================================
        # 9. Right boundary
        # =====================================================

        if self.angle >= self.max_angle:

            self.angle = self.max_angle

            self.direction = -1

        # =====================================================
        # 10. Left boundary
        # =====================================================

        elif self.angle <= self.min_angle:

            self.angle = self.min_angle

            self.direction = 1

            # =================================================
            # 完成一整轮
            # =================================================

            self.scan_count += 1

            print(
                "[RADAR] SCAN",
                self.scan_count
            )

            # =================================================
            # 清除上一轮所有红点
            # =================================================

            self.clear_targets()

    # =========================================================
    # Clear
    # =========================================================

    def clear(self):

        self.targets = []

        self.last_line_angle = None

        self.last_distance = -1

        self.draw_background()

    # =========================================================
    # Stop
    # =========================================================

    def stop(self):

        self.scanning = False

        # 停止后重新绘制干净背景
        self.draw_background()

        self.targets = []

        self.last_line_angle = None

        print("[RADAR] STOP")

    # =========================================================
    # Nearest target
    # =========================================================

    def get_nearest(self):

        if not self.targets:
            return None

        nearest = self.targets[0]

        for target in self.targets:

            if target[1] < nearest[1]:

                nearest = target

        return nearest

    # =========================================================
    # Status
    # =========================================================

    def status(self):

        nearest = self.get_nearest()

        return {
            "scanning": self.scanning,
            "angle": self.angle,
            "direction": self.direction,
            "distance": self.last_distance,
            "target_count": len(self.targets),
            "nearest": nearest,
            "scan_count": self.scan_count
        }