import socket
import json
import time


class RadarTCPServer:

    def __init__(
        self,
        radar,
        port=8888
    ):

        self.radar = radar

        self.port = port

        self.server = None

        self.client = None

        self.rx_buffer = ""


    # =====================================================
    # 启动 TCP Server
    # =====================================================

    def start(self):

        addr = socket.getaddrinfo(
            "0.0.0.0",
            self.port
        )[0][-1]


        self.server = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )


        self.server.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )


        self.server.bind(addr)

        self.server.listen(1)

        self.server.setblocking(False)


        print(
            "[TCP] SERVER START:",
            self.port
        )


    # =====================================================
    # 接收 PC
    # =====================================================

    def accept_client(self):

        if self.server is None:

            return


        if self.client is not None:

            return


        try:

            client, addr = \
                self.server.accept()


            client.setblocking(False)

            self.client = client

            self.rx_buffer = ""


            print(
                "[TCP] CLIENT:",
                addr
            )


        except OSError:

            pass


    # =====================================================
    # 处理 PC 命令
    # =====================================================

    def handle_client(self):

        if self.client is None:

            return


        try:

            data = self.client.recv(
                1024
            )


            if not data:

                self.close_client()

                return


            self.rx_buffer += \
                data.decode()


            while "\n" in self.rx_buffer:

                line, self.rx_buffer = \
                    self.rx_buffer.split(
                        "\n",
                        1
                    )


                line = line.strip()


                if line:

                    self.handle_command(
                        line
                    )


        except OSError:

            pass

        except Exception as e:

            print(
                "[TCP] RX ERROR:",
                e
            )


    # =====================================================
    # 处理 JSON 命令
    # =====================================================

    def handle_command(
        self,
        line
    ):

        try:

            command = json.loads(
                line
            )

        except Exception:

            print(
                "[TCP] BAD JSON:",
                line
            )

            return


        cmd = command.get(
            "cmd"
        )


        print(
            "[TCP] CMD:",
            cmd
        )


        if cmd == "start":

            self.radar.start()


        elif cmd == "stop":

            self.radar.stop()


        elif cmd == "clear":

            self.radar.clear()


        elif cmd == "config":

            step = command.get(
                "step"
            )

            if step is not None:

                self.radar.set_step(
                    step
                )


    # =====================================================
    # 发送数据
    # =====================================================

    def send_data(self):

        if self.client is None:

            return


        try:

            data = self.radar.get_data()


            message = json.dumps(
                data
            ) + "\n"


            self.client.send(
                message.encode()
            )


        except OSError:

            self.close_client()


        except Exception as e:

            print(
                "[TCP] TX ERROR:",
                e
            )

            self.close_client()


    # =====================================================
    # 关闭客户端
    # =====================================================

    def close_client(self):

        if self.client is not None:

            try:

                self.client.close()

            except Exception:

                pass


        self.client = None

        self.rx_buffer = ""


        print(
            "[TCP] CLIENT DISCONNECTED"
        )


    # =====================================================
    # 主循环处理
    # =====================================================

    def update(self):

        self.accept_client()

        self.handle_client()