
#!/usr/bin/python3
# -*- coding: UTF-8 -*-  


import can  
import time
import struct

import Dot_D1_config as cof



def send_extended_frame_main(bus, arbitration_id , data , block_receive):  
    state = 0
    rx_data = [0 for i in range(8)] 
    message = can.Message(arbitration_id=arbitration_id,data=data,is_extended_id=True)  

    bus.send(message)  
 
    if block_receive == 1:
        time_s=time.time()
        while (1):  
            message_ou = bus.recv(0.1)  
            if message_ou is not None:  
                rx_data = message_ou.data
                break

            elif time.time() - time_s >1:
                print("仲裁号: %d 未受到回馈-error" % arbitration_id)
                state = 1
                break


    return(state,rx_data) 


def send_extended_frame_helper2(bus, arbitration_id , data , block_receive):  

    state = 0
    rx_data = [0 for i in range(8)] 
    message = can.Message(arbitration_id=arbitration_id,data=data,is_extended_id=True)  

    bus.send(message)  

    if block_receive == 1:
        time_s=time.time()
        while (1):  
            message_ou = bus.recv(0.1)  
            if message_ou is not None:   
                rx_data = message_ou.data
                break
            elif time.time() - time_s >1:
                print("仲裁号: %d 未受到回馈-error" % arbitration_id)
                state = 1
                break

    return(state,rx_data) 


def receive_can_messages_main(bus):  

    rx_data_pin = 0
    rx_arbitration_id = 0
    rx_data = [0 for i in range(8)] 

    message = bus.recv(0.00001)  
    if message is not None:      
        rx_data_pin = 1 
        rx_data = message.data
        rx_arbitration_id = message.arbitration_id
    else:
        rx_data_pin = 0
    

    return(rx_data_pin,rx_arbitration_id,rx_data) 

def receive_can_messages_helper2(bus):  

    rx_data_pin = 0
    rx_arbitration_id = 0
    rx_data = [0 for i in range(8)] 

    message = bus.recv(0.00001)  
    if message is not None:       
        rx_data_pin = 1 
        rx_data = message.data
        rx_arbitration_id = message.arbitration_id
    else:
        rx_data_pin = 0
    return(rx_data_pin,rx_arbitration_id,rx_data) 


def read_can_channel(bus,motorID):     
    arbitration_id = 0x1100fd00
    arbitration_id = arbitration_id + motorID
    data_s = [0 for i in range(8)] 
    data_s[0] = 0x1c
    data_s[1] = 0x70
            
    (state,rx_data) = send_extended_frame_main(bus, arbitration_id, data_s,1)
    return state


def set_motor_angle_zero(bus,motorID):
    global pai   
    arbitration_id = 0x0600fd00
    arbitration_id = arbitration_id + motorID
    data_s = [0 for i in range(8)] 
    data_s[0] = 0x01

    (state,rx_data) = send_extended_frame_main(bus, arbitration_id, data_s,1)

    if state == 0:
        print("设置电机ID号:%d 设置负载端零角度OK" % motorID)
    else:
        print("设置电机ID号:%d 设置负载端零角度error" % motorID)

    time.sleep(0.0005)
    return state


def read_motor_single_data(bus,motorID,address): 
    arbitration_id = 0x1100fd00
    arbitration_id = arbitration_id | motorID

    data_s = [0 for i in range(8)] 
    data_s[0] = address & 0x00ff
    data_s[1] = address>>8 

    (state,rx_data) = send_extended_frame_main(bus, arbitration_id, data_s,1)

    if state == 0:
        read_data = rx_data[4]<<24 | rx_data[5]<<16 | rx_data[6]<<8 | rx_data[7]
        #print("read_data = ", hex(read_data))
        print("电机ID号:%d 读取单个寄存器:%s 参数为: %f " % (motorID,hex(address),P4hex_to_float(read_data)))
    else:
        print("电机ID号:%d 读取单个寄存器:%s 参数失败error" % (motorID,hex(address)))   

    return state


def set_motor_single_data(bus,motorID,address,data): 
    arbitration_id = 0x1200fd00
    arbitration_id = arbitration_id | motorID

    data_s = [0 for i in range(8)] 
    data_s[0] = address & 0x00ff
    data_s[1] = address>>8 

    rad_s_hex = float_to_P4hex(data)
    data_s[4] = rad_s_hex[0]
    data_s[5] = rad_s_hex[1]
    data_s[6] = rad_s_hex[2]
    data_s[7] = rad_s_hex[3]

    (state,rx_data) = send_extended_frame_main(bus, arbitration_id, data_s,1)
    if state == 0:
        print("电机ID号:%d 单个参数写入成功!OK!" % motorID)
    else:
        print("电机ID号:%d 写单个寄存器:%s 参数失败error" % (motorID,hex(address))) 

    return state


def set_motion_mode(bus,motorID):      
    arbitration_id = 0x1200fd00
    arbitration_id = arbitration_id + motorID
    data_s = [0 for i in range(8)] 

    (state,rx_data) = send_extended_frame_main(bus, arbitration_id, data_s,1)

    if state == 0:
        print("设置电机ID号:%d 控制模式(运控模式)OK" % motorID)
    else:
        print("设置电机ID号:%d 控制模式(运控模式)error" % motorID)

    time.sleep(0.0005)
    return state


