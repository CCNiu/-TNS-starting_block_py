import _thread
import time

# 定義第一個核心的無限迴圈
def core0_loop():
    while True:
        print("Core 0 is running")
        time.sleep(1)

# 定義第二個核心的無限迴圈
def core1_loop():
    while True:
        print("Core 1 is running")
        time.sleep(1)

# 在第二個核心上啟動無限迴圈
_thread.start_new_thread(core1_loop, ())

# 在第一個核心上執行無限迴圈
core0_loop()