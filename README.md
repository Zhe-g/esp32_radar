# ESP32 超声波雷达系统

基于 **ESP32 + HC-SR04 + MG90S + ST7789 TFT** 实现的嵌入式超声波雷达系统。

项目使用 **MicroPython** 开发，通过舵机带动 HC-SR04 超声波传感器进行水平扫描，在 TFT 屏幕上实时显示雷达扫描结果，同时通过 Wi-Fi 提供 Web 页面，可以在电脑或手机浏览器中查看雷达状态和扫描数据。

---

## 1. 项目简介

本项目实现一个简易的嵌入式超声波雷达系统：

```text
                    HC-SR04
                       │
                       │ 距离测量
                       ▼
                ┌─────────────┐
                │    ESP32    │
                │             │
                │ MicroPython │
                └──────┬──────┘
                       │
          ┌────────────┼────────────┐
          │            │            │
          ▼            ▼            ▼
       MG90S        ST7789 TFT     Wi-Fi
       舵机          雷达显示       Web网页
          │
          ▼
       HC-SR04
       扫描方向
```

ESP32 控制 MG90S 在一定角度范围内往返旋转，HC-SR04 在不同角度测量目标距离，然后将数据转换为极坐标显示在 TFT 上。

系统同时提供 Web 接口，可以通过浏览器查看当前雷达状态。

---

# 2. 主要功能

目前项目实现以下功能：

* [x] ESP32 MicroPython 开发
* [x] MG90S 舵机控制
* [x] HC-SR04 超声波测距
* [x] ST7789 1.54 英寸 TFT 显示
* [x] 雷达扫描动画
* [x] 10°～170° 往返扫描
* [x] 雷达圆形刻度显示
* [x] 当前扫描线显示
* [x] 检测到目标后显示红色目标点
* [x] 一轮完整扫描后清除目标点
* [x] Wi-Fi 连接
* [x] Wi-Fi 连接超时处理
* [x] Wi-Fi 失败后仍可以离线运行雷达
* [x] Web 页面查看雷达数据
* [x] `/start` 启动扫描
* [x] `/stop` 停止扫描
* [x] `/data` 获取当前雷达数据
* [x] 启动过程在 TFT/串口输出状态
* [x] 模块化代码结构

---

# 3. 硬件清单

| 硬件                 | 数量 | 说明              |
| ------------------ | -: | --------------- |
| ESP32-WROOM-32 开发板 |  1 | 主控制器            |
| MG90S 舵机           |  1 | 控制超声波传感器旋转      |
| HC-SR04            |  1 | 超声波测距           |
| ST7789 1.54 英寸 TFT |  1 | 雷达显示            |
| 1kΩ 电阻             |  1 | HC-SR04 ECHO 分压 |
| 2kΩ 电阻             |  1 | HC-SR04 ECHO 分压 |
| 外部 5V 电源           |  1 | 建议给舵机供电         |
| 杜邦线                | 若干 | 连接模块            |

---

# 4. 硬件接线

## 4.1 MG90S 舵机

| MG90S | ESP32/电源 |
| ----- | -------- |
| 信号线   | GPIO13   |
| VCC   | 外部 5V    |
| GND   | GND      |

注意：

**舵机建议使用独立 5V 电源供电。**

ESP32 与舵机电源必须：

```text
ESP32 GND ─────────── 舵机 GND
```

即两者需要共地。

---

## 4.2 HC-SR04

| HC-SR04 | ESP32  |
| ------- | ------ |
| VCC     | 5V     |
| GND     | GND    |
| TRIG    | GPIO5  |
| ECHO    | GPIO19 |

### ECHO 必须进行降压

HC-SR04 的 ECHO 输出通常为 5V，而 ESP32 GPIO 不适合直接承受 5V。

因此使用电阻分压：

```text
HC-SR04 ECHO
     │
    1kΩ
     │
     ├──────── ESP32 GPIO19
     │
    2kΩ
     │
    GND
```

输出电压约：

```text
5V × 2kΩ / (1kΩ + 2kΩ)
≈ 3.33V
```

适合 ESP32 GPIO 输入。

---

## 4.3 ST7789 TFT

当前使用的 TFT 引脚：

