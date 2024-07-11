from machine import Pin, I2C ,UART
import time
import utime
import ustruct
import math
import gc
gc.enable()
# Constants
ADXL345_ADDRESS = 0x53 # address for accelerometer 
ADXL345_POWER_CTL = 0x2D # address for power control
ADXL345_DATA_FORMAT = 0x31 # configure data format
ADXL345_DATAX0 = 0x32 # where the x-axis data starts
ADXL345_FREQ = 0x2C #the register of baud rate
#offsets
ADXL345_OFSX = 0x1E
# Initialize I2C
i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=100000)
uart = machine.UART(1, baudrate=115200,parity=None,tx=Pin(4),rx=Pin(5))  # UART0，波特率設置為9600
led = Pin(25, Pin.OUT)  # 內建 LED 連接到 GPIO 25
#datalist
X_list = [0] * 2000
X_new_list = [0] * 2000

N=0
# Initialize ADXL345
def init_adxl345():
    i2c.writeto_mem(ADXL345_ADDRESS, ADXL345_POWER_CTL, bytearray([0x08]))  # Set bit 3 to 1 to enable measurement mode
    i2c.writeto_mem(ADXL345_ADDRESS, ADXL345_DATA_FORMAT, bytearray([0x08]))  # Set data format to full resolution, +/- 16g
    i2c.writeto_mem(ADXL345_ADDRESS, ADXL345_FREQ , bytearray([0x0E]))
# Read acceleration data
def read_accel_data():
    data = i2c.readfrom_mem(ADXL345_ADDRESS, ADXL345_DATAX0, 6)# read 6 bytes from ADXL345_DATAX0 of ADXL345_ADDRESS
    x, y, z = ustruct.unpack('<hhh', data)#Unpack from the data according to the format string fmt. The return value is a tuple of the unpacked values.
    return x, y, z
init_adxl345()
time.sleep(0.0001)
def mean(data):
    if iter(data) is data:
        data = list(data)
    return sum(data)/len(data)

def pvariance(data, mu=None):
    if mu is None:
        mu = mean(data)
    return sum((x - mu) ** 2 for x in data) / len(data)

def pstdev(data, mu=None):
    return math.sqrt(pvariance(data, mu))

# Main loop

ADXL345_OFSX,ADXL345_OFSY,ADXL345_OFSZ = read_accel_data()
print("offset check",ADXL345_OFSX)

while True:
    x, y, z = read_accel_data()
    X = abs(x-ADXL345_OFSX)
    #print(X)
    if (N > 1999):
        break#FOR TEST
        N=0
        X_list[N]=X
        time.sleep(0.0001) #delay 尚未調整
        #break#FOR TEST
    else:#0~19
        X_list[N]=X
        time.sleep(0.0001) #delay 尚未調整
    N+=1
    #if訊號進來
    record_ptr=N
    
#重新建立list 接收起跑訊號為第1000點(10)
record_ptr=1000

X_new_list=X_list[record_ptr-500:record_ptr]+X_list[record_ptr:2000]+X_list[0:record_ptr-500]

print("排序前:",X_list)
print("排序後:",X_new_list)
X_list.clear()
#計算XY起跑前-200~-500的標準差
X_ready_std_list=[[0] for i in range(300)]#3--300
X_ready_std_list = X_new_list[0:300]#3--300
gc.collect()
#計算標準差，但不確定micropython支不支援statistics
X_ready_list_dev=round(pstdev(X_ready_std_list),2)
X_ready_list_mean=round(mean(X_ready_std_list),2)
X_ready_list_three_dev_mean=round(X_ready_list_mean+3*X_ready_list_dev,2)
print("平均數:",X_ready_list_mean)
print("標準差:",X_ready_list_dev)
print("3倍標準差+平均:",X_ready_list_three_dev_mean)

# 跟300後的比大小
for i in range(300, 2000 - 4):  # 確保切片不超出範圍
    if all(x > X_ready_list_three_dev_mean for x in X_new_list[i:i+4]):
        R_time = i / 1000.0  # 計算反應時間，這裡使用浮點數除法
        print("數值:",X_new_list[i],"第", R_time, "second")
        
        # 將資料轉換為字串並傳輸到 UART
        uart.write("Reaction time: ".encode('utf-8'))
        utime.sleep(0.01)
        uart.write(str(R_time).encode('utf-8'))
        utime.sleep(0.01)
        uart.write(" second\n".encode('utf-8'))
        utime.sleep(0.01)
        # 若i<起跑訊號後200毫秒，則犯規
        break
uart.write(("str").encode('utf-8')+ b'\n')
utime.sleep(0.01)
#

my_list = ','.join(str(x) for x in X_new_list)
time.sleep(0.01)
uart.write(my_list)
utime.sleep(0.01)

#
# for i in range(2000):
#     #uart.write("{:d}\n".format(X_new_list[i]).encode('utf-8'))
#     uart.write("{:d}\n".format(188))
#     utime.sleep(0.01)
# uart.write(("end").encode('utf-8')+ b'\n')

