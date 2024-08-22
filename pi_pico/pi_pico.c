#include "pico/stdlib.h"
#include "hardware/i2c.h"
#include "hardware/uart.h"
#include "pico/multicore.h"
#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>

// Constants
#define I2C_PORT i2c0

#define PICO_I2C_SDA_PIN 0
#define PICO_I2C_SCL_PIN 1

#define UART_ID uart1
#define BAUD_RATE 115200

#define UART_TX_PIN 4
#define UART_RX_PIN 5

#define ADXL345_ADDRESS 0x53
#define ADXL345_POWER_CTL 0x2D
#define ADXL345_DATA_FORMAT 0x31
#define ADXL345_DATAX0 0x32
#define ADXL345_FREQ 0x2C

char buffer[50]; // 定義一個足夠大的字元陣列來存儲格式化字串
char cmd_value[3];
char cmd_type;

// Function prototypes
void init_adxl345();
void my_i2c_init();
int16_t read_x_accel();
float mean(float* data, int length);
float pstdev(float* data, int length, float mean_val);
void read_uart_command(char* cmd_type, char* cmd_value);
void send_uart_message(const char* message);


// 初始化 I2C 接口
void my_i2c_init() {
    i2c_init(I2C_PORT, 100 * 1000);  // 初始化 I2C，設置速度為 100kHz
    gpio_set_function(PICO_I2C_SDA_PIN, GPIO_FUNC_I2C); // 設置 GP4 為 I2C 功能（SDA）
    gpio_set_function(PICO_I2C_SCL_PIN, GPIO_FUNC_I2C); // 設置 GP5 為 I2C 功能（SCL）
    gpio_pull_up(PICO_I2C_SDA_PIN);
    gpio_pull_up(PICO_I2C_SCL_PIN);
}

// 初始化 ADXL345
void init_adxl345() {
    
    uint8_t data_ADXL[2];
    data_ADXL[0] = ADXL345_POWER_CTL;
    data_ADXL[1] = 0x08;
    i2c_write_blocking(i2c0, ADXL345_ADDRESS, data_ADXL, 2, false);

    // 設定數據格式 (全解析度，16G 範圍)
    data_ADXL[0] = ADXL345_DATA_FORMAT;
    data_ADXL[1] = 0x0B;
    i2c_write_blocking(i2c0, ADXL345_ADDRESS, data_ADXL, 2, false);

    // 設定資料傳輸速率
    data_ADXL[0] = ADXL345_FREQ;
    data_ADXL[1] = 0x0A; // 100Hz
    i2c_write_blocking(i2c0, ADXL345_ADDRESS, data_ADXL, 2, false);
} 

// 讀取 X 軸加速度數據
int16_t read_x_accel() {
    uint8_t reg = ADXL345_DATAX0;
    uint8_t buffer[2];

    // 讀取 X 軸數據（2 bytes）
    i2c_write_blocking(I2C_PORT, ADXL345_ADDRESS, &reg, 1, true);
    i2c_read_blocking(I2C_PORT, ADXL345_ADDRESS, buffer, 2, false);

    // 將兩個 bytes 組合成一個 16-bit 數據
    int16_t x = (buffer[1] << 8) | buffer[0];

    return x;
}

float mean(float* data, int length) {
    if (data == NULL || length <= 0) {
        return 0.0f;  // 可以根據需求改為其他錯誤處理方式
    }
    float sum = 0.0f;
    for (int i = 0; i < length; i++) {
        sum += data[i];
    }
    return sum / length;
}

float pstdev(float* data, int length, float mean_val) {
    float sum = 0.0f;
    for (int i = 0; i < length; i++) {
        sum += pow(data[i] - mean_val, 2);
    }
    return sqrt(sum / length);
}

void read_uart_command(char* cmd_type, char* cmd_value) {
    if (uart_is_readable(UART_ID)) {
        char command[10] = {'0', '0', '0', '0', '0', '0', '0', '0', '0', '0'};
        
        uart_read_blocking(UART_ID, command, 10);  // 读取10个字节的数据

        // 将接收到的命令拆分并存储到对应变量中
        while (1)
        {
            if (command[0] == 'S' || command[0] == 'O' || command[0] == 'T' ||
                command[0] == 'D' || command[0] == 'R' || command[0] == 'C'){
                //*cmd_type = command[0];
                memcpy(cmd_type, &command[0], 1);
                sleep_ms(1);
                memcpy(cmd_value, &command[1], 2);
                cmd_value[2] = '\0';  // 确保字符串结束符
                break;
            }
            else{
                for(int i = 0;i<9;i++){
                    command[i]=command[i+1];
                }
                command[9] = '\0';  // 将最后一位设为 '\0' 或继续填充其他数据
            }
        
        }
        
          // 将后面的9个字符拷贝到cmd_value
        cmd_value[9] = '\0';  // 确保字符串结束符
    }
}

void send_uart_message(const char* message) {
    uart_puts(uart1, message);
    sleep_us(100);
    uart_puts(uart1, "\n");
}

int main() {
    uart_init(UART_ID, BAUD_RATE); //初始化UART

    gpio_set_function(UART_TX_PIN, GPIO_FUNC_UART);
    gpio_set_function(UART_RX_PIN, GPIO_FUNC_UART);

    stdio_init_all();
    my_i2c_init();  // 使用自定義的初始化函數
    init_adxl345();

    while (1) {

        //int16_t x_accel = read_x_accel();
        //sprintf(buffer, "X Acceleration: %d\n", x_accel);
        //uart_puts(UART_ID, buffer); // 發送格式化後的字串
        if (uart_is_readable(uart1)) {
            read_uart_command(&cmd_type, cmd_value);
            
            // 將 cmd_type 作為字串發送
            char cmd_type_str[2] = {cmd_type, '\0'};
            send_uart_message(cmd_type_str);
            send_uart_message(cmd_value);

            // 使用 strcmp 來比較字串
            if (cmd_type == 'S' && strcmp(cmd_value, "00") == 0) {
                send_uart_message("check S00");
            }
        }
    }
    return 0;
}