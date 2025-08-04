
import serial
import math 
import time
import pygame  # 导入PS2库

import mi_motor_drive as mi_dr
import Dot_D1_config as cof


motor_abnormal = 0
imu_abnormal = 0


class KalmanFilter:  
    #def __init__(self, initial_state, initial_uncertainty, process_noise, measurement_noise):
    def __init__(self, initial_state=0.0, initial_uncertainty=1, process_noise=0.01, measurement_noise=2):   
        self.x_est = initial_state  
        self.P = initial_uncertainty  
        self.Q = process_noise  
        self.R = measurement_noise  
  
    def filter_update(self, measurement):  
        # 预测  
        self.x_est_pred = self.x_est  
        self.P_pred = self.P + self.Q  
  
        # 更新  
        K = self.P_pred / (self.P_pred + self.R)  # 卡尔曼增益  
        self.x_est = self.x_est_pred + K * (measurement - self.x_est_pred)  
        self.P = (1 - K) * self.P_pred  
  
    def get_estimate(self):  
        return self.x_est  



def leg_can_write_L(bus_l):
    while(1):
        #print("设置一圈速度时间0= ",time.time())
        state = mi_dr.leg_set_motion_parameter_L(bus_l, cof.real.l_h_p_j_id, cof.real.l_h_p_j_d_a ,0,2)
        state = mi_dr.leg_set_motion_parameter_L(bus_l,cof.real.l_h_r_j_id,cof.real.l_h_r_j_d_a,0,2)
        state = mi_dr.leg_set_motion_parameter_L(bus_l,cof.real.l_k_j_id,cof.real.l_k_j_d_a,0,2)
        state = mi_dr.leg_set_motion_parameter_L(bus_l,cof.real.l_jz_j_id,cof.real.l_jz_j_d_a,0,3)


def leg_can_read_L(bus_l):
    while(1):

        (rx_data_pin,rx_arbitration_id,rx_data)  = mi_dr.receive_can_messages_main(bus_l)
        if rx_data_pin ==1:

            read_function = rx_arbitration_id>>24                             

            if read_function == 2:

                read_motorID = (rx_arbitration_id>>8)&0xff                    
            
                read_radian = (rx_data[0]<<8) | rx_data[1]                     
                read_radian = mi_dr.uint16_to_float(read_radian,cof.real.P_MIN,cof.real.P_MAX)

                read_speed = (rx_data[2]<<8) | rx_data[3]                     
                read_speed = mi_dr.uint16_to_float(read_speed,cof.real.V_MIN,cof.real.V_MAX)

                read_torque = (rx_data[4]<<8) | rx_data[5]                    
                read_torque = mi_dr.uint16_to_float(read_torque,cof.real.T_MIN,cof.real.T_MAX)

                read_C = (rx_data[6]<<8) | rx_data[7]                        
                read_C = read_C / 10


                if read_motorID == cof.real.l_h_p_j_id:
                    cof.real.l_h_p_j_r_a = read_radian
                    cof.real.l_h_p_j_r_s = read_speed
                    cof.real.l_h_p_j_r_t = read_torque
                                                                                        
                    if not cof.l_h_p_j_min <= cof.real.l_h_p_j_r_a <= cof.l_h_p_j_max: 
                        cof.real.motor_angle_exceed = read_motorID
                        print("角度超出范围的电机ID号,实际角度=",read_motorID,read_radian)

                elif read_motorID == cof.real.l_h_r_j_id:
                    cof.real.l_h_r_j_r_a = read_radian
                    cof.real.l_h_r_j_r_s = read_speed
                    cof.real.l_h_r_j_r_t = read_torque
                    if not cof.l_h_r_j_min <= cof.real.l_h_r_j_r_a <= cof.l_h_r_j_max: 
                        cof.real.motor_angle_exceed = read_motorID
                        print("角度超出范围的电机ID号,实际角度=",read_motorID,read_radian)

                elif read_motorID == cof.real.l_k_j_id:
                    cof.real.l_k_j_r_a = read_radian
                    cof.real.l_k_j_r_s = read_speed
                    cof.real.l_k_j_r_t = read_torque
                    if not cof.l_k_j_min <= cof.real.l_k_j_r_a <= cof.l_k_j_max:      
                        cof.real.motor_angle_exceed = read_motorID
                        print("角度超出范围的电机ID号,实际角度=",read_motorID,read_radian)

                elif read_motorID == cof.real.l_jz_j_id:
                    cof.real.l_jz_j_r_a = read_radian
                    cof.real.l_jz_j_r_s = read_speed
                    cof.real.l_jz_j_r_t = read_torque
                    if not cof.l_jz_j_min <= cof.real.l_jz_j_r_a <= cof.l_jz_j_max:      
                        cof.real.motor_angle_exceed = read_motorID
                        print("角度超出范围的电机ID号,实际角度=",read_motorID,read_radian)

        time.sleep(0.0002)


