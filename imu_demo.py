#!/usr/bin/python3
# -*- coding: UTF-8 -*-  


import time
import serial
import math 


read_imu = [0xff,0xaa,0x03,0X0c,0X0]
ser = serial.Serial("/dev/ttyUSB0",230400,timeout=0.001)  # 230400

#*******************************************************************
# 串口总线收发
# output_data 要下发的数据指令
# return state:0数据正常接收 1无数据反馈或超时,com_input:接收的数据
#*******************************************************************
def imu_com_out(ser):


    ser.flushInput()                
    ser.write(read_imu)             
    time_s = time.time()
    while True:
        count = ser.inWaiting()
        if count >= 22:
            break
        time.sleep(0.001)         
        #print('count------------------------=',count)
    print('imu_tim=',time.time() - time_s)

    com_input = ser.read(count) 
    if count == 22 and com_input[0]==0x55 and com_input[1]==0x52:

        Wx = (com_input[3]<<8 | com_input[2])/32768 * 2000
        if Wx >= 2000:
            Wx -= 2 * 2000
        Wy = (com_input[5]<<8 | com_input[4])/32768 * 2000
        if Wy >= 2000:
            Wy -= 2 * 2000
        Wz = (com_input[7]<<8 | com_input[6])/32768 * 2000
        if Wz >= 2000:
            Wz -= 2 * 2000

        Wx = math.radians(Wx)  
        Wy = math.radians(Wy)
        Wz = math.radians(Wz)
        #print('角弧速度1X、Y、z=',round(Wx,4),round(Wy,4),round(Wz,4))


        #解析 角度 数据部分  com_input[11] == 0X55 and com_input[12] == 0X53:
        Rx = (com_input[14]<<8 | com_input[13])/32768 *180
        if Rx >= 180:
            Rx -= 2 * 180
        Ry = (com_input[16]<<8 | com_input[15])/32768 *180
        if Ry >= 180:
            Ry -= 2 * 180
        Rz = (com_input[18]<<8 | com_input[17])/32768 *180
        if Rz >= 180:
            Rz -= 2 * 180

        Rx = math.radians(Rx)  
        Ry = math.radians(Ry)
        Rz = math.radians(Rz)
        print('角弧度1X、Y、z=',round(Rx,4),round(Ry,4),round(Rz,4))
        return 0

    else:
        print('xxxxxxxxxxxIMU接受数据格式错误xxxxxxxxxxxxx')
        
        for i in range(0,count): 
            print(hex(com_input[i]))   
        
        return 1

def main():  

    while True:
        if imu_com_out(ser) ==1 :
            break
            pass


if __name__ == "__main__":  
    main()



