#!/usr/bin/env python3
"""
BLE蓝牙遥控模块
实现蓝牙遥控服务器，接收移动端遥控指令
支持蓝牙和网络Socket两种连接方式
"""

import json
import logging
import time
import threading
import socket
from typing import Dict, Any, Optional

# 尝试导入蓝牙库
BLUETOOTH_AVAILABLE = False
try:
    import bluetooth
    BLUETOOTH_AVAILABLE = True
    print("✓ PyBluez蓝牙库可用")
except ImportError:
    print("⚠ PyBluez不可用，将使用网络Socket作为备用遥控方案")

import Dot_D1_config as cof

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RemoteControlServer:
    """遥控服务器类 - 支持蓝牙和网络Socket"""
    
    def __init__(self):
        self.server_sock = None
        self.client_sock = None
        self.client_info = None
        self.is_running = False
        self.last_command_time = 0
        self.heartbeat_timeout = 2.0  # 心跳超时时间（秒）
        self.use_bluetooth = BLUETOOTH_AVAILABLE and cof.ble.enabled
        
        # 遥控参数
        self.run_speed = getattr(cof.ble, 'speed_limit', 0.2)
        self.center_subtle = getattr(cof.ble, 'center_adjust_step', 0.001)
        
    def setup_bluetooth_server(self):
        """设置蓝牙服务器"""
        try:
            # 创建蓝牙socket
            self.server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            
            # 绑定到端口1（RFCOMM端口）
            port = 1
            self.server_sock.bind(("", port))
            self.server_sock.listen(1)
            
            # 获取本地蓝牙地址
            local_addr = bluetooth.read_local_bdaddr()[0]
            
            print(f"✓ 蓝牙服务器已启动")
            print(f"  地址: {local_addr}")
            print(f"  端口: {port}")
            print(f"  设备名: {cof.ble.device_name}")
            
            # 注册服务
            uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"
            bluetooth.advertise_service(
                self.server_sock, 
                "Dot_D1_Remote_Control",
                service_id=uuid,
                service_classes=[uuid, bluetooth.SERIAL_PORT_CLASS],
                profiles=[bluetooth.SERIAL_PORT_PROFILE]
            )
            
            logger.info("蓝牙服务已注册，等待连接...")
            return True
            
        except Exception as e:
            logger.error(f"蓝牙服务器设置失败: {e}")
            return False
    
    def setup_network_server(self):
        """设置网络Socket服务器（备用方案）"""
        try:
            # 创建TCP socket
            self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # 绑定到端口
            port = 8888
            self.server_sock.bind(('0.0.0.0', port))
            self.server_sock.listen(1)
            
            print(f"✓ 网络遥控服务器已启动")
            print(f"  端口: {port}")
            print(f"  连接方式: telnet <机器人IP> {port}")
            print(f"  或使用移动端APP连接")
            
            logger.info("网络服务已启动，等待连接...")
            return True
            
        except Exception as e:
            logger.error(f"网络服务器设置失败: {e}")
            return False
    
    def setup_server(self):
        """设置服务器"""
        if self.use_bluetooth:
            return self.setup_bluetooth_server()
        else:
            return self.setup_network_server()
    
    def process_command(self, command_data: Dict[str, Any]):
        """处理遥控指令"""
        try:
            cmd_type = command_data.get("cmd", "")
            
            if cmd_type == "move":
                # 运动控制指令
                x_vel = command_data.get("x", 0.0)
                y_vel = command_data.get("y", 0.0)
                z_vel = command_data.get("z", 0.0)
                
                # 限制速度范围
                x_vel = max(-self.run_speed, min(self.run_speed, x_vel))
                y_vel = max(-self.run_speed, min(self.run_speed, y_vel))
                z_vel = max(-2*self.run_speed, min(2*self.run_speed, z_vel))
                
                cof.commands[0] = x_vel  # 前进后退
                cof.commands[1] = y_vel  # 左右移动
                cof.commands[2] = z_vel  # 旋转
                
            elif cmd_type == "button":
                # 按键指令（兼容现有433MHz遥控器功能）
                button = command_data.get("button", 0)
                self.process_button_command(button)
                
            elif cmd_type == "center_adjust":
                # 重心调节
                adjust = command_data.get("adjust", 0.0)
                if adjust > 0:
                    cof.center_x += self.center_subtle
                elif adjust < 0:
                    cof.center_x -= self.center_subtle
                    
            elif cmd_type == "stop":
                # 停止所有运动
                cof.commands[0] = 0.0
                cof.commands[1] = 0.0
                cof.commands[2] = 0.0
                
            elif cmd_type == "ping":
                # 心跳包
                pass
                
        except Exception as e:
            logger.error(f"指令处理错误: {e}")
    
    def process_button_command(self, button: int):
        """处理按键指令（兼容433MHz遥控器）"""
        if button == 1:      # 前进
            cof.commands[0] = self.run_speed
        elif button == 2:    # 后退
            cof.commands[0] = -self.run_speed
        elif button == 3:    # 左移
            cof.commands[1] = self.run_speed
        elif button == 4:    # 右移
            cof.commands[1] = -self.run_speed
        elif button == 7:    # 左转
            cof.commands[2] = -(2*self.run_speed)
        elif button == 9:    # 右转
            cof.commands[2] = (2*self.run_speed)
        elif button == 5:    # 重心微调
            cof.center_x += self.center_subtle
        else:                # 停止
            cof.commands[0] = 0.0
            cof.commands[1] = 0.0
            cof.commands[2] = 0.0
    
    def send_status(self):
        """发送机器人状态信息"""
        if not self.client_sock:
            return
            
        try:
            status_data = {
                "type": "status",
                "timestamp": time.time(),
                "commands": cof.commands.copy(),
                "center_x": getattr(cof, 'center_x', 0.0),
                "motor_angle_exceed": getattr(cof.real, 'motor_angle_exceed', 0),
                "imu_angle_exceed": getattr(cof.real, 'imu_angle_exceed', 0),
                "connection_type": "bluetooth" if self.use_bluetooth else "network"
            }
            
            status_json = json.dumps(status_data) + "\n"
            self.client_sock.send(status_json.encode('utf-8'))
                    
        except Exception as e:
            logger.error(f"状态发送错误: {e}")
    
    def handle_client(self):
        """处理客户端连接"""
        try:
            conn_type = "蓝牙" if self.use_bluetooth else "网络"
            logger.info(f"{conn_type}客户端已连接: {self.client_info}")
            
            # 发送欢迎消息
            welcome_msg = {
                "type": "welcome",
                "message": f"欢迎连接Dot_D1机器人({conn_type})",
                "robot_name": getattr(cof.ble, 'device_name', 'Dot_D1_Robot'),
                "connection_type": "bluetooth" if self.use_bluetooth else "network",
                "timestamp": time.time(),
                "commands_help": {
                    "move": {"x": "前后", "y": "左右", "z": "旋转"},
                    "button": {"1": "前进", "2": "后退", "3": "左移", "4": "右移", "7": "左转", "9": "右转"},
                    "stop": "停止所有运动",
                    "ping": "心跳包"
                }
            }
            self.client_sock.send((json.dumps(welcome_msg) + "\n").encode('utf-8'))
            
            # 接收指令循环
            buffer = ""
            while self.is_running:
                try:
                    # 接收数据
                    data = self.client_sock.recv(1024).decode('utf-8')
                    if not data:
                        logger.info("客户端断开连接")
                        break
                    
                    buffer += data
                    
                    # 处理完整的JSON消息（以换行符分隔）
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        if line.strip():
                            try:
                                command_data = json.loads(line.strip())
                                self.process_command(command_data)
                                self.last_command_time = time.time()
                                logger.debug(f"收到指令: {command_data}")
                                
                                # 发送确认
                                ack = {"type": "ack", "status": "ok", "timestamp": time.time()}
                                self.client_sock.send((json.dumps(ack) + "\n").encode('utf-8'))
                                
                            except json.JSONDecodeError as e:
                                logger.error(f"JSON解析错误: {e}")
                                error_msg = {"type": "error", "message": "JSON格式错误"}
                                self.client_sock.send((json.dumps(error_msg) + "\n").encode('utf-8'))
                
                except (ConnectionResetError, ConnectionAbortedError):
                    logger.info("客户端主动断开连接")
                    break
                except Exception as e:
                    logger.error(f"客户端处理错误: {e}")
                    break
        
        except Exception as e:
            logger.error(f"客户端连接处理错误: {e}")
        finally:
            # 断开连接时停止所有运动
            cof.commands[0] = 0.0
            cof.commands[1] = 0.0
            cof.commands[2] = 0.0
            
            if self.client_sock:
                try:
                    self.client_sock.close()
                except:
                    pass
                self.client_sock = None
                self.client_info = None
            
            logger.info("客户端连接已关闭")
    
    def heartbeat_monitor(self):
        """心跳监控线程"""
        while self.is_running:
            try:
                # 检查心跳超时
                if (self.client_sock and 
                    time.time() - self.last_command_time > self.heartbeat_timeout):
                    logger.warning("心跳超时，停止运动")
                    cof.commands[0] = 0.0
                    cof.commands[1] = 0.0
                    cof.commands[2] = 0.0
                
                time.sleep(0.5)  # 每500ms检查一次
            except Exception as e:
                logger.error(f"心跳监控错误: {e}")
                time.sleep(1.0)
    
    def status_broadcast_loop(self):
        """状态广播循环"""
        while self.is_running:
            try:
                if self.client_sock:
                    self.send_status()
                time.sleep(getattr(cof.ble, 'status_broadcast_interval', 0.5))
            except Exception as e:
                logger.error(f"状态广播错误: {e}")
                time.sleep(1.0)
    
    def start_server(self):
        """启动遥控服务器"""
        try:
            if not self.setup_server():
                return False
            
            self.is_running = True
            self.last_command_time = time.time()
            
            # 启动后台线程
            heartbeat_thread = threading.Thread(target=self.heartbeat_monitor, daemon=True)
            status_thread = threading.Thread(target=self.status_broadcast_loop, daemon=True)
            
            heartbeat_thread.start()
            status_thread.start()
            
            # 主循环 - 等待客户端连接
            while self.is_running:
                try:
                    conn_type = "蓝牙" if self.use_bluetooth else "网络"
                    logger.info(f"等待{conn_type}客户端连接...")
                    self.client_sock, self.client_info = self.server_sock.accept()
                    
                    # 处理客户端
                    self.handle_client()
                    
                except (ConnectionResetError, OSError) as e:
                    if self.is_running:
                        logger.error(f"连接错误: {e}")
                        time.sleep(1.0)
                except Exception as e:
                    logger.error(f"服务器运行错误: {e}")
                    time.sleep(1.0)
            
        except Exception as e:
            logger.error(f"遥控服务器启动失败: {e}")
            return False
        finally:
            self.stop_server()
        
        return True
    
    def stop_server(self):
        """停止遥控服务器"""
        logger.info("正在停止遥控服务器...")
        self.is_running = False
        
        # 停止所有运动
        cof.commands[0] = 0.0
        cof.commands[1] = 0.0
        cof.commands[2] = 0.0
        
        # 关闭连接
        if self.client_sock:
            try:
                self.client_sock.close()
            except:
                pass
        
        if self.server_sock:
            try:
                if self.use_bluetooth and BLUETOOTH_AVAILABLE:
                    bluetooth.stop_advertising(self.server_sock)
                self.server_sock.close()
            except:
                pass

# 全局遥控服务器实例
remote_server = RemoteControlServer()

def start_ble_server_thread():
    """在新线程中启动遥控服务器（用于与主程序集成）"""
    def run_server():
        try:
            remote_server.start_server()
        except Exception as e:
            logger.error(f"遥控服务器线程错误: {e}")
    
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    conn_type = "蓝牙" if remote_server.use_bluetooth else "网络"
    logger.info(f"{conn_type}遥控服务器线程已启动")
    return thread

def stop_ble_server():
    """停止遥控服务器"""
    remote_server.stop_server()

# 测试代码
if __name__ == "__main__":
    try:
        print("启动遥控服务器测试...")
        print(f"使用{'蓝牙' if remote_server.use_bluetooth else '网络'}连接")
        remote_server.start_server()
    except KeyboardInterrupt:
        print("\n用户中断，正在停止服务器...")
        remote_server.stop_server()
    except Exception as e:
        print(f"测试失败: {e}")