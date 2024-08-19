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
    float sum = 0;
    for (int i = 0; i < length; i++) {
        sum += data[i];
    }
    return sum / length;
}

float pstdev(float* data, int length, float mean_val) {
    float sum = 0;
    for (int i = 0; i < length; i++) {
        sum += pow(data[i] - mean_val, 2);
    }
    return sqrt(sum / length);
}

void read_uart_command(char* cmd_type, char* cmd_value) {
    if (uart_is_readable(uart1)) {
        char command[4];
        uart_read_blocking(uart1, command, 3);
        command[3] = '\0';
        *cmd_type = command[0];
        strncpy(cmd_value, command + 1, 2);
        cmd_value[2] = '\0';
    }
}

void send_uart_message(const char* message) {
    uart_puts(uart0, message);
    uart_puts(uart0, "\n");
}

int main() {

    uart_init(UART_ID, BAUD_RATE); //初始化UART

    gpio_set_function(UART_TX_PIN, GPIO_FUNC_UART);
    gpio_set_function(UART_RX_PIN, GPIO_FUNC_UART);

    stdio_init_all();
    my_i2c_init();  // 使用自定義的初始化函數
    init_adxl345();

    while (1) {
        int16_t x_accel = read_x_accel();
        sprintf(buffer, "X Acceleration: %d\n", x_accel);
        uart_puts(UART_ID, buffer); // 發送格式化後的字串
        sleep_ms(50);
    }

    return 0;
}