def leg_can_write_R(bus_r):
    while(1):
        #print("设置一圈速度时间0= ",time.time())
        state = mi_dr.leg_set_motion_parameter_R(bus_r,cof.real.r_h_p_j_id,cof.real.r_h_p_j_d_a,0,2)
        state = mi_dr.leg_set_motion_parameter_R(bus_r,cof.real.r_h_r_j_id,cof.real.r_h_r_j_d_a,0,2)
        state = mi_dr.leg_set_motion_parameter_R(bus_r,cof.real.r_k_j_id,cof.real.r_k_j_d_a,0,2)
        state = mi_dr.leg_set_motion_parameter_R(bus_r,cof.real.r_jz_j_id,cof.real.r_jz_j_d_a,0,3)

def leg_can_read_R(bus_r):

    while(1):

        (rx_data_pin,rx_arbitration_id,rx_data)  = mi_dr.receive_can_messages_helper2(bus_r) 
        if rx_data_pin ==1:

            read_function = rx_arbitration_id>>24                             

            if read_function == 2:

                read_motorID = (rx_arbitration_id>>8)&0xff                    
            
                read_radian = (rx_data[0]<<8) | rx_data[1]                     
                read_radian = mi_dr.uint16_to_float(read_radian,cof.real.P_MIN,cof.real.P_MAX)

                read_speed = (rx_data[2]<<8) | rx_data[3]                    
                read_speed = mi_dr.uint16_to_float(read_speed,cof.real.V_MIN,cof.real.V_MAX)

                read_torque = (rx_data[4]<<8) | rx_data[5]                     
                read_torque = mi_dr.uint16_to_float(read_torque,cof.real.T_MIN,cof.real.T_MAX)

                read_C = (rx_data[6]<<8) | rx_data[7]                         
                read_C = read_C / 10


                if read_motorID ==  cof.real.r_h_p_j_id:
                    cof.real.r_h_p_j_r_a = read_radian
                    cof.real.r_h_p_j_r_s = read_speed
                    cof.real.r_h_p_j_r_t = read_torque
                                                                                       
                    if not cof.r_h_p_j_min <= cof.real.r_h_p_j_r_a <= cof.r_h_p_j_max: 
                        cof.real.motor_angle_exceed = read_motorID
                        print("角度超出范围的电机ID号,实际角度=",read_motorID,read_radian)

                elif read_motorID == cof.real.r_h_r_j_id:
                    cof.real.r_h_r_j_r_a = read_radian
                    cof.real.r_h_r_j_r_s = read_speed
                    cof.real.r_h_r_j_r_t = read_torque
                    if not cof.r_h_r_j_min <= cof.real.r_h_r_j_r_a  <= cof.r_h_r_j_max: 
                        cof.real.motor_angle_exceed = read_motorID   
                        print("角度超出范围的电机ID号,实际角度=",read_motorID,read_radian)

                elif read_motorID == cof.real.r_k_j_id:
                    cof.real.r_k_j_r_a = read_radian
                    cof.real.r_k_j_r_s = read_speed
                    cof.real.r_k_j_r_t = read_torque
                    if not cof.r_k_j_min <= cof.real.r_k_j_r_a  <= cof.r_k_j_max:      
                        cof.real.motor_angle_exceed = read_motorID
                        print("角度超出范围的电机ID号,实际角度=",read_motorID,read_radian)

                elif read_motorID == cof.real.r_jz_j_id:
                    cof.real.r_jz_j_r_a = read_radian
                    cof.real.r_jz_j_r_s = read_speed
                    cof.real.r_jz_j_r_t = read_torque
                    if not cof.r_jz_j_min <= cof.real.r_jz_j_r_a  <= cof.r_jz_j_max:     
                        cof.real.motor_angle_exceed = read_motorID
                        print("角度超出范围的电机ID号,实际角度=",read_motorID,read_radian)
                         
        time.sleep(0.0002)


