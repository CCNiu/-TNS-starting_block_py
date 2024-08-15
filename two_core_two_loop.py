from machine import Pin, I2C, UART
import time
import utime
import ustruct
import math
import gc
import _thread
from rp2 import PIO, StateMachine, asm_pio

gc.enable()

UID = '00'

# Constants
ADXL345_ADDRESS = 0x53
ADXL345_POWER_CTL = 0x2D
ADXL345_DATA_FORMAT = 0x31
ADXL345_DATAX0 = 0x32
ADXL345_FREQ = 0x2C

# Initialize I2C and UART
i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=100000)
uart = machine.UART(1, baudrate=115200, parity=None, tx=Pin(4), rx=Pin(5))
led = Pin(25, Pin.OUT)

# Data lists
X_list = [0] * 2000
X_new_list = [0] * 2000
record_ptr = 0
N = 0
counter = 0
R_time = 99999
s_switch = 0 #off
mode = ' '
status = False
X_realtime = 0
ADXL345_OFSX = 0

def init_adxl345():
    """Initialize the ADXL345 accelerometer."""
    i2c.writeto_mem(ADXL345_ADDRESS, ADXL345_POWER_CTL, bytearray([0x08]))
    i2c.writeto_mem(ADXL345_ADDRESS, ADXL345_DATA_FORMAT, bytearray([0x08]))
    i2c.writeto_mem(ADXL345_ADDRESS, ADXL345_FREQ, bytearray([0x0E]))

def read_accel_data():
    """Read acceleration data from ADXL345."""
    data = i2c.readfrom_mem(ADXL345_ADDRESS, ADXL345_DATAX0, 6)
    x, y, z = ustruct.unpack('<hhh', data)
    return x

def mean(data):
    return sum(data) / len(data)

def pvariance(data, mu=None):
    if mu is None:
        mu = mean(data)
    return sum((x - mu) ** 2 for x in data) / len(data)

def pstdev(data, mu=None):
    return math.sqrt(pvariance(data, mu))

def read_uart_command():
    if uart.any():
        #print('OK')
        command = uart.read().decode('utf-8')
        #print(command)
        if len(command) >= 3:
            cmd_type = command[0]
            cmd_value = command[1:3]
            return cmd_type, cmd_value
    return None, None

def send_uart_message(message):
    uart.write( UID + " " )
    uart.write( message.encode('utf-8') + b'\n')
    utime.sleep(0.01)

# Initialize ADXL345
init_adxl345()
time.sleep(0.0001)

# 在全局變量中初始化偏移量
ADXL345_OFSX = 0
def core0_task():
    global R_time, mode, X_realtime ,record_ptr,ADXL345_OFSX
    while(True):
        if uart.any() :
            cmd_type, cmd_value = read_uart_command()
            print(cmd_type, cmd_value)
            time.sleep(0.1)

            if cmd_value != UID and cmd_value != '00':
                continue

            if cmd_type == 'O':  # open
                ADXL345_OFSX = read_accel_data()
                print("11",ADXL345_OFSX)
                print(str(ADXL345_OFSX))
                send_uart_message(str(ADXL345_OFSX))
                time.sleep(0.01)
                mode = 'O'

            elif cmd_type == 'S':  # start
                mode = 'S'
                record_ptr = N
                counter = 0
                # send_uart_message("set ptr=0")
                time.sleep(0.01)

            elif cmd_type == 'R':  # react time
                mode = 'R'
                send_uart_message("R")
                if (R_time == 99999 ):
                    send_uart_message( " NULL " )#no react time data
                else:
                    send_uart_message("Reaction time: " + str(R_time) + " second")

            elif cmd_type == 'D':  # data
                mode = 'D'
                if ( X_new_list[1:100] == 0 ):
                    send_uart_message("NULL") #no data list
                else:
                    my_list = ','.join(str(x) for x in X_new_list)
                    time.sleep(0.01)
                    send_uart_message(my_list)
                send_uart_message("D")

            elif cmd_type == 'T':  # test
                mode = 'T'
                send_uart_message("testing")
                #print("X_realtime2 =",X_realtime)
                send_uart_message(str(X_realtime))
                time.sleep(0.01)
                
            elif cmd_type == 'C':
                mode = 'C'
                send_uart_message("C")
                utime.sleep(0.01)

            else:
                send_uart_message("invalid instruction")

# 核心 1 上執行的加速度計測量和計算函數
def core1_task():
    global N, counter, X_list, X_new_list, record_ptr, R_time, ADXL345_OFSX, mode, X_realtime, status
    while True:
        if mode != 'T' and mode != 'C' and mode != 'ST' : # O S R D
            #get accel
            if mode =='O' :
                if status == False:
                    ADXL345_OFSX = read_accel_data()
                    status = True
                    #print("offset check", ADXL345_OFSX)
                    
                s_switch = 1
                
            elif mode=='S' and s_switch ==1 :
                if counter> 999 :
                    X_new_list = X_list[record_ptr - 500:record_ptr] + X_list[record_ptr:2000] + X_list[0:record_ptr - 500]
                    #print("排序前:", X_list)
                    #print("排序後:", X_new_list)
                    X_list.clear()

                    X_ready_std_list = X_new_list[0:300]

                    X_ready_list_dev = round(pstdev(X_ready_std_list), 2)
                    X_ready_list_mean = round(mean(X_ready_std_list), 2)
                    X_ready_list_three_dev_mean = round(X_ready_list_mean + 3 * X_ready_list_dev, 2)
                    print("平均數:", X_ready_list_mean)
                    print("標準差:", X_ready_list_dev)
                    print("3倍標準差+平均:", X_ready_list_three_dev_mean)

                    for i in range(300, 2000 - 4):
                        if all(x > X_ready_list_three_dev_mean for x in X_new_list[i:i + 4]):
                            R_time = (i - 500) / 1000.0
                            print("數值:", X_new_list[i], "第", R_time, "second")
                            send_uart_message("Reaction time: " + str(R_time) + " second")
                            break
                    mode = 'ST'
                    continue
                else:
                    counter += 1
            print(mode,N)
            x= read_accel_data()
            X = abs(x - ADXL345_OFSX)
            if N > 1999:
                N = 0
            X_list[N] = X
            time.sleep(0.001)
            N += 1
            
        elif mode == 'C': #C
            #reset
            if status == True:
                status = False
            X_list = [0] * 2000
            X_new_list = [0] * 2000
            init_adxl345()
        elif mode == 'T':
            X_realtime = read_accel_data()
            #print("X_realtime1 =",X_realtime)
            time.sleep(0.0001)
            mode = 'ST'
        else:
            continue

# 啟動第二個核心
_thread.start_new_thread(core1_task, ())

# 核心 0 上執行的 UART 指令處理函數
core0_task()

