import time
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
x=1
y=2
z=3
running_time=500
N=0
#multiple_data(xyz)
data_list = [ [0] * 3 for N in range(10)]
while(True):
    #if 訊號尚未進來
    if (N >= 10):
        N=0
        data_list[N]=[[x],[y],[z]]
        time.sleep(1) #delay 尚未調整
        break
    else:
        data_list[N]=[[x],[y],[z]]
        # data_list[N]=[x,y,z]
        time.sleep(1) #delay 尚未調整
    #if訊號進來
    #record_ptr=N
    #
    print(N)
    print(data_list)
    N+=1
    x+=1
    y+=1
    z+=1
#one_direction_data(x)







# plt.plot(N, data_list[1], color='b')
# plt.xlabel('SEASON') # 設定x軸標題
# plt.xticks(N, rotation='vertical') # 設定x軸label以及垂直顯示
# plt.title('LeBron James') # 設定圖表標題
# plt.show()