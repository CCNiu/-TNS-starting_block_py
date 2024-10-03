from machine import UART, Pin
import machine
import utime
i = 0
uart = machine.UART(1, baudrate=115200,parity=None,tx=Pin(4),rx=Pin(5))  # UART0，波特率設置為9600

while True:
    if uart.any():
        #data = uart.read().decode('utf-8')
        data = uart.read().decode('utf-8')

        utime.sleep(0.1)
        print(data)

    else:
        print("nothing")
        uart.write(str(i).encode('utf-8') + b'\r\n')
        utime.sleep(0.01)
        i+=1
#     uart.write("Data received\n")
#     print(data)   
    utime.sleep(0.1)