| TFT | ESP32  |
| --- | ------ |
| GND | GND    |
| VCC | 3.3V   |
| SCL | GPIO18 |
| SDA | GPIO23 |
| RST | GPIO4  |
| DC  | GPIO2  |
| CS  | GPIO15 |
| BL  | 3.3V   |

SPI 配置：

```text
SPI2
SCK  = GPIO18
MOSI = GPIO23
CS   = GPIO15
DC   = GPIO2
RST  = GPIO4
```

当前屏幕按 **240 × 240** 分辨率配置。

---

# 5. 软件环境

## MicroPython

当前开发板：

```text
ESP32-WROOM-32
```

MicroPython：

```text
MicroPython v1.29.0
```

烧录后通过串口 REPL 与 ESP32 通信。

当前串口：

```text
COM5
```

---

# 6. 项目目录

当前 ESP32 文件系统主要包含：

```text
/
├── boot.py
├── main.py
├── config.py
├── servo.py
├── hcsr04.py
├── radar.py
├── st7789.py
├── web.py
│
├── esp/
├── umqtt/
└── urequests.py
```

其中核心文件：

```text
main.py
config.py
servo.py
hcsr04.py
radar.py
st7789.py
web.py
```

---

# 7. 文件功能说明

## `boot.py`

系统启动文件。

主要用于输出启动信息，例如：

```text
ESP32 Radar booting...
```

随后由 MicroPython 自动运行：

```text
main.py
```

---

## `main.py`

系统主程序。

负责：

1. 初始化配置
2. 初始化 SPI
3. 初始化 TFT
4. 初始化舵机
5. 初始化 HC-SR04
6. 初始化 Radar
7. 初始化 Wi-Fi Web 服务
8. 启动雷达扫描
9. 进入主循环

整体结构：

```text
main.py
   │
   ├── config.py
   │
   ├── servo.py
   │
   ├── hcsr04.py
   │
   ├── st7789.py
   │
   ├── radar.py
   │
   └── web.py
```

---

# 8. `config.py`

用于集中管理系统参数。

当前主要配置：

```python
WIFI_SSID = "你的WiFi名称"
WIFI_PASSWORD = "你的WiFi密码"
WIFI_TIMEOUT_S = 10

SERVO_PIN = 13
MIN_ANGLE = 10
MAX_ANGLE = 170
SCAN_STEP = 5
SERVO_SETTLE_MS = 10

TRIG_PIN = 5
ECHO_PIN = 19
MAX_DISTANCE_CM = 200

TFT_SCK = 18
TFT_MOSI = 23
TFT_CS = 15
TFT_DC = 2
TFT_RST = 4

TFT_WIDTH = 240
TFT_HEIGHT = 240
TFT_BAUDRATE = 40000000

RADAR_MAX_DISTANCE = 200
ALARM_DISTANCE = 30

WEB_PORT = 80
AUTO_START = True
```

因此以后修改硬件引脚或扫描参数时，优先修改 `config.py`，而不是直接修改主程序。

---

# 9. 舵机控制

`servo.py` 对 MG90S 进行了简单封装。

舵机使用：

```text
GPIO13
```

PWM：

```text
50Hz
```

默认脉宽范围：

```text
500us ～ 2500us
```

控制范围：

```text
0° ～ 180°
```

项目实际扫描范围：

```text
10° ～ 170°
```

扫描过程中：

```text
10°
 ↓
15°
 ↓
20°
 ↓
...
 ↓
170°
 ↓
165°
 ↓
160°
 ↓
...
 ↓
10°
```

然后重复。

---

# 10. HC-SR04 测距

`hcsr04.py` 对 HC-SR04 进行了封装。

主要流程：

```text
TRIG 输出 10us 高电平
        │
        ▼
HC-SR04 发射超声波
        │
        ▼
等待 ECHO
        │
        ▼
测量 ECHO 高电平持续时间
        │
        ▼
计算距离
```

距离计算：

```text
distance = duration × 0.0343 / 2
```

单位为厘米。

当前最大测量距离：

```text
200 cm
```

无有效回波时返回：

```text
-1
```

---

# 11. 雷达显示原理

`radar.py` 是整个项目的核心。

雷达采用极坐标方式显示。

假设：

```text
(cx, cy)
```

为雷达中心。

对于：

