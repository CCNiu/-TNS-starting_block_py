from machine import Pin, I2C
import time
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
ADXL345_OFSY = 0x1F
ADXL345_OFSZ = 0x20
# Initialize I2C
i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)

#datalist
XY_list = [ [0] for N in range(2000)]
XY_new_list=[[0] for N in range(2000)]

#
XY = 0
N=0
# Initialize ADXL345
def init_adxl345():
    i2c.writeto_mem(ADXL345_ADDRESS, ADXL345_POWER_CTL, bytearray([0x08]))  # Set bit 3 to 1 to enable measurement mode
    i2c.writeto_mem(ADXL345_ADDRESS, ADXL345_DATA_FORMAT, bytearray([0x0B]))  # Set data format to full resolution, +/- 16g

# Read acceleration data
def read_accel_data():
    data = i2c.readfrom_mem(ADXL345_ADDRESS, ADXL345_DATAX0, 6)# read 6 bytes from ADXL345_DATAX0 of ADXL345_ADDRESS
    x, y, z = ustruct.unpack('<hhh', data)#Unpack from the data according to the format string fmt. The return value is a tuple of the unpacked values.
    return x, y, z

# 0509_2axis accer 
def two_axis_accer(x,y):
    return math.sqrt(x**2 + y**2)

def mean(data):
    if iter(data) is data:
        data = list(data)
    return sum(data)/len(data)

def pvariance(data, mu=None):
    if iter(data) is data:
        data = list(data)
    return _ss(data, mu)/len(data)

def _ss(data, c=None):
    if c is None:
        c = mean(data)
    total = total2 = 0
    for x in data:
        total += (x - c)**2
        total2 += (x - c) 
    total -= total2**2/len(data)
    return total

def pstdev(data, mu=None):
    return math.sqrt(pvariance(data, mu))

# Main loop
init_adxl345()
ADXL345_OFSX,ADXL345_OFSY,ADXL345_OFSZ = read_accel_data()
print("offset check")
while True:
    x, y, z = read_accel_data()
    x = x - ADXL345_OFSX
    y = y - ADXL345_OFSY
    z = z - ADXL345_OFSZ
    XY = int(round(two_axis_accer(x,y),2)*100)#備用計畫 只用一軸
    print(x, y, z)
    if (N > 1999):
        break#FOR TEST
        N=0
        XY_list[N]=XY
        time.sleep(0.0001) #delay 尚未調整
        #break#FOR TEST
    else:#0~19
        XY_list[N]=XY
        time.sleep(0.0001) #delay 尚未調整
    N+=1
    #if訊號進來
    record_ptr=N
    
#重新建立list 接收起跑訊號為第1000點(10)
record_ptr=1000

XY_new_list=XY_list[record_ptr-500:record_ptr]+XY_list[record_ptr:2000]+XY_list[0:record_ptr-500]

print("排序前:",XY_list)
print("排序後:",XY_new_list)
XY_list.clear()
#print(XY_list)#check XY_list clear
#計算XY起跑前-200~-500的標準差
XY_ready_std_list=[[0] for i in range(300)]#3--300
XY_ready_std_list = XY_new_list[0:300]#3--300

#計算標準差，但不確定micropython支不支援statistics
print(XY_ready_std_list)
XY_ready_list_dev=round(pstdev(XY_ready_std_list),2)
XY_ready_list_mean=round(mean(XY_ready_std_list),2)
XY_ready_list_three_dev_mean=round(XY_ready_list_mean+3*XY_ready_list_dev,2)
print("平均數:",XY_ready_list_mean)
print("標準差:",XY_ready_list_dev)
print("3倍標準差+平均:",XY_ready_list_three_dev_mean)

#跟300後的比大小
for i in range(0,2000):
    if XY_new_list[i] > XY_ready_list_three_dev_mean:
        print("好大喔",XY_new_list[i],i)
        #若i<起跑訊號後200毫秒，則犯規
        break

