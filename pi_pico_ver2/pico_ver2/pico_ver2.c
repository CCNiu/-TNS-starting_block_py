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

#define PICO_I2C_SDA_PIN 8
#define PICO_I2C_SCL_PIN 9

#define UART_ID uart1
#define BAUD_RATE 115200

#define UART_TX_PIN 4
#define UART_RX_PIN 5

#define ADXL345_ADDRESS 0x53
#define ADXL345_POWER_CTL 0x2D
#define ADXL345_DATA_FORMAT 0x31
#define ADXL345_DATAX0 0x32
#define ADXL345_FREQ 0x2C

#define CALC_NUM 300
#define DETECT_PREV_NUM 500
#define DETECT_POST_NUM 1000
#define THREADSHOLD 100

char UID[3] = "00";

char buffer[50]; // 定義一個足夠大的字元陣列來存儲格式化字串
char cmd_value[3];
char cmd_type;

// Global variables
int Global_X_Prev_List[CALC_NUM + DETECT_PREV_NUM];
int Global_X_Post_List[DETECT_POST_NUM];
float Global_X_Realtime = 0;
char Global_Mode = 'Q';
float Global_Accel_Offset = 0;
float Global_RT = -1;

int Global_Prev_Prev_index = 0;
int Global_Prev_Post_index = 0;

float Global_Threshold = 0;
float Global_Mean_Value = 0;
int Global_Post_Index = 0;

// Function prototypes
void init_adxl345();
void my_i2c_init();
int16_t read_x_accel();
float mean(float* data, int length);
float pstdev(float* data, int length, float mean_val);
void read_uart_command(char* cmd_type, char* cmd_value);
void send_uart_message(const char* message);
void core0_task();
void core1_task();

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
        char command[8] = {0}; // Ensure all characters are initialized to '\0'
        int index = 0;
        
        while (uart_is_readable(UART_ID) && index < 8) {
            char c = uart_getc(UART_ID);
            // printf("%c, %d \n", c, index);
            if (c == '\n' || c == '\r') break; // End on newline
            command[index++] = c;  // Store character
            sleep_us(100);
        }
        
        command[index] = '\0'; // Null-terminate
        // printf(command);

        // Check the first character to determine the command type
        if (index >= 3 && (command[0] == 'S' || command[0] == 'O' || command[0] == 'T' ||
                            command[0] == 'D' || command[0] == 'R' || command[0] == 'C')) {
            *cmd_type = command[0];
            strncpy(cmd_value, &command[1], 2); // Copy the next two characters
            cmd_value[2] = '\0'; // Null-terminate
        }
    }
}

void send_uart_message(const char* message) {
    uart_puts(uart1, UID);
    uart_puts(uart1, message);
    sleep_us(100);
    uart_puts(uart1, "\n");
}

void send_accel_data(int* data, int length) {
    char buffer_D[5001];  // 為1000個四位整數+逗號+結束符保留足夠的空間
    int pos = 0;

    for (int i = 0; i < length; i++) {
        // 格式化整數，並加入逗號
        int written = snprintf(buffer_D + pos, sizeof(buffer_D) - pos, "%04d", data[i]);
        if (written < 0 || pos + written >= sizeof(buffer_D)) {
            break;  // 發生錯誤或者緩衝區不足時，停止
        }
        pos += written;

        // 除了最後一個數字之外，添加逗號
        if (i < length - 1 && pos < sizeof(buffer_D) - 1) {
            buffer_D[pos++] = ',';
        }
    }

    buffer_D[pos] = '\0';  // 確保字串以 null 結束

    send_uart_message(buffer_D);  // 傳送格式化的數據
}



