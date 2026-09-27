from machine import Pin
import time


class ST7789:

    def __init__(
        self,
        width,
        height,
        spi,
        cs,
        dc,
        rst,
        x_offset=0,
        y_offset=0
    ):
        self.width = width
        self.height = height
        self.spi = spi

        self.cs = Pin(cs, Pin.OUT, value=1)
        self.dc = Pin(dc, Pin.OUT, value=0)
        self.rst = Pin(rst, Pin.OUT, value=1)

        self.x_offset = x_offset
        self.y_offset = y_offset

        self._reset()
        self._init_display()

    # =========================
    # Basic communication
    # =========================

    def _reset(self):
        self.rst.value(1)
        time.sleep_ms(50)

        self.rst.value(0)
        time.sleep_ms(120)

        self.rst.value(1)
        time.sleep_ms(120)

    def _write_cmd(self, cmd):
        self.cs.value(0)
        self.dc.value(0)
        self.spi.write(bytes([cmd]))
        self.cs.value(1)

    def _write_data(self, data):
        self.cs.value(0)
        self.dc.value(1)
        self.spi.write(data)
        self.cs.value(1)

    # =========================
    # ST7789 initialization
    # =========================

    def _init_display(self):

        self._write_cmd(0x01)
        time.sleep_ms(150)

        self._write_cmd(0x11)
        time.sleep_ms(120)

        # RGB565
        self._write_cmd(0x3A)
        self._write_data(b'\x55')

        # Memory access control
        self._write_cmd(0x36)
        self._write_data(b'\x00')

        # Display inversion ON
        self._write_cmd(0x21)

        self._write_cmd(0x13)

        self._write_cmd(0x29)
        time.sleep_ms(100)

    # =========================
    # Set drawing window
    # =========================

    def _set_window(self, x0, y0, x1, y1):

        x0 += self.x_offset
        x1 += self.x_offset

        y0 += self.y_offset
        y1 += self.y_offset

        # Column address
        self._write_cmd(0x2A)

        self._write_data(bytes([
            (x0 >> 8) & 0xFF,
            x0 & 0xFF,
            (x1 >> 8) & 0xFF,
            x1 & 0xFF
        ]))

        # Row address
        self._write_cmd(0x2B)

        self._write_data(bytes([
            (y0 >> 8) & 0xFF,
            y0 & 0xFF,
            (y1 >> 8) & 0xFF,
            y1 & 0xFF
        ]))

        # Memory write
        self._write_cmd(0x2C)

    # =========================
    # Fill screen
    # =========================

    def fill(self, color):

        hi = (color >> 8) & 0xFF
        lo = color & 0xFF

        row = bytes([hi, lo]) * self.width

        self._set_window(
            0,
            0,
            self.width - 1,
            self.height - 1
        )

        self.cs.value(0)
        self.dc.value(1)

        for _ in range(self.height):
            self.spi.write(row)

        self.cs.value(1)

    # =========================
    # Fill rectangle
    # =========================

    def fill_rect(self, x, y, w, h, color):

        if w <= 0 or h <= 0:
            return

        if x >= self.width or y >= self.height:
            return

        if x + w <= 0 or y + h <= 0:
            return

        x0 = max(0, x)
        y0 = max(0, y)

        x1 = min(self.width - 1, x + w - 1)
        y1 = min(self.height - 1, y + h - 1)

        width = x1 - x0 + 1
        height = y1 - y0 + 1

        hi = (color >> 8) & 0xFF
        lo = color & 0xFF

        data = bytes([hi, lo]) * width

        self._set_window(
            x0,
            y0,
            x1,
            y1
        )

        self.cs.value(0)
        self.dc.value(1)

        for _ in range(height):
            self.spi.write(data)

        self.cs.value(1)

    # =========================
    # Pixel
    # =========================

    def pixel(self, x, y, color):

        if (
            x < 0
            or x >= self.width
            or y < 0
            or y >= self.height
        ):
            return

        self._set_window(
            x,
            y,
            x,
            y
        )

        self._write_data(bytes([
            (color >> 8) & 0xFF,
            color & 0xFF
        ]))

    # =========================
    # Horizontal line
    # =========================

    def hline(self, x, y, length, color):

        if length <= 0:
            return

        if y < 0 or y >= self.height:
            return

        x0 = max(0, x)
        x1 = min(
            self.width - 1,
            x + length - 1
        )

        if x0 > x1:
            return

        count = x1 - x0 + 1

        pixel = bytes([
            (color >> 8) & 0xFF,
            color & 0xFF
        ])

        self._set_window(
            x0,
            y,
            x1,
            y
        )

        self.cs.value(0)
        self.dc.value(1)

        self.spi.write(pixel * count)

        self.cs.value(1)

    # =========================
    # Vertical line
    # =========================

    def vline(self, x, y, length, color):

        if length <= 0:
            return

        if x < 0 or x >= self.width:
            return

        y0 = max(0, y)
        y1 = min(
            self.height - 1,
            y + length - 1
        )

        if y0 > y1:
            return

        count = y1 - y0 + 1

        pixel = bytes([
            (color >> 8) & 0xFF,
            color & 0xFF
        ])

        self._set_window(
            x,
            y0,
            x,
            y1
        )

        self.cs.value(0)
        self.dc.value(1)

        self.spi.write(pixel * count)

        self.cs.value(1)

    # =========================
    # Rectangle
    # =========================

    def rect(self, x, y, w, h, color):

        self.hline(
            x,
            y,
            w,
            color
        )

        self.hline(
            x,
            y + h - 1,
            w,
            color
        )

        self.vline(
            x,
            y,
            h,
            color
        )

        self.vline(
            x + w - 1,
            y,
            h,
            color
        )

    # =========================
    # Bresenham line
    # =========================

    def line(
        self,
        x0,
        y0,
        x1,
        y1,
        color
    ):

        dx = abs(x1 - x0)
        sx = 1 if x0 < x1 else -1

        dy = -abs(y1 - y0)
        sy = 1 if y0 < y1 else -1

        err = dx + dy

        while True:

            self.pixel(
                x0,
                y0,
                color
            )

            if x0 == x1 and y0 == y1:
                break

            e2 = 2 * err

            if e2 >= dy:
                err += dy
                x0 += sx

            if e2 <= dx:
                err += dx
                y0 += sy

    # =========================
    # Circle
    # =========================

    def circle(
        self,
        cx,
        cy,
        r,
        color
    ):

        x = -r
        y = 0
        err = 2 - 2 * r

        while x < 0:

            self.pixel(
                cx - x,
                cy + y,
                color
            )

            self.pixel(
                cx - y,
                cy - x,
                color
            )

            self.pixel(
                cx + x,
                cy - y,
                color
            )

            self.pixel(
                cx + y,
                cy + x,
                color
            )

            r2 = err

            if r2 <= y:
                y += 1
                err += y * 2 + 1

            if r2 > x or err > y:
                x += 1
                err += x * 2 + 1

    # =========================
    # Small ASCII font
    # =========================

    _FONT = {
        '0':[0x3E,0x51,0x49,0x45,0x3E],
        '1':[0x00,0x42,0x7F,0x40,0x00],
        '2':[0x42,0x61,0x51,0x49,0x46],
        '3':[0x21,0x41,0x45,0x4B,0x31],
        '4':[0x18,0x14,0x12,0x7F,0x10],
        '5':[0x27,0x45,0x45,0x45,0x39],
        '6':[0x3C,0x4A,0x49,0x49,0x30],
        '7':[0x01,0x71,0x09,0x05,0x03],
        '8':[0x36,0x49,0x49,0x49,0x36],
        '9':[0x06,0x49,0x49,0x29,0x1E],

        'A':[0x7E,0x11,0x11,0x11,0x7E],
        'B':[0x7F,0x49,0x49,0x49,0x36],
        'C':[0x3E,0x41,0x41,0x41,0x22],
        'D':[0x7F,0x41,0x41,0x22,0x1C],
        'E':[0x7F,0x49,0x49,0x49,0x41],
        'F':[0x7F,0x09,0x09,0x09,0x01],
        'G':[0x3E,0x41,0x49,0x49,0x7A],
        'H':[0x7F,0x08,0x08,0x08,0x7F],
        'I':[0x00,0x41,0x7F,0x41,0x00],
        'J':[0x20,0x40,0x41,0x3F,0x01],
        'K':[0x7F,0x08,0x14,0x22,0x41],
        'L':[0x7F,0x40,0x40,0x40,0x40],
        'M':[0x7F,0x02,0x0C,0x02,0x7F],
        'N':[0x7F,0x04,0x08,0x10,0x7F],
        'O':[0x3E,0x41,0x41,0x41,0x3E],
        'P':[0x7F,0x09,0x09,0x09,0x06],
        'Q':[0x3E,0x41,0x51,0x21,0x5E],
        'R':[0x7F,0x09,0x19,0x29,0x46],
        'S':[0x46,0x49,0x49,0x49,0x31],
        'T':[0x01,0x01,0x7F,0x01,0x01],
        'U':[0x3F,0x40,0x40,0x40,0x3F],
        'V':[0x1F,0x20,0x40,0x20,0x1F],
        'W':[0x7F,0x20,0x18,0x20,0x7F],
        'X':[0x63,0x14,0x08,0x14,0x63],
        'Y':[0x07,0x08,0x70,0x08,0x07],
        'Z':[0x61,0x51,0x49,0x45,0x43],

        ':':[0x00,0x36,0x36,0x00,0x00],
        '.':[0x00,0x60,0x60,0x00,0x00],
        '-':[0x08,0x08,0x08,0x08,0x08],
        '/':[0x20,0x10,0x08,0x04,0x02],
        ' ':[0x00,0x00,0x00,0x00,0x00]
    }

    def text(
        self,
        string,
        x,
        y,
        color,
        scale=1
    ):

        cursor_x = x

        for ch in str(string):

            glyph = self._FONT.get(
                ch.upper(),
                self._FONT[' ']
            )

            for col in range(5):

                bits = glyph[col]

                for row in range(7):

                    if bits & (1 << row):

                        if scale == 1:

                            self.pixel(
                                cursor_x + col,
                                y + row,
                                color
                            )

                        else:

                            for sx in range(scale):

                                for sy in range(scale):

                                    self.pixel(
                                        cursor_x
                                        + col * scale
                                        + sx,

                                        y
                                        + row * scale
                                        + sy,

                                        color
                                    )

            cursor_x += 6 * scale
