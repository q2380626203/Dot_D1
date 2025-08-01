import sys
import time
import wiringpi
from wiringpi import GPIO
import Dot_D1_config as cof

Pin_1 = 13                                    # 遥控器按键号对应开发板IO引脚号位
Pin_2 = 15                            
Pin_3 = 16                          
Pin_4 = 18                           
Pin_5 = 24                           
Pin_7 = 26                           
Pin_9 = 27                           

wiringpi.wiringPiSetup()                      # 初始化一下引脚
wiringpi.pinMode(Pin_1,GPIO.INPUT)            # 设置引脚输入模式
wiringpi.pinMode(Pin_2,GPIO.INPUT)  
wiringpi.pinMode(Pin_3,GPIO.INPUT)  
wiringpi.pinMode(Pin_4,GPIO.INPUT)  
wiringpi.pinMode(Pin_5,GPIO.INPUT)  
wiringpi.pinMode(Pin_7,GPIO.INPUT)  
wiringpi.pinMode(Pin_9,GPIO.INPUT) 

set_mode = 0                                    # 模式设置标志位，实现按下松开才算一次调整
center_subtle = 0.001                           # 重心补偿分量
run_speed = 0.2                                 # 行走目标速度

while True:

    Pin_1_state = wiringpi.digitalRead(Pin_1)
    Pin_2_state = wiringpi.digitalRead(Pin_2)
    Pin_3_state = wiringpi.digitalRead(Pin_3)
    Pin_4_state = wiringpi.digitalRead(Pin_4)
    Pin_5_state = wiringpi.digitalRead(Pin_5)
    Pin_7_state = wiringpi.digitalRead(Pin_7)
    Pin_9_state = wiringpi.digitalRead(Pin_9)

    # 微调模式
    if Pin_5_state == 1 :
        set_mode += 1
    # 遥控模式
    else:
        if Pin_1_state == 1:    # 前进 
            cof.commands[0] = run_speed
        elif Pin_2_state == 1:  # 后退
            cof.commands[0] = -run_speed
        elif Pin_3_state == 1:  # 左移
            cof.commands[1] = run_speed
        elif Pin_4_state == 1:  # 右移
            cof.commands[1] = -run_speed
        elif Pin_7_state == 1:  # 左旋转 逆时针
            cof.commands[2] = -(2*run_speed)
        elif Pin_9_state == 1:  # 右旋转 顺时针
            cof.commands[2] = (2*run_speed)
        else:
            cof.commands[0] = 0.0
            cof.commands[1] = 0.0
            cof.commands[2] = 0.0

        if set_mode > 0 and set_mode < 20: # 按住1秒以内微调增加(对应IMU0点应该是往后仰调整)
            cof.center_x += center_subtle
            set_mode = 0
        elif set_mode > 20:                # 按住1秒以内微调减小(对应IMU0点应该是往前倾斜调整)
            cof.center_x -= center_subtle
            set_mode = 0
    
    time.sleep(0.05)
    print('重心前后微调,行走xyz=',cof.center_x,cof.commands[0],cof.commands[1],cof.commands[2])
