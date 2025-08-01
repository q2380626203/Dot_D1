
import sys 
import math
from math import cos,sin
import time
import math 
import time
import can  
import _thread
import torch

import mi_motor_drive as mi_dr
import synch_run as synch
import fixed_action as fixed
import Dot_D1_config as cof

import numpy as np
from collections import deque



rl_model_path_yd = 'rl_model/policy_yd.pt'                                              
rl_model_yd = torch.jit.load(rl_model_path_yd)                                          

rl_model_path_jz = 'rl_model/policy_jz.pt'                                              
rl_model_jz = torch.jit.load(rl_model_path_jz)                                         


bus_l = can.interface.Bus(interface ='socketcan', channel='can0', bitrate=1000000) 
bus_r = can.interface.Bus(interface ='socketcan', channel='can1', bitrate=1000000) 




#**************************************************************************
# 子线程集合
#**************************************************************************
def leg_can_write_L():             
    global bus_l
    synch.leg_can_write_L(bus_l)

def leg_can_read_L():            
    global bus_l
    synch.leg_can_read_L(bus_l)

def leg_can_write_R():           
    global bus_r
    synch.leg_can_write_R(bus_r)

def leg_can_read_R():            
    global bus_r
    synch.leg_can_read_R(bus_r)

def read_imu_data():              
    synch.read_imu_data()

def read_control_data():         
    synch.read_control_data()


@torch.jit.script
def quat_rotate_inverse(q, v):
    shape = q.shape
    q_w = q[:, -1]
    q_vec = q[:, :3]
    a = v * (2.0 * q_w ** 2 - 1.0).unsqueeze(-1)
    b = torch.cross(q_vec, v, dim=-1) * q_w.unsqueeze(-1) * 2.0
    c = q_vec * \
        torch.bmm(q_vec.view(shape[0], 1, 3), v.view(
            shape[0], 3, 1)).squeeze(-1) * 2.0
    return a - b + c


#**************************************************************************
# 读出观测值
#**************************************************************************
def read_obs(): 
    # 关节位置
    dof_pos = np.array([cof.real.l_h_p_j_r_a,
                        cof.real.l_h_r_j_r_a,
                        cof.real.l_k_j_r_a,
                        cof.real.l_jz_j_r_a,
                        cof.real.r_h_p_j_r_a,
                        cof.real.r_h_r_j_r_a,
                        cof.real.r_k_j_r_a,
                        cof.real.r_jz_j_r_a
                        ])                              

    # 关节速度                                                                                                                                                         
    dof_vel = np.array([cof.real.l_h_p_j_r_s,
                        cof.real.l_h_r_j_r_s,
                        cof.real.l_k_j_r_s,
                        cof.real.l_jz_j_r_s,
                        cof.real.r_h_p_j_r_s,
                        cof.real.r_h_r_j_r_s,
                        cof.real.r_k_j_r_s,
                        cof.real.r_jz_j_r_s
                        ]) 

    # IMU 角速度
    imu_vel = np.array([cof.real.imu_data[3],cof.real.imu_data[4],cof.real.imu_data[5]])

    # IMU 欧拉角     
    imu_rpy = np.array([cof.real.imu_data[6],cof.real.imu_data[7]])   
    imu_rpy[imu_rpy > math.pi] -= 2 * math.pi                         

    return (dof_pos,dof_vel,imu_vel,imu_rpy)


#**************************************************************************
# 执行一步更改电机新的位置 
#**************************************************************************
def step(target_q):
    cof.real.l_h_p_j_d_a   =  target_q[0] + cof.l_h_p_j_init                  
    cof.real.l_h_r_j_d_a   =  target_q[1] + cof.l_h_r_j_init                  
    cof.real.l_k_j_d_a     =  target_q[2] + cof.l_k_j_init                     
    cof.real.l_jz_j_d_a    =  target_q[3] + cof.l_jz_j_init                   

    cof.real.r_h_p_j_d_a   =  target_q[4] + cof.r_h_p_j_init                   
    cof.real.r_h_r_j_d_a   =  target_q[5] + cof.r_h_r_j_init                            
    cof.real.r_k_j_d_a     =  target_q[6] + cof.r_k_j_init                       
    cof.real.r_jz_j_d_a    =  target_q[7] + cof.r_jz_j_init                  

