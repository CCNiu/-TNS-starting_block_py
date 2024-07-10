# from machine import UART, Pin
# import time
# 
# # 初始化UART0，波特率9600
# #uart0 = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))
# #machine.UART(id,baudrate=115200,bits=8,parity=None,stop=1,tx=None,rx=None)
# uart1=machine.UART(1,baudrate=9600,tx=Pin(4),rx=Pin(5))
# def setup():
#     print("UART Communication Initialized on Pi Pico")
# 
# def loop():
#     # 檢查是否有來自UART的數據
#     if uart1.any():
#         # 讀取數據
#         received_data = uart1.read().decode('utf-8')
#         
#         # 顯示接收到的數據
#         print("Received: ", received_data)
#         
#         # 回應數據
#         #uart.write("Data received: " + received_data + "\n")
#     else:
#         print("nothing")
#     time.sleep(0.1)
# 
# setup()
# while True:
#     loop
from machine import UART, Pin
import machine
import utime

uart = machine.UART(1, baudrate=9600,tx=Pin(4),rx=Pin(5))  # UART0，波特率設置為9600

while True:
    if uart.any():
        data = uart.read().decode('utf-8')
        print(data)
    else:
        print("nothing")
    utime.sleep(1)

