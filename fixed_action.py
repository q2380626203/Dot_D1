
import time
import mi_motor_drive as mi_dr
import synch_run as synch
import Dot_D1_config as cof

pi = 3.1415926
half_pi = 1.570796


def robot_attitude_init():
    #------------------------------执行双腿至微蹲姿态

    while True:
        # 左腿 
        if cof.real.l_h_p_j_d_a < (cof.l_h_p_j_init - 0.001):            
            cof.real.l_h_p_j_d_a  += 0.001
        elif cof.real.l_h_p_j_d_a > (cof.l_h_p_j_init + 0.001):          
            cof.real.l_h_p_j_d_a  -= 0.001

        elif cof.real.l_h_r_j_d_a < (cof.l_h_r_j_init - 0.001):         
            cof.real.l_h_r_j_d_a  += 0.001
        elif cof.real.l_h_r_j_d_a > (cof.l_h_r_j_init + 0.001):          
            cof.real.l_h_r_j_d_a  -= 0.001

        elif cof.real.l_k_j_d_a < (cof.l_k_j_init - 0.001):             
            cof.real.l_k_j_d_a += 0.001
        elif cof.real.l_k_j_d_a > (cof.l_k_j_init + 0.001):           
            cof.real.l_k_j_d_a -= 0.001


        elif cof.real.l_jz_j_d_a < (cof.l_jz_j_init - 0.001):             
            cof.real.l_jz_j_d_a += 0.001
        elif cof.real.l_jz_j_d_a > (cof.l_jz_j_init + 0.001):             
            cof.real.l_jz_j_d_a -= 0.001

        # 右腿
        
        elif cof.real.r_h_p_j_d_a < (cof.r_h_p_j_init - 0.001):         
            cof.real.r_h_p_j_d_a  += 0.001
        elif cof.real.r_h_p_j_d_a > (cof.r_h_p_j_init + 0.001):         
            cof.real.r_h_p_j_d_a  -= 0.001

        elif cof.real.r_h_r_j_d_a < (cof.r_h_r_j_init - 0.001):       
            cof.real.r_h_r_j_d_a  += 0.001
        elif cof.real.r_h_r_j_d_a > (cof.r_h_r_j_init + 0.0001):      
            cof.real.r_h_r_j_d_a  -= 0.0001

        elif cof.real.r_k_j_d_a < (cof.r_k_j_init - 0.001):            
            cof.real.r_k_j_d_a += 0.001
        elif cof.real.r_k_j_d_a > (cof.r_k_j_init + 0.001):           
            cof.real.r_k_j_d_a -= 0.001


        elif cof.real.r_jz_j_d_a < (cof.r_jz_j_init - 0.001):          
            cof.real.r_jz_j_d_a += 0.001
        elif cof.real.r_jz_j_d_a > (cof.r_jz_j_init + 0.001):         
            cof.real.r_jz_j_d_a -= 0.001

        else:
            break

        #必要的延时    
        time.sleep(0.003)


# 保持最后实际角度防止扩大持续堵转
def leg_vertical():
    cof.real.l_h_r_j_d_a  = cof.real.l_h_r_j_r_a
    cof.real.l_h_p_j_d_a  = cof.real.l_h_p_j_r_a
    cof.real.l_k_j_d_a    = cof.real.l_k_j_r_a
    cof.real.l_jz_j_d_a    = cof.real.l_jz_j_r_a

    cof.real.r_h_r_j_d_a = cof.real.r_h_r_j_r_a
    cof.real.r_h_p_j_d_a = cof.real.r_h_p_j_r_a
    cof.real.r_k_j_d_a   = cof.real.r_k_j_r_a
    cof.real.r_jz_j_d_a   = cof.real.r_jz_j_r_a

    time.sleep(1)

