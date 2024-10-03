from machine import Pin, I2C
import time
import ustruct
import math
 
# Constants
ADXL345_ADDRESS = 0x53 # address for accelerometer 
ADXL345_POWER_CTL = 0x2D # address for power control
ADXL345_DATA_FORMAT = 0x31 # configure data format
ADXL345_DATAX0 = 0x32 # where the x-axis data starts

#offsets
ADXL345_OFSX = 0x1E
ADXL345_OFSY = 0x1F
ADXL345_OFSZ = 0x20
# Initialize I2C
i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)
 
# Initialize ADXL345
def init_adxl345():
    i2c.writeto_mem(ADXL345_ADDRESS, ADXL345_POWER_CTL, bytearray([0x08]))  # Set bit 3 to 1 to enable measurement mode
    i2c.writeto_mem(ADXL345_ADDRESS, ADXL345_DATA_FORMAT, bytearray([0x0B]))  # Set data format to full resolution, +/- 16g
 
# Read acceleration data
def read_accel_data():
    data = i2c.readfrom_mem(ADXL345_ADDRESS, ADXL345_DATAX0, 6)# read 6 bytes from ADXL345_DATAX0 of ADXL345_ADDRESS
    x, y, z = ustruct.unpack('<hhh', data)#Unpack from the data according to the format string fmt. The return value is a tuple of the unpacked values.
    return x, y, z

# Calculate the magnitude of acceleration
def calc_accel_magnitude(x, y, z):
    return math.sqrt(x**2 + y**2 + z**2)

# Main loop
init_adxl345()
ADXL345_OFSX,ADXL345_OFSY,ADXL345_OFSZ = read_accel_data()
print("offset check")
while True:
    x, y, z = read_accel_data()
    x = x - ADXL345_OFSX
    y = y - ADXL345_OFSY
    z = z - ADXL345_OFSZ
    magnitude = calc_accel_magnitude(x, y, z)
    print('--------------------')
    print(x, y, z)
    print("X: {}, Y: {}, Z: {}, Magnitude:{:.2f} ".format(x*0.0039, y*0.0039, z*0.0039 , magnitude))
    time.sleep(0.01)
    
    
# if you do get OSError: [Errno 5] EIO, try unplug and plug
# if you do set different resolution 0.0039 may not be the constant (check data sheet)