```text
angle
distance
```

通过：

```text
x = cx + cos(angle) × distance
y = cy - sin(angle) × distance
```

转换成 TFT 屏幕坐标。

因此：

```text
             90°
              │
              │
       120°   │   60°
          ╲   │   ╱
           ╲  │  ╱
            ╲ │ ╱
180° ─────────●───────── 0°
```

最终形成类似真实雷达的扫描效果。

---

# 12. 雷达扫描参数

当前：

```text
最小角度：10°
最大角度：170°
扫描步长：5°
舵机等待：10ms
最大距离：200cm
```

因此每次扫描大约：

```text
10°
15°
20°
25°
...
170°
165°
160°
...
10°
```

每个角度进行一次超声波测距。

---

# 13. TFT 雷达界面

屏幕主要包含：

### 雷达圆

用于表示最大扫描范围。

当前显示多个同心圆：

```text
100%
75%
50%
25%
```

---

### 角度辅助线

显示：

```text
10°
30°
60°
90°
120°
150°
170°
```

用于辅助判断目标所在方向。

---

### 扫描线

使用蓝色/青色扫描线：

```text
中心 ● ───────────────►
```

当前设计只保留：

> **一条正在运动的扫描线**

不会永久保存之前的扫描线。

---

### 目标点

检测到有效目标后：

```text
●
```

使用红色显示。

目标距离越近，目标点越靠近雷达中心。

---

# 14. 目标点清除机制

为了避免目标点不断累积导致屏幕最终变成一片红色，目前采用：

```text
一整轮扫描
    ↓
记录本轮目标
    ↓
10° → 170°
    ↓
170° → 10°
    ↓
完成一轮扫描
    ↓
清除所有目标点
    ↓
重新绘制雷达背景
    ↓
开始下一轮扫描
```

因此红色目标点不会永久累积。

---

# 15. 为什么没有使用 FrameBuffer

项目曾尝试使用：

```text
240 × 240 × 2 bytes
```

的 RGB565 FrameBuffer。

所需内存：

```text
240 × 240 × 2
= 115200 bytes
≈ 112.5 KB
```

在当前 ESP32 MicroPython 环境中可能无法分配足够大的连续内存，因此出现：

```text
MemoryError:
memory allocation failed,
allocating 115200 bytes
```

因此当前项目采用：

> **直接操作 ST7789，而不是创建完整屏幕 FrameBuffer**

这样可以显著降低 RAM 使用量。

---

# 16. ST7789 驱动注意事项

当前 `st7789.py` 使用的是项目原本的 ST7789 驱动。

其构造方式为：

```python
tft = ST7789(
    config.TFT_WIDTH,
    config.TFT_HEIGHT,
    spi,
    config.TFT_CS,
    config.TFT_DC,
    config.TFT_RST
)
```

不要使用：

```python
ST7789(
    spi,
    width,
    height,
    reset=...
)
```

因为当前驱动的构造函数并不是这种形式。

同时：

```python
tft.init()
```

也不需要调用。

ST7789 在创建对象时已经执行初始化。

---

# 17. Wi-Fi 功能

系统启动后尝试连接指定 Wi-Fi。

默认超时时间：

```text
10 秒
```

启动流程：

```text
ESP32 启动
    │
    ▼
初始化硬件
    │
    ▼
尝试连接 Wi-Fi
    │
    ├── 成功
    │     │
    │     ▼
    │   启动 Web Server
    │
    └── 超时/失败
          │
          ▼
      跳过 Web
          │
          ▼
      雷达继续运行
```

这样即使没有 Wi-Fi，雷达的核心功能仍然可以正常运行。

---

# 18. Web 服务

连接 Wi-Fi 后，ESP32 会启动 HTTP Web Server。

默认端口：

```text
80
```

浏览器访问：

```text
http://ESP32_IP/
```

即可进入雷达网页。

---

# 19. Web API

当前设计包含：

## 启动扫描

```text
/start
```

---

## 停止扫描

```text
/stop
```

---

## 获取雷达数据

```text
/data
```

用于获取当前雷达状态，例如：

```json
{
    "scanning": true,
    "angle": 90,
    "direction": 1,
    "distance": 35.2,
    "target_count": 2,
    "scan_count": 3
}
```