def set_motion_enable(bus,motorID):  
    state = 0   
    arbitration_id = 0x0300fd00
    arbitration_id = arbitration_id + motorID
    data_s = [0 for i in range(8)] 
    (state,rx_data) = send_extended_frame_main(bus, arbitration_id, data_s,1)

    if state == 0:
        print("设置电机ID号:%d 电机模式使能OK" % motorID)
    else:
        print("设置电机ID号:%d 电机模式使能error" % motorID)

    time.sleep(0.0005)
    return state



def leg_set_motion_parameter_L(bus,motorID,radian,read,pd):

    torque = cof.real.mi_motion_parameter[0]      
    speed  = cof.real.mi_motion_parameter[1]    
    if pd == 1:
        KP  = cof.real.mi_motion_parameter[2]   
        KD  = cof.real.mi_motion_parameter[3]    
    elif pd == 2:
        KP  = cof.real.mi_motion_parameter[4]
        KD  = cof.real.mi_motion_parameter[5]
    elif pd == 3:
        KP  = cof.real.mi_motion_parameter[6]
        KD  = cof.real.mi_motion_parameter[7]


    data_s = [0 for i in range(8)] 


    data_int16 = (float_to_uint16(torque,cof.real.T_MIN,cof.real.T_MAX))<<8 
    arbitration_id = 0x01000000 | data_int16 | motorID

    data_int16 = (float_to_uint16(radian,cof.real.P_MIN,cof.real.P_MAX))
    data_s[0] = data_int16>>8
    data_s[1] = data_int16 & 0x00ff

    data_int16 = (float_to_uint16(speed,cof.real.V_MIN,cof.real.V_MAX))
    data_s[2] = data_int16>>8
    data_s[3] = data_int16 & 0x00ff

    data_int16 = (float_to_uint16(KP,cof.real.KP_MIN,cof.real.KP_MAX))
    data_s[4] = data_int16>>8
    data_s[5] = data_int16 & 0x00ff  

    data_int16 = (float_to_uint16(KD,cof.real.KD_MIN,cof.real.KD_MAX))
    data_s[6] = data_int16>>8
    data_s[7] = data_int16 & 0x00ff 

    (state,rx_data)  = send_extended_frame_main(bus, arbitration_id, data_s,read)

    if read == 1:
        print("以下是电机ID号:%d 运控读出的参数-----------|" % motorID)

        print("读出计算出当前角度---")
        read_radian = (rx_data[0]<<8) | rx_data[1]
        read_radian = uint16_to_float(read_radian,cof.real.P_MIN,cof.real.P_MAX)
        print("read_radian=",read_radian)

        print("读出计算出当前速度---")
        read_speed = (rx_data[2]<<8) | rx_data[3]
        read_speed = uint16_to_float(read_speed,cof.real.V_MIN,cof.real.V_MAX)
        print("read_speed=",read_speed)

        print("读出计算出当前扭矩---")
        read_torque = (rx_data[4]<<8) | rx_data[5]
        read_torque = uint16_to_float(read_torque,cof.real.T_MIN,cof.real.T_MAX)
        print("read_torque=",read_torque)

        print("读出计算出当前温度---")
        read_C = (rx_data[6]<<8) | rx_data[7]
        read_C = read_C / 10
        print("read_C=",read_C)

    time.sleep(0.0005)
    return state
 


def leg_set_motion_parameter_R(bus,motorID,radian,read,pd):

    torque = cof.real.mi_motion_parameter[0]
    speed  = cof.real.mi_motion_parameter[1]
    if pd == 1:
        KP  = cof.real.mi_motion_parameter[2]
        KD  = cof.real.mi_motion_parameter[3]
    elif pd == 2:
        KP  = cof.real.mi_motion_parameter[4]
        KD  = cof.real.mi_motion_parameter[5]
    elif pd == 3:
        KP  = cof.real.mi_motion_parameter[6]
        KD  = cof.real.mi_motion_parameter[7]

    data_s = [0 for i in range(8)] 
   

    data_int16 = (float_to_uint16(torque,cof.real.T_MIN,cof.real.T_MAX))<<8 
    arbitration_id = 0x01000000 | data_int16 | motorID

    data_int16 = (float_to_uint16(radian,cof.real.P_MIN,cof.real.P_MAX))
    data_s[0] = data_int16>>8
    data_s[1] = data_int16 & 0x00ff

    data_int16 = (float_to_uint16(speed,cof.real.V_MIN,cof.real.V_MAX))
    data_s[2] = data_int16>>8
    data_s[3] = data_int16 & 0x00ff

    data_int16 = (float_to_uint16(KP,cof.real.KP_MIN,cof.real.KP_MAX))
    data_s[4] = data_int16>>8
    data_s[5] = data_int16 & 0x00ff  

    data_int16 = (float_to_uint16(KD,cof.real.KD_MIN,cof.real.KD_MAX))
    data_s[6] = data_int16>>8
    data_s[7] = data_int16 & 0x00ff 

    (state,rx_data)  = send_extended_frame_helper2(bus, arbitration_id, data_s,read)

    if read == 1:
        print("以下是电机ID号:%d 运控读出的参数-----------|" % motorID)

        print("读出计算出当前角度---")
        read_radian = (rx_data[0]<<8) | rx_data[1]
        read_radian = uint16_to_float(read_radian,cof.real.P_MIN,cof.real.P_MAX)
        print("read_radian=",read_radian)

        print("读出计算出当前速度---")
        read_speed = (rx_data[2]<<8) | rx_data[3]
        read_speed = uint16_to_float(read_speed,cof.real.V_MIN,cof.real.V_MAX)
        print("read_speed=",read_speed)

        print("读出计算出当前扭矩---")
        read_torque = (rx_data[4]<<8) | rx_data[5]
        read_torque = uint16_to_float(read_torque,cof.real.T_MIN,cof.real.T_MAX)
        print("read_torque=",read_torque)

        print("读出计算出当前温度---")
        read_C = (rx_data[6]<<8) | rx_data[7]
        read_C = read_C / 10
        print("read_C=",read_C)

    time.sleep(0.0005)
    return state
 


