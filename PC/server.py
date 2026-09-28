import json
import socket
import threading
import time

from http.server import (
    ThreadingHTTPServer,
    BaseHTTPRequestHandler
)

from pathlib import Path


# =========================================================
# 配置
# =========================================================

ESP32_HOST = "10.173.90.166"

ESP32_PORT = 8888

WEB_HOST = "0.0.0.0"

WEB_PORT = 8080


BASE_DIR = Path(
    __file__
).resolve().parent


INDEX_FILE = (
    BASE_DIR / "index.html"
)


# =========================================================
# ESP32 数据
# =========================================================

latest_data = {

    "type": "data",

    "scanning": False,

    "angle": 10,

    "distance": -1,

    "nearest": -1,

    "points": [],

    "scan_count": 0
}


data_lock = threading.Lock()


# =========================================================
# ESP32 TCP 管理器
# =========================================================

class ESP32Connection:

    def __init__(self):

        self.sock = None

        self.lock = threading.Lock()

        self.connected = False


    # =====================================================
    # 发送命令
    # =====================================================

    def send_command(
        self,
        command
    ):

        message = (
            json.dumps(
                command
            )
            +
            "\n"
        )


        with self.lock:

            if self.sock is None:

                return False


            try:

                self.sock.sendall(
                    message.encode()
                )

                return True


            except Exception as e:

                print(
                    "[ESP32] SEND ERROR:",
                    e
                )

                self.disconnect()

                return False


    # =====================================================
    # 断开
    # =====================================================

    def disconnect(self):

        with self.lock:

            if self.sock:

                try:

                    self.sock.close()

                except Exception:

                    pass


            self.sock = None

            self.connected = False


    # =====================================================
    # 接收数据
    # =====================================================

    def receiver(self):

        global latest_data


        buffer = ""


        while True:

            if self.sock is None:

                time.sleep(1)

                continue


            try:

                data = self.sock.recv(
                    4096
                )


                if not data:

                    print(
                        "[ESP32] DISCONNECTED"
                    )

                    self.disconnect()

                    continue


                buffer += \
                    data.decode(
                        errors="ignore"
                    )


                while "\n" in buffer:

                    line, buffer = \
                        buffer.split(
                            "\n",
                            1
                        )


                    line = line.strip()


                    if not line:

                        continue


                    try:

                        obj = json.loads(
                            line
                        )


                        if (
                            obj.get("type")
                            ==
                            "data"
                        ):

                            with data_lock:

                                latest_data = obj


                    except Exception as e:

                        print(
                            "[ESP32] JSON ERROR:",
                            e
                        )


            except Exception as e:

                print(
                    "[ESP32] RECEIVE ERROR:",
                    e
                )

                self.disconnect()


    # =====================================================
    # 自动连接
    # =====================================================

    def connector(self):

        while True:

            if self.sock is not None:

                time.sleep(1)

                continue


            print(
                "[ESP32] CONNECTING:",
                ESP32_HOST,
                ESP32_PORT
            )


            try:

                sock = socket.socket(
                    socket.AF_INET,
                    socket.SOCK_STREAM
                )


                sock.settimeout(3)


                sock.connect(
                    (
                        ESP32_HOST,
                        ESP32_PORT
                    )
                )


                sock.settimeout(None)


                with self.lock:

                    self.sock = sock

                    self.connected = True


                print(
                    "[ESP32] CONNECTED"
                )


            except Exception as e:

                print(
                    "[ESP32] CONNECTION FAILED:",
                    e
                )


                try:

                    sock.close()

                except Exception:

                    pass


                time.sleep(2)


    # =====================================================
    # 启动后台线程
    # =====================================================

    def start(self):

        threading.Thread(
            target=self.connector,
            daemon=True
        ).start()


        threading.Thread(
            target=self.receiver,
            daemon=True
        ).start()


# =========================================================
# ESP32 Connection
# =========================================================

esp32 = ESP32Connection()

esp32.start()


# =========================================================
# HTTP Handler
# =========================================================

class RadarHTTPHandler(
    BaseHTTPRequestHandler
):


    # -----------------------------------------------------
    # 日志
    # -----------------------------------------------------

    def log_message(
        self,
        format,
        *args
    ):

        # 不打印每一个浏览器请求
        pass


    # -----------------------------------------------------
    # GET
    # -----------------------------------------------------

    def do_GET(self):

        # -------------------------
        # 首页
        # -------------------------

        if self.path == "/":

            try:

                content = \
                    INDEX_FILE.read_bytes()


                self.send_response(200)

                self.send_header(
                    "Content-Type",
                    "text/html; charset=utf-8"
                )

                self.send_header(
                    "Content-Length",
                    str(len(content))
                )

                self.end_headers()

                self.wfile.write(
                    content
                )


            except Exception as e:

                self.send_error(
                    500,
                    str(e)
                )


            return


        # -------------------------
        # 雷达数据
        # -------------------------

        if self.path == "/data":

            with data_lock:

                data = dict(
                    latest_data
                )


            content = json.dumps(
                data,
                ensure_ascii=False
            ).encode()


            self.send_response(200)

            self.send_header(
                "Content-Type",
                "application/json; charset=utf-8"
            )

            self.send_header(
                "Cache-Control",
                "no-cache"
            )

            self.send_header(
                "Content-Length",
                str(len(content))
            )

            self.end_headers()

            self.wfile.write(
                content
            )


            return


        self.send_error(
            404,
            "Not Found"
        )


    # -----------------------------------------------------
    # POST
    # -----------------------------------------------------

    def do_POST(self):

        if self.path != "/command":

            self.send_error(
                404,
                "Not Found"
            )

            return


        try:

            length = int(
                self.headers.get(
                    "Content-Length",
                    0
                )
            )


            body = self.rfile.read(
                length
            )


            command = json.loads(
                body.decode()
            )


            success = \
                esp32.send_command(
                    command
                )


            result = {

                "ok": success

            }


            content = json.dumps(
                result
            ).encode()


            self.send_response(200)

            self.send_header(
                "Content-Type",
                "application/json"
            )

            self.send_header(
                "Content-Length",
                str(len(content))
            )

            self.end_headers()

            self.wfile.write(
                content
            )


        except Exception as e:

            content = json.dumps({

                "ok": False,

                "error": str(e)

            }).encode()


            self.send_response(500)

            self.send_header(
                "Content-Type",
                "application/json"
            )

            self.send_header(
                "Content-Length",
                str(len(content))
            )

            self.end_headers()

            self.wfile.write(
                content
            )


# =========================================================
# 启动 Web Server
# =========================================================

def main():

    server = ThreadingHTTPServer(
        (
            WEB_HOST,
            WEB_PORT
        ),
        RadarHTTPHandler
    )


    print()
    print(
        "================================"
    )

    print(
        " PC RADAR WEB SERVER"
    )

    print(
        "================================"
    )

    print(
        "Web:",
        f"http://127.0.0.1:{WEB_PORT}"
    )

    print(
        "ESP32:",
        f"{ESP32_HOST}:{ESP32_PORT}"
    )

    print(
        "================================"
    )

    print()


    try:

        server.serve_forever()

    except KeyboardInterrupt:

        print(
            "\n[SERVER] STOP"
        )

        server.shutdown()


if __name__ == "__main__":

    main()