具体字段以当前 `web.py` 实现为准。

---

# 20. `Radar.status()`

雷达模块提供状态接口：

```python
radar.status()
```

返回当前状态信息，包括：

```text
scanning
angle
direction
distance
target_count
nearest
scan_count
```

例如：

```python
{
    "scanning": True,
    "angle": 90,
    "direction": 1,
    "distance": 35.2,
    "target_count": 2,
    "nearest": (85, 28.4),
    "scan_count": 3
}
```

---

# 21. 系统启动流程

ESP32 上电后：

```text
                 ESP32 上电
                     │
                     ▼
                  boot.py
                     │
                     ▼
                  main.py
                     │
                     ▼
             初始化系统配置
                     │
                     ▼
                初始化 TFT
                     │
                     ▼
                初始化舵机
                     │
                     ▼
              初始化 HC-SR04
                     │
                     ▼
               初始化 Radar
                     │
                     ▼
              尝试连接 Wi-Fi
                /          \
             成功           失败
              │              │
              ▼              ▼
          Web Server       离线模式
              │              │
              └──────┬───────┘
                     ▼
                 启动扫描
                     │
                     ▼
              舵机旋转 + 测距
                     │
                     ▼
                 TFT 显示
                     │
                     ▼
               循环扫描
```

---

# 22. 启动日志

正常情况下，可以在串口 REPL 中看到类似：

```text
ESP32 Radar booting...

[BOOT] STEP 1 - CONFIG
[BOOT] CONFIG OK

[BOOT] STEP 2 - TFT
[BOOT] TFT OK

[BOOT] STEP 3 - SERVO
[BOOT] SERVO OK

[BOOT] STEP 4 - HC-SR04
[BOOT] HC-SR04 OK

[BOOT] STEP 5 - RADAR
[RADAR] START

[BOOT] STEP 6 - WIFI
[WIFI] CONNECTING...
[WIFI] CONNECTED
```

如果 Wi-Fi 连接失败：

```text
[WIFI] TIMEOUT
```

系统应该继续执行雷达扫描，而不是直接停止。

---

# 23. 开发与上传

可以使用：

* VS Code
* MicroPython 插件
* 串口 REPL
* ESP32 COM5

连接后可以进入：

```text
MicroPython REPL
```

例如：

```text
>>>
```

可以测试：

```python
import machine
print(machine.freq())
```

---

# 24. 单独测试舵机

可以先测试：

```python
from servo import Servo

servo = Servo(13)

servo.move(90)
```

然后：

```python
servo.move(10)
```

以及：

```python
servo.move(170)
```

确认舵机能够正常旋转后，再进行完整雷达测试。

---

# 25. 单独测试 HC-SR04

```python
from hcsr04 import HCSR04

sensor = HCSR04(5, 19)

print(sensor.distance_cm())
```

如果前方有物体，应返回类似：

```text
26.8
35.2
48.6
```

单位为：

```text
cm
```

如果没有检测到有效回波：

```text
-1
```

---

# 26. 项目中的重要注意事项

## 26.1 舵机不要直接从 ESP32 3.3V 供电

MG90S 工作电流会明显高于 ESP32 GPIO/3.3V 电源适合提供的电流。

建议：

```text
外部 5V → 舵机 VCC
ESP32 GND ↔ 外部电源 GND
```

---

## 26.2 HC-SR04 ECHO 必须降压

不要直接：

```text
HC-SR04 ECHO → GPIO19
```

而应该使用：

```text
ECHO
 │
1kΩ
 │
 ├──── GPIO19
 │
2kΩ
 │
GND
```

---

## 26.3 TFT 使用 3.3V

当前 TFT：

```text
VCC → 3.3V
BL  → 3.3V
```

---

## 26.4 不要随意修改 `st7789.py`

当前 `radar.py` 依赖原有 ST7789 API。

尤其是：

```python
text()
```

等函数的参数形式必须保持一致。

如果更换 ST7789 驱动，需要同步修改整个项目。

---

# 27. 当前项目限制

目前项目已经能够完成基本的雷达扫描，但仍存在一些可以继续优化的问题。

### 1. 扫描速度

当前：

```text
SCAN_STEP = 5°
SERVO_SETTLE_MS = 10ms
```

