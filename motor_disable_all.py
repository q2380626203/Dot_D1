#!/usr/bin/python3
# -*- coding: UTF-8 -*-  

import can  
import time
import mi_motor_drive as mi_dr
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


def set_motion_disable(bus,motorID):  
    state = 0   
    arbitration_id = 0x0400fd00
    arbitration_id = arbitration_id + motorID
    data_s = [0 for i in range(8)] 
    (state,rx_data) = send_extended_frame_main(bus, arbitration_id, data_s,1)

    if state == 0:
        print("设置电机ID号:%d 电机模式失能OK" % motorID)
    else:
        print("设置电机ID号:%d 电机模式失能error" % motorID)

    time.sleep(0.0005)
    return state


def robot_motor_disable_all(leg_bus_L, leg_bus_R):
    """
    失能所有电机，参考robot_motor_init的结构
    """
    print("开始失能所有电机...")
    
    # 失能左腿电机
    left_motor_id = [cof.real.l_h_r_j_id, cof.real.l_h_p_j_id, cof.real.l_k_j_id, cof.real.l_jz_j_id]
    print("失能左腿电机...")
    for number in left_motor_id:  
        state = set_motion_disable(leg_bus_L, number)
        if state != 0:
            print("左腿电机ID:%d 失能失败" % number)

    # 失能右腿电机
    right_motor_id = [cof.real.r_h_r_j_id, cof.real.r_h_p_j_id, cof.real.r_k_j_id, cof.real.r_jz_j_id]
    print("失能右腿电机...")
    for number in right_motor_id:  
        state = set_motion_disable(leg_bus_R, number)
        if state != 0:
            print("右腿电机ID:%d 失能失败" % number)

    print("所有电机失能操作完成")
    return state


############主函数############
############主函数############
def main():  
    print("机器人电机失能程序启动...")
    
    # 创建CAN总线连接，参考Dot_D1_run.py的配置
    bus_l = can.interface.Bus(interface='socketcan', channel='can0', bitrate=1000000) 
    bus_r = can.interface.Bus(interface='socketcan', channel='can1', bitrate=1000000) 

    try:
        # 失能所有电机
        robot_motor_disable_all(bus_l, bus_r)
        
        print("电机失能完成，机器人已安全停止")
        
    except Exception as e:
        print(f"执行失能过程中出现错误: {e}")
    
    finally:
        # 在退出时确保资源被释放  
        bus_l.shutdown() 
        bus_r.shutdown()
        print("CAN总线连接已关闭")
    

if __name__ == "__main__":  
    main()