#**************************************************************************
# 主程序
#**************************************************************************
def main():
    global bus_l, bus_r, rl_model_yd, rl_model_jz
    time.sleep(1)
    _thread.start_new_thread(read_control_data,()) #创建一个读取遥控器的线程

    time.sleep(1)
    state = mi_dr.robot_motor_init(bus_l,bus_r)    
    

    print("机器人所有电机是否都初始化产生扭矩 且 离开定零支架？如果不是请检查原因或重新关机开机执行") 
    cof.start = 0
    print('请按下遥控器左1按键启动')
    while True:
        if cof.start == 1:
            break
        time.sleep(0.1)

    
    _thread.start_new_thread(leg_can_write_L,())  
    _thread.start_new_thread(leg_can_read_L,())    
    _thread.start_new_thread(leg_can_write_R,())   
    _thread.start_new_thread(leg_can_read_R ,())  
    _thread.start_new_thread(read_imu_data,())    
    time.sleep(0.1)

    fixed.robot_attitude_init()                   


    print("机器人双腿是否正常执行到微蹲姿态？") 
    print("如果一切正常则:请按下遥控器左1按键启动,如果不是请检查原因或重新关机开机执行")
    cof.start = 0
    while True:
        if cof.start == 1:
            break
        time.sleep(0.1)

    time.sleep(1)                                 


    target_q = np.zeros((cof.sim.num_actions), dtype=np.double)                   
    action = np.zeros((cof.sim.num_actions), dtype=np.double)                    

    hist_obs = deque()                                                             
    for _ in range(cof.sim.frame_stack):                                          
        hist_obs.append(np.zeros([1, cof.sim.num_obs], dtype=np.double)) 

    obs = np.zeros([1, cof.sim.num_obs], dtype=np.float32)                        
    policy_input = np.zeros([1, cof.sim.num_observations], dtype=np.float32)      

    count_lowlevel = 0                                                             
    yd_or_jz_bit = 100                                                            
    dt_front = time.time()

    while True:

        #---------------------摔倒或imu异常恢复-----------------
        if synch.imu_abnormal == 1 and cof.real.imu_data[6]==0 and cof.real.imu_data[7]==0 and cof.real.imu_data[8]==0:   
            print('IMU启动异常!无数据输出，请检查相关设施！')
            break
        if cof.real.motor_angle_exceed != 0 or cof.real.imu_angle_exceed != 0 :   
            print('有关节电机 或 IMU XY倾角 超出范围。即将退出执行',cof.real.motor_angle_exceed,cof.real.imu_angle_exceed)
            cof.real.motor_angle_exceed = 0                                       
            fixed.leg_vertical()                                                 
            print('请提起机器人,5秒后执行恢复到微蹲姿态')
            time.sleep(5)
            fixed.robot_attitude_init()                                            

            #-------------------遥控器重新启动-----------------
            cof.start = 0
            print('请按下遥控器左1按键启动')
            while True:
                if cof.start == 1:
                    break
                time.sleep(0.1)
            cof.real.motor_angle_exceed = 0                                        
            count_lowlevel = 0                                                     
            yd_or_jz_bit = 100
            
            hist_obs = deque()                                                             
            for _ in range(cof.sim.frame_stack):                                        
                hist_obs.append(np.zeros([1, cof.sim.num_obs], dtype=np.double)) 

            time.sleep(1)


        model_time = time.time()
        # --------------------降采样10步执行一次---------------
        if count_lowlevel % cof.sim.decimation == 0:

            (dof_pos,dof_vel,imu_vel,imu_rpy) = read_obs()                           

            obs[0, 0] = math.sin(2 * math.pi * count_lowlevel * cof.sim.dt / 0.6)     
            obs[0, 1] = math.cos(2 * math.pi * count_lowlevel * cof.sim.dt / 0.6)

            obs[0, 2] = cof.commands[0] * cof.sim.lin_vel                            
            obs[0, 3] = cof.commands[1] * cof.sim.lin_vel                                                                      
            obs[0, 4] = cof.commands[2] * cof.sim.ang_vel  

            obs[0, 5:13] = (dof_pos - cof.motor_real_angle_init) * cof.sim.dof_pos   
            obs[0, 13:21] = dof_vel * cof.sim.dof_vel                                
            obs[0, 21:29] = action                                                   

            obs[0, 29:32] = imu_vel * cof.sim.ang_vel                                
            obs[0, 32:34] = imu_rpy * cof.sim. quat                                  

            
            obs = np.clip(obs, -cof.sim.clip_observations, cof.sim.clip_observations)
            hist_obs.append(obs)                                                     
            hist_obs.popleft()                                                                                     
            

            for i in range(cof.sim.frame_stack):                
                policy_input[0, i * cof.sim.num_obs: (i + 1) * cof.sim.num_obs:] = hist_obs[i][0, :]
            
            print('---模型推理周期---=',time.time()-model_time) 


            torch.set_num_threads(1)
            if abs(cof.commands[0]) < 0.02 and abs(cof.commands[1]) < 0.02 and abs(cof.commands[2])< 0.02 :
                if yd_or_jz_bit > 0 :
                    yd_or_jz_bit -= 1
            else:
                yd_or_jz_bit = 100

            if yd_or_jz_bit > 0:
                action[:] = rl_model_yd(torch.tensor(policy_input))[0].detach().numpy()
            else:
                action[:] = rl_model_jz(torch.tensor(policy_input))[0].detach().numpy()


            action = np.clip(action, -cof.sim.clip_actions, cof.sim.clip_actions)
            target_q = action * cof.sim.action_scale                                
            step(target_q)                                                           


        count_lowlevel += cof.sim.decimation                                        


        #------------------------阻塞10毫秒---------------------
        while True:
            if (time.time() - dt_front) >= (cof.sim.dt * cof.sim.decimation):           
                dt_front = time.time()
                break
            else:
                time.sleep(0.0001)


if __name__ == '__main__':
    main()


'''

sudo cpufreq-set -c 0 -g performance
sudo cpufreq-set -c 1 -g performance
sudo cpufreq-set -c 2 -g performance
sudo cpufreq-set -c 3 -g performance

sudo chmod 777 /dev/ttyUSB0
sudo ip link set down can0
sudo ip link set can0 type can bitrate 1000000 loopback off
sudo ip link set up can0

sudo ip link set down can1
sudo ip link set can1 type can bitrate 1000000 loopback off
sudo ip link set up can1


'''
