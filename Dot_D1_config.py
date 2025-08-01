
import torch
import numpy as np



# 各个关节电机 在IsaacGYM 仿真里的 角度范围(此值是IsaacGYM仿真的范围值)
l_h_p_j_min   = -1.5          
l_h_p_j_max   = 0.5          

l_h_r_j_min   = -1.3         
l_h_r_j_max   = 0.35           

l_k_j_min     = -2.0         
l_k_j_max     = 0.2          

l_jz_j_min     = -1.0         
l_jz_j_max     = 0.4          


r_h_p_j_min   = -0.5         
r_h_p_j_max   = 1.5          

r_h_r_j_min   = -0.35        
r_h_r_j_max   = 1.3          

r_k_j_min     = -0.2          
r_k_j_max     = 2.0          

r_jz_j_min     = -0.4         
r_jz_j_max     = 1.0         

# 初始化微蹲姿态 各个电机 初始角度补偿值 
l_h_p_j_init   =  -0.4                 
l_h_r_j_init   =  0.0               
l_k_j_init     =  -0.8         
l_jz_j_init    =  -0.4               

r_h_p_j_init   =  0.4       
r_h_r_j_init   =  0.0                       
r_k_j_init     =  0.8        
r_jz_j_init    =  0.4        

motor_real_angle_init = np.array([[l_h_p_j_init, l_h_r_j_init, l_k_j_init, l_jz_j_init, r_h_p_j_init, r_h_r_j_init, r_k_j_init,r_jz_j_init]]) 

commands = [0.0,0.0,0.0]     
run_speed = 0.2             

start = 0                    


class sim:
    dt = 0.001                                   
    decimation = 10                               

    clip_observations = 4.                       
    clip_actions = 4.                             

    lin_vel = 2.                                  
    ang_vel  = 1.                                 

    dof_pos = 1.                                  
    dof_vel = 0.05                                
    quat = 1.                                     


    action_scale = 0.25                          

    num_obs = 34                                
    frame_stack = 15                             
    num_observations = num_obs * frame_stack     
    num_actions = 8                              
 


class real:

    hostID = 0xfd   

    # 所有电机ID号
    l_h_p_j_id   =  1        
    l_h_r_j_id   =  2        
    l_k_j_id     =  3       
    l_jz_j_id    =  4        

    r_h_p_j_id   =  5        
    r_h_r_j_id   =  6              
    r_k_j_id     =  7        
    r_jz_j_id    =  8        


    # 机械臂各个关节实际旋转弧度                                    
    l_h_p_j_r_a   =  0.0      
    l_h_r_j_r_a   =  0.0     
    l_k_j_r_a     =  0.0   
    l_jz_j_r_a    =  0.0    

    r_h_p_j_r_a   =  0.0   
    r_h_r_j_r_a   =  0.0                
    r_k_j_r_a     =  0.0    
    r_jz_j_r_a    =  0.0    

    # 机械臂各个关节实际扭矩
    l_h_p_j_r_t   =  0.0    
    l_h_r_j_r_t   =  0.0     
    l_k_j_r_t     =  0.0    
    l_jz_j_r_t    =  0.0    

    r_h_p_j_r_t   =  0.0     
    r_h_r_j_r_t   =  0.0                    
    r_k_j_r_t     =  0.0   
    r_jz_j_r_t    =  0.0    

    # 机械臂各个关节实际转速 
    l_h_p_j_r_s   =  0.0     
    l_h_r_j_r_s   =  0.0     
    l_k_j_r_s     =  0.0    
    l_jz_j_r_s    =  0.0    

    r_h_p_j_r_s   =  0.0     
    r_h_r_j_r_s   =  0.0                    
    r_k_j_r_s     =  0.0   
    r_jz_j_r_s    =  0.0    

    # 腿部机械臂各个关节期望旋转弧度
    l_h_p_j_d_a   =  0.0     
    l_h_r_j_d_a   =  0.0   
    l_k_j_d_a     =  0.0   
    l_jz_j_d_a    =  0.0     

    r_h_p_j_d_a   =  0.0    
    r_h_r_j_d_a   =  0.0                 
    r_k_j_d_a     =  0.0   
    r_jz_j_d_a    =  0.0   

    # 不可改动(灵足E01)
    P_MIN = -12.5    
    P_MAX = 12.5    
    V_MIN = -44.0   
    V_MAX = 44.0    
    KP_MIN = 0.0    
    KP_MAX = 500.0   
    KD_MIN = 0.0    
    KD_MAX = 5.0     
    T_MIN = -17.0   
    T_MAX =  17.0    


    #运控参数 不可改动
    mi_motion_parameter =  [0.,0.,9.0,0.5,9.0,0.5,4.0,0.2]

    # 马达是否超出范围标志位
    motor_angle_exceed = 0   


    #IMU数据 0～2：XYZ加速度， 3～5：XYZ角速度， 6～8：XYZ欧拉角，9～12：四元数(qx qy qz qw)
    imu_data = [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]

    imu_angle_effective = 50 
    imu_angle_exceed = 0     
    imu_y_wc = 0.