int main() {
    // Initialize UART
    uart_init(UART_ID, BAUD_RATE); //初始化UART
    gpio_set_function(UART_TX_PIN, GPIO_FUNC_UART);
    gpio_set_function(UART_RX_PIN, GPIO_FUNC_UART);

    stdio_init_all();
    // Initialize I2C
    my_i2c_init();  // 使用自定義的初始化函數

    // Initialize ADXL345
    init_adxl345();

    while (1) {
        // Launch the second core task
        multicore_launch_core1(core1_task);

        // Run the core0 task
        core0_task();
    }
    return 0;
}

void core0_task() {
    char cmd_type, cmd_value[3];

    while (1) {
        if (uart_is_readable(uart1)) {
            read_uart_command(&cmd_type, cmd_value);
            printf("%c %s\n", cmd_type, cmd_value);
            if(strcmp(cmd_value, "00") == 0 || strcmp(cmd_value, UID) == 0){
                sleep_ms(1);
                if (cmd_type == 'O') {
                    Global_Mode = 'O';
                    send_uart_message("Offset set");
                    sleep_us(100);
                } else if (cmd_type == 'S') {
                    Global_Mode = 'S';
                    send_uart_message("Started");
                    sleep_us(100);
                } else if (cmd_type == 'R') {
                    if (Global_RT == -1) {
                        send_uart_message("NULL");
                    } else {
                        char buffer[32];
                        snprintf(buffer, 32, "Reaction time: %.2f seconds", Global_RT);
                        send_uart_message(buffer);
                    }
                } else if (cmd_type == 'T') {
                    Global_Mode = 'T';
                    send_uart_message("Testing");
                    sleep_us(100);
                } else if (cmd_type == 'C') {
                    Global_Mode = 'C';
                    send_uart_message("Reset");
                    sleep_us(100);
                } else if (cmd_type == 'D') {
                    Global_Mode = 'D';
                    send_uart_message("Data set");
                    sleep_us(100);
                    send_accel_data(Global_X_Post_List, DETECT_POST_NUM);
                    sleep_ms(10);
                } else {
                    send_uart_message("Invalid command");
                    sleep_us(100);
                }
            }
        }
    }
}

void core1_task() {
    int status = 0;
    int calc_prev_index = 0;
    int calc_post_index = 0;
    float sum_value = 0;

    int current_time, prev_time;
    current_time = time_us_32();
    prev_time = current_time - 1;

    while (1) {
        current_time = time_us_32();
        if ((current_time - prev_time) >= 1000) {
            prev_time = current_time;

            if (Global_Mode == 'C') {
                status = 0;
                Global_X_Realtime = 0;
                Global_Accel_Offset = 0;
                Global_RT = -1;
                Global_Prev_Prev_index = 0;
                Global_Prev_Post_index = 0;
                Global_Threshold = 0;
                Global_Mean_Value = 0;
                Global_Post_Index = 0;
            } else if (Global_Mode == 'T') {
                Global_X_Realtime = read_x_accel();
                printf("X_realtime = %.2f\n", Global_X_Realtime);
                Global_Mode = 'Q';
            } else if (Global_Mode == 'O' || Global_Mode == 'S') {
                float x_float = fabs(read_x_accel() - Global_Accel_Offset);
                int x = (int)x_float;
                if (Global_Mode == 'O') {
                    if (status == 0) {
                        Global_Accel_Offset = read_x_accel();
                        status = 1;
                        printf("Offset = %.2f\n", Global_Accel_Offset);
                        memset(Global_X_Prev_List, 0, sizeof(Global_X_Prev_List));
                        memset(Global_X_Post_List, 0, sizeof(Global_X_Post_List));
                    }

                    Global_X_Prev_List[Global_Prev_Post_index++] = x;
                    if (Global_Prev_Post_index >= CALC_NUM + DETECT_PREV_NUM) {
                        Global_Prev_Post_index = 0;
                    }
                } else {
                    Global_X_Post_List[Global_Post_Index++] = x;
                    if (Global_Post_Index >= DETECT_POST_NUM) {
                        Global_Mode = 'Q';
                    }
                }
            }
        }
    }
}