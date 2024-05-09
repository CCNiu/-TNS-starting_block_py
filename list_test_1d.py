import statistics
import time

#get_data
x=1
y=1
z=1
XY=0
g=0
running_time=500
N=0     #list計數器

data_list = [ [0] *3 for N in range(20)]
XY_list = [ [0] for N in range(20)]
XY_new_list=[[0] for N in range(20)]

while(True):
    #if 起跑訊號尚未進來
    #從accer_sensor收資料
    XY= (x**2 + y**2)#**0.5 #取兩軸的信號做平方平均數
    if (N > 19):
        break#FOR TEST
        N=0
        XY_list[N]=XY
        data_list[N]=[[x],[y],[z]]
        time.sleep(0.001) #delay 尚未調整
        break#FOR TEST
    else:#0~19
        XY_list[N]=XY
        data_list[N]=[[x],[y],[z]]
        time.sleep(0.001) #delay 尚未調整
    N+=1
    x+=1
    #if訊號進來
    record_ptr=N
    #for i in range(500,2000):
    #XY_list[N]=[XY]
    #data_list[N]=[[x],[y],[z]]
    #i+=1
    #break
    #print(N)
    

#重新建立list 接收起跑訊號為第1000點(10)
record_ptr=10
#122為第10位
XY_new_list=XY_list[record_ptr-5:record_ptr]+XY_list[record_ptr:20]+XY_list[0:record_ptr-5]
#37應為第0位
print("排序前:",XY_list)
print("排序後:",XY_new_list)

#計算XY起跑前-200~-500的標準差
XY_ready_std_list=[[0] for i in range(3)]#3--300
XY_ready_std_list = XY_new_list[0:3]#3--300

#計算標準差，但不確定micropython支不支援statistics
print(XY_ready_std_list)
XY_ready_list_dev=statistics.pstdev(XY_ready_std_list)
XY_ready_list_mean=statistics.mean(XY_ready_std_list)
XY_ready_list_three_dev_mean=XY_ready_list_mean+3*XY_ready_list_dev
print("平均數:",XY_ready_list_mean)
print("標準差:",XY_ready_list_dev)
print("3倍標準差+平均:",XY_ready_list_three_dev_mean)

#跟300後的比大小
for i in range(0,20):
    if XY_new_list[i] > XY_ready_list_three_dev_mean:
        print("好大喔",i)
        break