def read_imu_data():
    global imu_abnormal

    read_imu = [0xff,0xaa,0x03,0X0c,0X0]
    ser = serial.Serial("/dev/ttyUSB0",230400,timeout=0.001)     

    while(1):
  
        ser.flushInput()               
        ser.write(read_imu)            
        while True:
            count = ser.inWaiting()
            if count >= 22:
                break
            time.sleep(0.0005)          

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

            cof.real.imu_data[3] = math.radians(Wx)  
            cof.real.imu_data[4] = math.radians(Wy) 
            cof.real.imu_data[5] = math.radians(Wz)


            Rx = (com_input[14]<<8 | com_input[13])/32768 *180
            if Rx >= 180:
                Rx -= 2 * 180
            Ry = (com_input[16]<<8 | com_input[15])/32768 *180
            if Ry >= 180:
                Ry -= 2 * 180
            Rz = (com_input[18]<<8 | com_input[17])/32768 *180
            if Rz >= 180:
                Rz -= 2 * 180

            cof.real.imu_data[6] = math.radians(Rx) 
            cof.real.imu_data[7] = math.radians(Ry) 
            cof.real.imu_data[8] = math.radians(Rz)
                                           
            if abs(cof.real.imu_data[6]) > cof.real.imu_angle_effective or abs(cof.real.imu_data[7]) > cof.real.imu_angle_effective :
                cof.real.imu_angle_exceed = 1

            imu_abnormal = 0

        else:       
            print('---------IMU数据解析格式故障---------count = ',count)


def read_control_data():

    pygame.init()                                                                    
    pygame.joystick.init()                             

    if pygame.joystick.get_count() == 0:               
        print("没有检测到操纵杆，请连接后再试。")          
    else:
        joystick = pygame.joystick.Joystick(0)       
        joystick.init()                               
        print("操纵杆已初始化：", joystick.get_name())  

    running = True
    while running:                                   

        for event in pygame.event.get():             

            if event.type == pygame.QUIT:            
                running = False                      

            if event.type == pygame.JOYBUTTONDOWN:     
                kay = int(event.button)
                print(f"Button {kay} 被按下")         

                if kay == 4:                           
                    cof.start = 1                     
                elif kay == 5:                         
                    cof.commands[0] = 0.0
                    cof.commands[1] = 0.0
                    cof.commands[2] = 0.0
                elif kay == 3:                         
                    cof.commands[0] = cof.run_speed
                    cof.commands[1] = 0.0
                    cof.commands[2] = 0.0
                elif kay == 0:                         
                    cof.commands[0] = -cof.run_speed
                    cof.commands[1] = 0.0
                    cof.commands[2] = 0.0
                elif kay == 2:                         
                    cof.commands[1] = cof.run_speed
                    cof.commands[0] = 0.0
                    cof.commands[2] = 0.0
                elif kay == 1:                         
                    cof.commands[1] = -cof.run_speed
                    cof.commands[0] = 0.0
                    cof.commands[2] = 0.0
                elif kay == 6:                         
                    cof.commands[2] = 0.6 
                    cof.commands[1] = 0.0
                    cof.commands[0] = 0.0 
                elif kay == 7:                       
                    cof.commands[2] = -0.6 
                    cof.commands[1] = 0.0
                    cof.commands[0] = 0.0
            
            time.sleep(0.2)

        time.sleep(0.2)

    pygame.quit()  


def ble_remote_server():
    """BLE蓝牙遥控服务器线程函数"""
    try:
        # 检查BLE是否启用
        if not cof.ble.enabled:
            print("BLE遥控功能已禁用")
            return
            
        print("正在启动BLE遥控服务器...")
        
        # 导入BLE模块
        import ble_remote
        
        # 启动BLE服务器线程
        ble_thread = ble_remote.start_ble_server_thread()
        
        print("BLE遥控服务器已启动")
        
        # 保持线程活跃
        while True:
            time.sleep(1.0)
            
    except ImportError as e:
        print(f"BLE模块导入失败: {e}")
        print("请确保已安装 bleak 库: pip3 install bleak")
    except Exception as e:
        print(f"BLE遥控服务器启动失败: {e}")



