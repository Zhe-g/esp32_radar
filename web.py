# =========================================================
# ESP32 Radar Web Server
# =========================================================

import network
import socket
import time
import json


class WebServer:

    def __init__(
        self,
        radar,
        ssid,
        password,
        port=80
    ):

        self.radar = radar

        self.ssid = ssid
        self.password = password

        self.port = port

        self.wlan = None
        self.server = None

        self.connected = False
        self.ip = None

        self.running = False


    # =====================================================
    # WiFi
    # =====================================================

    def connect_wifi(self, timeout_s=10, progress_callback=None):

        print()
        print("================================")
        print(" WIFI CONNECT")
        print("================================")

        # 创建 STA
        self.wlan = network.WLAN(
            network.STA_IF
        )

        self.wlan.active(True)

        # 如果之前已经连接
        if self.wlan.isconnected():

            self.connected = True

            self.ip = self.wlan.ifconfig()[0]

            print("WiFi already connected")
            print("IP:", self.ip)

            if progress_callback:
                progress_callback(
                    "CONNECTED",
                    self.ip
                )

            return True


        # 开始连接
        print("SSID:", self.ssid)

        try:

            self.wlan.disconnect()

        except Exception:
            pass


        try:

            self.wlan.connect(
                self.ssid,
                self.password
            )

        except Exception as e:

            print("WiFi connect error:")
            print(e)

            self.connected = False

            if progress_callback:
                progress_callback(
                    "ERROR",
                    str(e)
                )

            return False


        start_time = time.ticks_ms()

        last_second = -1


        while True:

            # 已连接
            if self.wlan.isconnected():

                self.connected = True

                self.ip = self.wlan.ifconfig()[0]

                print()
                print("WiFi connected!")
                print("IP address:")
                print(self.ip)

                if progress_callback:
                    progress_callback(
                        "CONNECTED",
                        self.ip
                    )

                return True


            # 计算已经等待多久
            elapsed_ms = time.ticks_diff(
                time.ticks_ms(),
                start_time
            )

            elapsed_s = elapsed_ms // 1000


            # TFT / 串口显示倒计时
            if elapsed_s != last_second:

                last_second = elapsed_s

                print(
                    "WiFi connecting... {} / {} s".format(
                        elapsed_s,
                        timeout_s
                    )
                )

                if progress_callback:

                    progress_callback(
                        "CONNECTING",
                        "{} / {}s".format(
                            elapsed_s,
                            timeout_s
                        )
                    )


            # 超时
            if elapsed_ms >= timeout_s * 1000:

                print()
                print("WiFi connection TIMEOUT")
                print("Skip WiFi.")

                self.connected = False
                self.ip = None

                try:
                    self.wlan.disconnect()
                except Exception:
                    pass

                if progress_callback:

                    progress_callback(
                        "TIMEOUT",
                        "SKIP WIFI"
                    )

                return False


            time.sleep_ms(100)


    # =====================================================
    # Web Server
    # =====================================================

    def start(self):

        # WiFi 没连接
        if not self.connected:

            print("Web server skipped.")

            self.running = False

            return False


        try:

            addr = socket.getaddrinfo(
                "0.0.0.0",
                self.port
            )[0][-1]

            self.server = socket.socket()

            self.server.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_REUSEADDR,
                1
            )

            self.server.bind(addr)

            self.server.listen(1)

            # 非阻塞
            self.server.setblocking(False)

            self.running = True

            print()
            print("================================")
            print(" WEB SERVER STARTED")
            print("================================")

            print(
                "http://{}/".format(
                    self.ip
                )
            )

            return True


        except Exception as e:

            print("Web server start error:")
            print(e)

            self.running = False

            return False


    # =====================================================
    # Handle HTTP request
    # =====================================================

    def handle(self):

        # 没有 WiFi
        if not self.connected:
            return


        # Web Server 没启动
        if not self.running:
            return


        try:

            client, addr = self.server.accept()

        except Exception:

            # 没有新的连接
            return


        try:

            client.settimeout(1)

            request = client.recv(2048)

            if not request:

                client.close()

                return


            request = request.decode(
                "utf-8",
                "ignore"
            )


            # 第一行
            first_line = request.split(
                "\r\n"
            )[0]

            parts = first_line.split(" ")

            if len(parts) < 2:

                client.close()

                return


            path = parts[1]


            # =============================================
            # START
            # =============================================

            if path == "/start":

                self.radar.start()

                self.send_text(
                    client,
                    "START"
                )


            # =============================================
            # STOP
            # =============================================

            elif path == "/stop":

                self.radar.stop()

                self.send_text(
                    client,
                    "STOP"
                )


            # =============================================
            # DATA
            # =============================================

            elif path == "/data":

                data = self.radar.get_data()

                self.send_json(
                    client,
                    data
                )


            # =============================================
            # HTML
            # =============================================

            else:

                html = self.get_html()

                self.send_html(
                    client,
                    html
                )


        except Exception as e:

            print(
                "HTTP error:",
                e
            )


        finally:

            try:
                client.close()
            except Exception:
                pass


    # =====================================================
    # HTTP response
    # =====================================================

    def send_text(
        self,
        client,
        text
    ):

        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/plain\r\n"
            "Connection: close\r\n"
            "\r\n"
            + text
        )

        client.send(
            response.encode()
        )


    def send_json(
        self,
        client,
        data
    ):

        body = json.dumps(
            data
        )

        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: application/json\r\n"
            "Access-Control-Allow-Origin: *\r\n"
            "Connection: close\r\n"
            "\r\n"
            + body
        )

        client.send(
            response.encode()
        )


    def send_html(
        self,
        client,
        html
    ):

        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/html; charset=utf-8\r\n"
            "Connection: close\r\n"
            "\r\n"
            + html
        )

        client.send(
            response.encode()
        )


    # =====================================================
    # Web page
    # =====================================================

    def get_html(self):

        return """<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width,initial-scale=1.0">

<title>ESP32 Radar</title>

<style>

body {
    background: #111;
    color: white;
    font-family: Arial;
    text-align: center;
}

canvas {
    background: #000;
    border: 1px solid #333;
    max-width: 95vw;
}

button {
    font-size: 18px;
    padding: 10px 25px;
    margin: 8px;
}

#info {
    margin: 10px;
    font-size: 18px;
}

</style>

</head>


<body>

<h2>ESP32 WiFi Radar</h2>

<canvas
    id="radar"
    width="500"
    height="300">
</canvas>

<br>

<button onclick="startRadar()">
START
</button>

<button onclick="stopRadar()">
STOP
</button>

<div id="info">
Waiting...
</div>


<script>

const canvas =
    document.getElementById("radar");

const ctx =
    canvas.getContext("2d");


let data = {
    angle: 90,
    distance: -1,
    scanning: false,
    nearest: -1,
    points: []
};


function startRadar() {

    fetch("/start");

}


function stopRadar() {

    fetch("/stop");

}


function draw() {

    ctx.fillStyle = "#000";

    ctx.fillRect(
        0,
        0,
        canvas.width,
        canvas.height
    );


    const cx = 250;
    const cy = 270;

    const radius = 220;


    // 雷达圆

    ctx.strokeStyle = "#00ff00";

    ctx.lineWidth = 1;


    for (
        let r = 50;
        r <= radius;
        r += 50
    ) {

        ctx.beginPath();

        ctx.arc(
            cx,
            cy,
            r,
            Math.PI,
            Math.PI * 2
        );

        ctx.stroke();

    }


    // 中心线

    ctx.beginPath();

    ctx.moveTo(
        cx - radius,
        cy
    );

    ctx.lineTo(
        cx + radius,
        cy
    );

    ctx.stroke();


    // 扫描线

    let angle =
        data.angle * Math.PI / 180;


    let x =
        cx +
        Math.cos(
            Math.PI - angle
        ) * radius;


    let y =
        cy -
        Math.sin(
            angle
        ) * radius;


    ctx.strokeStyle = "#00ff00";

    ctx.beginPath();

    ctx.moveTo(
        cx,
        cy
    );

    ctx.lineTo(
        x,
        y
    );

    ctx.stroke();


    // 点

    if (data.points) {

        data.points.forEach(
            function(p) {

                let a =
                    p[0] *
                    Math.PI /
                    180;

                let d =
                    p[1];

                if (
                    d <= 0 ||
                    d > 200
                ) {
                    return;
                }


                let rr =
                    d /
                    200 *
                    radius;


                let px =
                    cx +
                    Math.cos(
                        Math.PI - a
                    ) * rr;


                let py =
                    cy -
                    Math.sin(
                        a
                    ) * rr;


                ctx.fillStyle =
                    "#ff3333";

                ctx.fillRect(
                    px - 3,
                    py - 3,
                    6,
                    6
                );

            }
        );

    }


    document.getElementById(
        "info"
    ).innerHTML =
        "Angle: " +
        data.angle +
        "°　 Distance: " +
        data.distance +
        " cm　 Nearest: " +
        data.nearest +
        " cm";


    requestAnimationFrame(
        draw
    );

}


async function updateData() {

    try {

        const response =
            await fetch(
                "/data"
            );

        data =
            await response.json();

    }
    catch(e) {

        console.log(e);

    }

}


setInterval(
    updateData,
    100
);


draw();

</script>

</body>

</html>
"""