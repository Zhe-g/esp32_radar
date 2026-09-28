import math
import time


class Radar:

    BLACK = 0x0000
    WHITE = 0xFFFF

    GRID_COLOR = 0x03EF

    SCAN_COLOR = 0x07FF

    TARGET_COLOR = 0xF800

    CENTER_COLOR = 0x07E0


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

        self.max_distance = \
            max_distance

        self.settle_ms = settle_ms


        self.cx = \
            self.tft.width // 2

        self.cy = \
            self.tft.height - 15


        self.radius = min(
            self.tft.width // 2 - 5,
            self.tft.height - 30
        )


        self.angle = \
            self.min_angle

        self.direction = 1

        self.scanning = False

        self.targets = []

        self.scan_count = 0

        self.last_distance = -1

        self.last_line_angle = None


    # =====================================================
    # 启动
    # =====================================================

    def start(self):

        self.scanning = True

        self.angle = self.min_angle

        self.direction = 1

        self.targets = []

        self.scan_count = 0

        self.last_distance = -1

        self.last_line_angle = None


        self.draw_background()

        self.servo.move(
            self.angle
        )

        print("[RADAR] START")


    # =====================================================
    # 坐标转换
    # =====================================================

    def polar_to_xy(
        self,
        angle,
        distance
    ):

        rad = math.radians(
            angle
        )

        x = int(
            self.cx
            +
            math.cos(rad)
            * distance
        )

        y = int(
            self.cy
            -
            math.sin(rad)
            * distance
        )

        return x, y


    # =====================================================
    # 绘制雷达背景
    # =====================================================

    def draw_background(self):

        self.tft.fill(
            self.BLACK
        )


        # 同心圆

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


        # 角度线

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


        # 中心点

        self.tft.fill_rect(
            self.cx - 2,
            self.cy - 2,
            5,
            5,
            self.CENTER_COLOR
        )


    # =====================================================
    # 背景像素恢复
    # =====================================================

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


        if distance > self.radius + 1:

            return self.BLACK


        circles = (
            self.radius,
            self.radius * 0.75,
            self.radius * 0.50,
            self.radius * 0.25
        )


        for r in circles:

            if abs(
                distance - r
            ) <= 1.0:

                return self.GRID_COLOR


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

                if abs(
                    angle - a
                ) <= 0.6:

                    return self.GRID_COLOR


        if (
            abs(dx) <= 2
            and
            abs(dy) <= 2
        ):

            return self.CENTER_COLOR


        return self.BLACK


    # =====================================================
    # 恢复扫描线
    # =====================================================

    def restore_pixel(
        self,
        x,
        y
    ):

        if (
            x < 0
            or
            x >= self.tft.width
        ):

            return


        if (
            y < 0
            or
            y >= self.tft.height
        ):

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


    # =====================================================
    # 删除旧扫描线
    # =====================================================

    def erase_scan_line(self):

        if self.last_line_angle is None:

            return


        angle = \
            self.last_line_angle


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
                x0 == x1
                and
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


        self.redraw_targets()


    # =====================================================
    # 绘制扫描线
    # =====================================================

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


        self.last_line_angle = \
            self.angle


    # =====================================================
    # 添加目标
    # =====================================================

    def add_target(
        self,
        angle,
        distance
    ):

        self.targets.append(
            (
                angle,
                distance
            )
        )


        if len(self.targets) > 30:

            self.targets.pop(0)


    # =====================================================
    # 绘制目标
    # =====================================================

    def draw_target(
        self,
        angle,
        distance
    ):

        if (
            distance <= 0
            or
            distance > self.max_distance
        ):

            return


        display_distance = int(
            distance
            /
            self.max_distance
            *
            self.radius
        )


        x, y = self.polar_to_xy(
            angle,
            display_distance
        )


        if (
            x < 3
            or
            x >= self.tft.width - 3
        ):

            return


        if (
            y < 3
            or
            y >= self.tft.height - 3
        ):

            return


        self.tft.fill_rect(
            x - 2,
            y - 2,
            5,
            5,
            self.TARGET_COLOR
        )


    # =====================================================
    # 重新绘制所有目标
    # =====================================================

    def redraw_targets(self):

        for angle, distance in self.targets:

            self.draw_target(
                angle,
                distance
            )


    # =====================================================
    # 清除目标
    # =====================================================

    def clear_targets(self):

        self.targets = []

        self.draw_background()


        if self.scanning:

            self.draw_scan_line()


    # =====================================================
    # 单次扫描
    # =====================================================

    def scan_once(self):

        if not self.scanning:

            return


        self.erase_scan_line()


        self.servo.move(
            self.angle
        )


        if self.settle_ms > 0:

            time.sleep_ms(
                self.settle_ms
            )


        distance = \
            self.sensor.distance_cm()


        self.last_distance = \
            distance


        if (
            distance > 0
            and
            distance <= self.max_distance
        ):

            self.add_target(
                self.angle,
                distance
            )


        self.draw_scan_line()


        if (
            distance > 0
            and
            distance <= self.max_distance
        ):

            self.draw_target(
                self.angle,
                distance
            )


        self.angle += (
            self.direction
            *
            self.step
        )


        if self.angle >= self.max_angle:

            self.angle = \
                self.max_angle

            self.direction = -1


        elif self.angle <= self.min_angle:

            self.angle = \
                self.min_angle

            self.direction = 1


            self.scan_count += 1


            print(
                "[RADAR] SCAN",
                self.scan_count
            )


            self.clear_targets()


    # =====================================================
    # 设置步进
    # =====================================================

    def set_step(
        self,
        step
    ):

        step = int(step)

        if step < 1:

            step = 1

        if step > 20:

            step = 20


        self.step = step


        print(
            "[RADAR] STEP =",
            self.step
        )


    # =====================================================
    # 清除
    # =====================================================

    def clear(self):

        self.targets = []

        self.last_line_angle = None

        self.last_distance = -1

        self.draw_background()


    # =====================================================
    # 停止
    # =====================================================

    def stop(self):

        self.scanning = False

        self.draw_background()

        self.targets = []

        self.last_line_angle = None

        print("[RADAR] STOP")


    # =====================================================
    # 最近目标
    # =====================================================

    def get_nearest(self):

        if not self.targets:

            return None


        nearest = self.targets[0]


        for target in self.targets:

            if target[1] < nearest[1]:

                nearest = target


        return nearest


    # =====================================================
    # 获取 Web 数据
    # =====================================================

    def get_data(self):

        nearest = \
            self.get_nearest()


        return {

            "type": "data",

            "scanning":
                self.scanning,

            "angle":
                self.angle,

            "distance":
                self.last_distance,

            "nearest":
                nearest[1]
                if nearest
                else -1,

            "points":
                self.targets,

            "scan_count":
                self.scan_count

        }