def robot_motor_init(leg_bus_L,leg_bus_R):

    left_motor_id = [cof.real.l_h_r_j_id, cof.real.l_h_p_j_id, cof.real.l_k_j_id, cof.real.l_jz_j_id]
    for number in left_motor_id:  

        state = set_motor_angle_zero(leg_bus_L,number)
        state = set_motion_mode(leg_bus_L,number)
        state = set_motion_enable(leg_bus_L,number)
        state = leg_set_motion_parameter_L(leg_bus_L,number,0.0,0,1)

    right_motor_id = [cof.real.r_h_r_j_id, cof.real.r_h_p_j_id, cof.real.r_k_j_id, cof.real.r_jz_j_id]
    for number in right_motor_id:  

        state = set_motor_angle_zero(leg_bus_R,number)
        state = set_motion_mode(leg_bus_R,number)
        state = set_motion_enable(leg_bus_R,number)
        state = leg_set_motion_parameter_R(leg_bus_R,number,0.0,0,1)

    return state



def float_to_P4hex(float_data):
    byte_representation = struct.pack('f', float_data)
    return byte_representation


def P4hex_to_float(P4hex_data):
    bytes_obj = P4hex_data.to_bytes(4, byteorder='big') 
    float_value = struct.unpack('f', bytes_obj)[0]
    return float_value


def float_to_uint16(float_data,float_data_min,float_data_max):

    if float_data > float_data_max:
        float_data_s = float_data_max
    elif float_data < float_data_min:
        float_data_s = float_data_min
    else:
        float_data_s = float_data
    
    return int((float_data_s - float_data_min)/(float_data_max - float_data_min) * 65535)


def uint16_to_float(uint16_data,float_data_min,float_data_max):
   return float((uint16_data - 32767)/65535) * (float_data_max - float_data_min)


############主函数############
############主函数############
def main():  


    bus = can.interface.Bus(bustype='socketcan', channel='can1', bitrate=1000000)  

    motorID = 9

    set_motor_angle_zero(bus,motorID)
    set_motion_mode(bus,motorID)
    set_motion_enable(bus,motorID)



    red = 0.0            #最小角度也是起始角度必须为0
    fx = 0               #方向标志位
    red_max = 0.2        #最大角度
    time_delay = 0.01    #速率延时
    while True:

        try:  
            if fx == 0 and red < red_max:
                red = red + 0.01
            elif fx == 0 and red >= red_max:
                fx = 1
                time.sleep(2) 

            elif fx == 1 and red > 0:
                red = red - 0.01
            elif fx == 1 and red <= 0:
                fx = 0
                time.sleep(2) 

            leg_set_motion_parameter_L(bus,motorID,red,0,1)
            time.sleep(time_delay) 


        # 当用户按下 Ctrl+C 时，会执行这里的代码
        except KeyboardInterrupt:  
            print("按下 Ctrl+C,结束----")
            break



    # 在退出时确保资源被释放  
    bus.shutdown() 
    

  
if __name__ == "__main__":  
    main()



# CAN库的安装 https://blog.csdn.net/molangmolang/article/details/140389153


# 进入conda ungym 环境命令     conda activate ungym

# CAN模块插上后 命令行 ifconfig -a 查看是否有 can0 或其他


# 串口 权限设置命令 sudo chmod 777 /dev/ttyUSB0

'''
sudo ip link set down can0
sudo ip link set can0 type can bitrate 1000000 loopback off
sudo ip link set up can0


sudo chmod 777 /dev/ttyUSB0

sudo ip link set down can1
sudo ip link set can1 type can bitrate 1000000 loopback off
sudo ip link set up can1

sudo ip link set down can2
sudo ip link set can2 type can bitrate 1000000 loopback off
sudo ip link set up can2



sudo ip link set down can3
sudo ip link set can3 type can bitrate 1000000 loopback off
sudo ip link set up can3

'''


