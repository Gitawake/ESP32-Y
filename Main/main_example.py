import machine
import time
import uasyncio as asyncio
import network
import socket

isAP = False
if isAP:
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(ssid='ESP-Socket',key="903903903")
else:
    station = network.WLAN(network.STA_IF)
    station.active(True)

    async def connect_wifi():
        if not station.isconnected():
            station.connect("SuHome2022", "SuJunWei2022")
            while not station.isconnected():
                await asyncio.sleep(1)
        # 打印获取到的 IP 地址
        ip_address = station.ifconfig()[0]
        print("Connected to Wi-Fi. IP Address:", ip_address)



# 定义引脚号
MOTOR1_IN1 = 4  # 使用 GPIO4（D2）
MOTOR1_IN2 = 5  # 使用 GPIO5（D1）
MOTOR1_ENA = 14  # 使用 GPIO14（D5）

MOTOR2_IN1 = 0  # 使用 GPIO0（D3）
MOTOR2_IN2 = 2  # 使用 GPIO2（D4）
MOTOR2_ENA = 12  # 使用 GPIO12（D6）

# 初始化引脚
motor1_in1 = machine.Pin(MOTOR1_IN1, machine.Pin.OUT)
motor1_in2 = machine.Pin(MOTOR1_IN2, machine.Pin.OUT)
motor1_ena = machine.PWM(machine.Pin(MOTOR1_ENA), freq=1000, duty=0)

motor2_in1 = machine.Pin(MOTOR2_IN1, machine.Pin.OUT)
motor2_in2 = machine.Pin(MOTOR2_IN2, machine.Pin.OUT)
motor2_ena = machine.PWM(machine.Pin(MOTOR2_ENA), freq=1000, duty=0)

# 设置电机方向和速度
def set_motor(motor, direction, speed):
    in1 = motor[0]
    in2 = motor[1]
    ena = motor[2]
    
    in1.value(1 if direction == 'forward' else 0)
    in2.value(0 if direction == 'forward' else 1)
    ena.duty(int(speed * 1023 / 100))

async def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 1212))
    server_socket.listen(1)
    print("Server started, waiting for connection...")

    # 设置 server_socket 为非阻塞模式
    server_socket.setblocking(False)

    while True:
        try:
            conn, addr = server_socket.accept()
            print("Connected to:", addr)
            
            last_activity_time = time.time()  # 初始化活动时间戳

            while True:
                try:
                    last_activity_time = time.time()  # 更新活动时间戳
                    data = conn.recv(1024)
                    if not data:
                        print("Connection closed by client.")
                        print("resource release")
                        set_motor([motor1_in1, motor1_in2, motor1_ena], 'stop', 0)
                        set_motor([motor2_in1, motor2_in2, motor2_ena], 'stop', 0)
                        
                        # 清理资源
                        motor1_ena.deinit()
                        motor2_ena.deinit()
                        motor1_in1.value(0)
                        motor1_in2.value(0)
                        motor2_in1.value(0)
                        motor2_in2.value(0)
                        conn.close()
                        break
                    
                    partial_data = data.decode().strip()
                    print("Re:", repr(partial_data))
                    
                    last_activity_time = time.time()  # 更新活动时间戳
                    
                    while b'\n' in partial_data:  # 检查部分数据是否包含分隔符
                        message, partial_data = partial_data.split(b'\n', 1)  # 按分隔符分割消息
                        command = message.decode().strip()
                    
                        if "heartbeat" in command:
                            pass
                        elif command == "1F":
                            print("1F")
                            set_motor([motor1_in1, motor1_in2, motor1_ena], 'forward', 100)
                        elif command == "1A":
                            print("1A")
                            set_motor([motor1_in1, motor1_in2, motor1_ena], 'retreat', 100)
                        elif command == "-1F" or command == "-1A":
                            print("1FA-stop")
                            set_motor([motor1_in1, motor1_in2, motor1_ena], 'stop', 0)
                            # 清理资源
                            motor1_ena.deinit()
                            motor1_in1.value(0)
                            motor1_in2.value(0)
                        elif command == "2F":
                            print("2F")
                            set_motor([motor2_in1, motor2_in2, motor2_ena], 'forward', 100)
                        elif command == "2A":
                            print("2A")
                            set_motor([motor2_in1, motor2_in2, motor2_ena], 'retreat', 100)
                        elif command == "-2F" or command == "-2A":
                            print("2FA-stop")
                            set_motor([motor2_in1, motor2_in2, motor2_ena], 'retreat', 0)
                            # 清理资源
                            motor2_ena.deinit()
                            motor2_in1.value(0)
                            motor2_in2.value(0)
                        else:
                            print("resource release")
                            set_motor([motor1_in1, motor1_in2, motor1_ena], 'stop', 0)
                            set_motor([motor2_in1, motor2_in2, motor2_ena], 'stop', 0)
                        
                            # 清理资源
                            motor1_ena.deinit()
                            motor2_ena.deinit()
                            motor1_in1.value(0)
                            motor1_in2.value(0)
                            motor2_in1.value(0)
                            motor2_in2.value(0)
                        print("Send a message to customer service")
                        response = "OK&{}".format(message.decode())
                        conn.send(response.encode())
                        last_activity_time = time.time()  # 更新活动时间戳
                    
                except OSError as e:
                    if e.args[0] == 11:  # EAGAIN 错误
                        pass  # 没有数据可供接收，继续等待
                
                # 检查是否超过阈值没有收到数据，超时则关闭连接
                if time.time() - last_activity_time > 4:  # 假设设置超时时间为 60 秒
                    print("Connection timed out. Closing connection.")
                    print("resource release")
                    set_motor([motor1_in1, motor1_in2, motor1_ena], 'stop', 0)
                    set_motor([motor2_in1, motor2_in2, motor2_ena], 'stop', 0)
                        
                    # 清理资源
                    motor1_ena.deinit()
                    motor2_ena.deinit()
                    motor1_in1.value(0)
                    motor1_in2.value(0)
                    motor2_in1.value(0)
                    motor2_in2.value(0)
                    conn.close()
                    break

        except OSError as e:
            pass  # 没有连接或接收数据时，继续等待

        await asyncio.sleep(0.1)  # 添加一个短暂的等待，避免无限循环阻塞

    server_socket.close()


# 创建一个事件循环，并在其中运行 update_display() 协程
loop = asyncio.get_event_loop()
if not isAP:
    loop.create_task(connect_wifi())
loop.create_task(start_server())
loop.run_forever()