速度和稳定性之间进行了简单平衡。

---

### 2. 测距精度

HC-SR04 本身受到：

* 环境噪声
* 目标材质
* 目标角度
* 温度
* 超声波反射
* 舵机振动

等因素影响。

因此雷达显示主要用于：

> **目标方向和大致距离检测**

而不是精密测距。

---

### 3. TFT 绘图效率

当前没有使用完整 FrameBuffer，而是直接向 ST7789 绘制。

这是为了降低 RAM 使用量，但也意味着：

```text
复杂图形绘制
```

可能受到 ESP32 MicroPython 性能限制。

---

### 4. 目标识别

当前系统检测的是：

```text
某个角度是否存在有效距离回波
```

并不是计算机视觉意义上的目标识别。

因此多个物体、复杂反射环境下可能出现：

* 虚假目标
* 距离跳变
* 目标点抖动

等情况。

---

# 28. 后续可扩展方向

项目后续可以继续增加：

### 雷达算法

* [ ] 距离滑动平均
* [ ] 中值滤波
* [ ] 多次采样平均
* [ ] 异常值过滤
* [ ] 目标持续跟踪
* [ ] 多目标检测

### TFT

* [ ] 距离刻度
* [ ] 当前角度显示
* [ ] 当前距离显示
* [ ] 最近目标显示
* [ ] 扫描次数显示
* [ ] 状态栏
* [ ] Wi-Fi 状态显示

### Web

* [ ] 实时雷达动画
* [ ] 历史扫描数据
* [ ] 距离曲线
* [ ] 目标数量统计
* [ ] 扫描参数调整
* [ ] Web 控制舵机
* [ ] Web 修改扫描范围

### 系统

* [ ] Wi-Fi AP 模式
* [ ] WebSocket 实时数据
* [ ] 配置持久化
* [ ] 看门狗
* [ ] 异常自动恢复
* [ ] 更高效的 ST7789 绘图方式

---

# 29. 项目技术栈

```text
硬件
├── ESP32-WROOM-32
├── MG90S
├── HC-SR04
└── ST7789 TFT

软件
├── MicroPython 1.29.0
├── Python
├── SPI
├── PWM
├── Wi-Fi
└── HTTP Server
```

---

# 30. 项目核心逻辑总结

整个系统可以概括为：

```text
                 ┌──────────────┐
                 │    ESP32     │
                 └──────┬───────┘
                        │
             ┌──────────┴──────────┐
             │                     │
             ▼                     ▼
          MG90S                  Wi-Fi
             │                     │
             ▼                     ▼
          HC-SR04              Web Server
             │
             │ distance
             ▼
          Radar.py
             │
             ├──────────────┐
             │              │
             ▼              ▼
          TFT显示          状态数据
             │              │
             ▼              ▼
        雷达扫描图        Web页面
```

项目的核心循环：

```text
舵机转动
   ↓
等待稳定
   ↓
HC-SR04测距
   ↓
获得 angle + distance
   ↓
转换为屏幕坐标
   ↓
绘制目标点
   ↓
移动扫描线
   ↓
继续下一角度
   ↓
完成 10°～170°～10°
   ↓
清除本轮目标
   ↓
重新扫描
```

---

# 31. 当前版本状态

**项目状态：基础功能已完成，可作为后续优化基础。**

当前已经解决的主要问题包括：

* ESP32 舵机控制
* HC-SR04 测距
* ST7789 TFT 初始化
* 雷达极坐标绘制
* 扫描线动画
* 目标点显示
* 目标点周期清理
* Wi-Fi 超时处理
* Web 服务框架
* 模块化程序结构
* ESP32 RAM 限制下的绘图方案调整

目前最需要注意的是：

> **不要重新使用 240×240 的完整 FrameBuffer，否则容易出现约 115200 bytes 的内存分配失败。**

同时：

> **不要随意替换当前 `st7789.py`，因为 `radar.py` 和 `main.py` 依赖现有驱动接口。**

---

# 32. License

本项目主要用于：

* 嵌入式课程实验
* ESP32 学习
* MicroPython 学习
* 超声波雷达原理验证
* TFT 图形显示学习
* IoT / Web 控制实验

可根据实际课程或个人项目需求继续修改和扩展。
