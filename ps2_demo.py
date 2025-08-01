
import time
import pygame  # 导入PS2库

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
    try:
        
        for event in pygame.event.get():             

            if event.type == pygame.QUIT:            
                running = False                      

            if event.type == pygame.JOYBUTTONDOWN:         
                abc = int(event.button)
                print(f"Button {abc} 被按下")      
             
            time.sleep(0.2)
        
        time.sleep(0.2)

    except KeyboardInterrupt: 
        print("你已按下 Ctrl+C, 主程序将退出...") 
        pygame.quit()  # 退出pygame 
        break

    



