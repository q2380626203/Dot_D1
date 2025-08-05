#!/usr/bin/env python3
"""
纯BLE GATT服务器 - 强制只使用BLE低功耗蓝牙
直接控制蓝牙适配器，确保只启用BLE模式
"""

import asyncio
import json
import logging
import time
import threading
import subprocess
import sys
from typing import Dict, Any

try:
    from bluez_peripheral.gatt.service import Service
    from bluez_peripheral.gatt.characteristic import characteristic, CharacteristicFlags as CharFlags
    from bluez_peripheral.advert import Advertisement
    from bluez_peripheral.agent import NoIoAgent
    from bluez_peripheral.util import *
    BLE_AVAILABLE = True
    print("✓ BLE GATT库可用")
except ImportError as e:
    BLE_AVAILABLE = False
    print(f"✗ BLE GATT库不可用: {e}")
    print("请安装: pip3 install bluez-peripheral")

import Dot_D1_config as cof

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_command(cmd, use_sudo=False, timeout=10):
    """执行系统命令"""
    try:
        if use_sudo:
            cmd = f"echo 1234 | sudo -S {cmd}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "Command timeout"
    except Exception as e:
        return False, "", str(e)

def force_ble_only_mode():
    """强制设置蓝牙为BLE专用模式"""
    print("=== 强制BLE专用模式设置 ===")
    
    # 1. 停止bluetoothd服务
    print("1. 停止蓝牙服务...")
    success, out, err = run_command("systemctl stop bluetooth", use_sudo=True)
    if success:
        print("  ✓ 蓝牙服务已停止")
    
    time.sleep(2)
    
    # 2. 重置蓝牙适配器
    print("2. 重置蓝牙适配器...")
    run_command("hciconfig hci0 down", use_sudo=True)
    time.sleep(1)
    
    success, out, err = run_command("hciconfig hci0 up", use_sudo=True)
    if not success:
        print(f"  ✗ 蓝牙适配器启动失败: {err}")
        # 尝试解除rfkill
        run_command("rfkill unblock bluetooth", use_sudo=True)
        time.sleep(1)
        success, out, err = run_command("hciconfig hci0 up", use_sudo=True)
    
    if success:
        print("  ✓ 蓝牙适配器已启动")
    else:
        print(f"  ✗ 蓝牙适配器仍然无法启动: {err}")
        return False
    
    # 3. 启动bluetoothd (BLE专用模式)
    print("3. 启动BLE专用蓝牙服务...")
    ble_cmd = "/usr/lib/bluetooth/bluetoothd --noplugin=a2dp,avrcp,network,input,hog,audio,autopair,policy,sap,avctp,avdtp --experimental"
    
    # 后台启动bluetoothd
    success, out, err = run_command(f"nohup {ble_cmd} > /tmp/bluetoothd.log 2>&1 &", use_sudo=True)
    time.sleep(3)
    
    # 验证bluetoothd是否运行
    success, out, err = run_command("pgrep bluetoothd")
    if success:
        print("  ✓ BLE专用蓝牙服务已启动")
    else:
        print("  ✗ BLE专用蓝牙服务启动失败")
        return False
    
    # 4. 等待D-Bus接口就绪
    print("4. 等待蓝牙接口就绪...")
    for i in range(10):
        success, out, err = run_command("bluetoothctl show", timeout=5)
        if success and "Controller" in out:
            print("  ✓ 蓝牙接口就绪")
            break
        time.sleep(1)
    else:
        print("  ⚠ 蓝牙接口可能未完全就绪")
    
    # 5. 设置蓝牙为可发现
    print("5. 设置蓝牙为可发现...")
    run_command("bluetoothctl power on", timeout=5)
    run_command("bluetoothctl discoverable on", timeout=5)
    
    print("=== BLE专用模式设置完成 ===\n")
    return True

class Dot_D1_BLE_Service(Service):
    """Dot_D1机器人BLE GATT服务"""
    
    def __init__(self):
        # 定义服务UUID
        self.service_uuid = "12345678-1234-1234-1234-123456789abc"
        super().__init__(self.service_uuid, True)
        
        self.last_command_time = time.time()
        self.heartbeat_timeout = 2.0
        
        # 遥控参数
        self.run_speed = getattr(cof.ble, 'speed_limit', 0.2)
        self.center_subtle = getattr(cof.ble, 'center_adjust_step', 0.001)
        
        logger.info("BLE GATT服务初始化完成")
    
    @characteristic("87654321-4321-4321-4321-cba987654321", CharFlags.WRITE)
    def command_char(self, options):
        """接收控制指令的特征值"""
        def write_callback(value, offset):
            try:
                command_str = bytes(value).decode('utf-8')
                command_data = json.loads(command_str)
                self.process_command(command_data)
                self.last_command_time = time.time()
                logger.info(f"收到BLE指令: {command_data}")
                print(f">>> 收到指令: {command_data}")
            except Exception as e:
                logger.error(f"BLE指令处理错误: {e}")
        
        return write_callback
    
    @characteristic("11111111-2222-3333-4444-555555555555", CharFlags.READ | CharFlags.NOTIFY)
    def status_char(self, options):
        """发送状态信息的特征值"""
        def read_callback(offset):
            try:
                status_data = {
                    "type": "status",
                    "timestamp": time.time(),
                    "commands": cof.commands.copy(),
                    "center_x": getattr(cof, 'center_x', 0.0),
                    "motor_angle_exceed": getattr(cof.real, 'motor_angle_exceed', 0),
                    "imu_angle_exceed": getattr(cof.real, 'imu_angle_exceed', 0),
                    "connection_type": "ble_only"
                }
                
                status_json = json.dumps(status_data)
                return status_json.encode('utf-8')
            except Exception as e:
                logger.error(f"状态生成错误: {e}")
                return b'{"error":"status_error"}'
        
        return read_callback
    
    def process_command(self, command_data: Dict[str, Any]):
        """处理BLE控制指令"""
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
                
                print(f">>> 运动指令: x={x_vel}, y={y_vel}, z={z_vel}")
                
            elif cmd_type == "button":
                # 按键指令（兼容现有433MHz遥控器功能）
                button = command_data.get("button", 0)
                self.process_button_command(button)
                print(f">>> 按键指令: button={button}")
                
            elif cmd_type == "center_adjust":
                # 重心调节
                adjust = command_data.get("adjust", 0.0)
                if adjust > 0:
                    cof.center_x += self.center_subtle
                elif adjust < 0:
                    cof.center_x -= self.center_subtle
                print(f">>> 重心调节: adjust={adjust}, center_x={cof.center_x}")
                    
            elif cmd_type == "stop":
                # 停止所有运动
                cof.commands[0] = 0.0
                cof.commands[1] = 0.0
                cof.commands[2] = 0.0
                print(">>> 停止指令")
                
            elif cmd_type == "ping":
                # 心跳包
                print(">>> 心跳包")
                pass
                
        except Exception as e:
            logger.error(f"BLE指令处理错误: {e}")
    
    def process_button_command(self, button: int):
        """处理按键指令（兼容433MHz遥控器）"""
        if button == 1:      # 前进
            cof.commands[0] = self.run_speed
            print("  -> 前进")
        elif button == 2:    # 后退
            cof.commands[0] = -self.run_speed
            print("  -> 后退")
        elif button == 3:    # 左移
            cof.commands[1] = self.run_speed
            print("  -> 左移")
        elif button == 4:    # 右移
            cof.commands[1] = -self.run_speed
            print("  -> 右移")
        elif button == 7:    # 左转
            cof.commands[2] = -(2*self.run_speed)
            print("  -> 左转")
        elif button == 9:    # 右转
            cof.commands[2] = (2*self.run_speed)
            print("  -> 右转")
        elif button == 5:    # 重心微调
            cof.center_x += self.center_subtle
            print(f"  -> 重心微调: {cof.center_x}")
        else:                # 停止
            cof.commands[0] = 0.0
            cof.commands[1] = 0.0
            cof.commands[2] = 0.0
            print("  -> 停止")

class BLE_Only_Server:
    """纯BLE服务器管理类"""
    
    def __init__(self):
        self.service = None
        self.advertisement = None
        self.is_running = False
        
    async def setup_ble_server(self):
        """设置BLE服务器"""
        max_retries = 3
        retry_delay = 2.0
        
        for attempt in range(max_retries):
            try:
                if not BLE_AVAILABLE:
                    raise ImportError("BLE库不可用")
                
                logger.info(f"BLE服务器设置尝试 {attempt + 1}/{max_retries}")
                
                # 添加初始化延迟，等待蓝牙服务稳定
                if attempt > 0:
                    logger.info(f"等待 {retry_delay} 秒后重试...")
                    await asyncio.sleep(retry_delay)
                
                # 创建服务
                self.service = Dot_D1_BLE_Service()
                await asyncio.sleep(0.5)  # 让服务创建完成
                
                # 创建广告 - 强制BLE模式
                self.advertisement = Advertisement(
                    localName="Dot_D1_Robot",
                    serviceUUIDs=[self.service.service_uuid],
                    appearance=0x0000,  # 通用设备
                    timeout=0  # 永不超时
                )
                await asyncio.sleep(0.5)  # 让广告创建完成
                
                logger.info("BLE服务器设置完成")
                return True
                
            except Exception as e:
                logger.error(f"BLE服务器设置失败 (尝试 {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    logger.error("所有重试均失败，BLE服务器设置失败")
                    return False
                
                # 清理失败的对象
                self.service = None
                self.advertisement = None
                
        return False
    
    async def start_server(self):
        """启动BLE服务器"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                logger.info(f"BLE服务器启动尝试 {attempt + 1}/{max_retries}")
                
                if not await self.setup_ble_server():
                    if attempt < max_retries - 1:
                        logger.warning("BLE服务器设置失败，准备重试...")
                        await asyncio.sleep(3.0)
                        continue
                    return False
                
                self.is_running = True
                
                print("✓ 纯BLE GATT服务器已启动")
                print(f"  设备名: Dot_D1_Robot")
                print(f"  服务UUID: {self.service.service_uuid}")
                print(f"  指令特征值: 87654321-4321-4321-4321-cba987654321")
                print(f"  状态特征值: 11111111-2222-3333-4444-555555555555")
                print("  >>> 等待BLE客户端连接...")
                
                # 启动代理和服务
                agent = NoIoAgent()
                
                # 获取D-Bus连接，添加重试机制
                bus = None
                for bus_attempt in range(3):
                    try:
                        bus = await get_message_bus()
                        break
                    except Exception as bus_e:
                        logger.warning(f"D-Bus连接失败 (尝试 {bus_attempt + 1}): {bus_e}")
                        if bus_attempt < 2:
                            await asyncio.sleep(1.0)
                        else:
                            raise
                
                # 注册服务和广告，添加延迟
                await asyncio.sleep(1.0)  # 等待D-Bus连接稳定
                await self.service.register(bus)
                await asyncio.sleep(0.5)  # 服务注册间隔
                await self.advertisement.register(bus)
                
                logger.info("BLE服务已注册并开始广告")
                print("  >>> BLE广告已激活，现在可以搜索到设备")
                
                # 启动心跳监控
                asyncio.create_task(self.heartbeat_monitor())
                
                # 保持服务器运行
                while self.is_running:
                    await asyncio.sleep(1)
                
                return True
                
            except Exception as e:
                logger.error(f"BLE服务器启动失败 (尝试 {attempt + 1}): {e}")
                await self.stop_server()
                
                if attempt < max_retries - 1:
                    logger.info(f"等待 5 秒后重试...")
                    await asyncio.sleep(5.0)
                else:
                    logger.error("所有重试均失败，BLE服务器启动失败")
                    return False
        
        return False
    
    async def heartbeat_monitor(self):
        """心跳监控"""
        while self.is_running:
            try:
                # 检查心跳超时
                if (time.time() - self.service.last_command_time > self.service.heartbeat_timeout):
                    # 超时时自动停止运动
                    if any(cmd != 0 for cmd in cof.commands):
                        logger.warning("BLE心跳超时，停止运动")
                        cof.commands[0] = 0.0
                        cof.commands[1] = 0.0
                        cof.commands[2] = 0.0
                        print(">>> 心跳超时，自动停止")
                
                await asyncio.sleep(0.5)  # 每500ms检查一次
            except Exception as e:
                logger.error(f"BLE心跳监控错误: {e}")
                await asyncio.sleep(1.0)
    
    async def stop_server(self):
        """停止BLE服务器"""
        logger.info("正在停止BLE服务器...")
        self.is_running = False
        
        # 安全地注销服务和广告
        unregister_tasks = []
        
        try:
            if self.advertisement:
                unregister_tasks.append(self.advertisement.unregister())
            if self.service:
                unregister_tasks.append(self.service.unregister())
            
            if unregister_tasks:
                # 并行执行注销，设置超时
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*unregister_tasks, return_exceptions=True),
                        timeout=5.0
                    )
                except asyncio.TimeoutError:
                    logger.warning("BLE服务注销超时")
                
        except Exception as e:
            logger.warning(f"BLE服务注销时出现错误: {e}")
        finally:
            # 清理对象引用
            self.advertisement = None
            self.service = None
        
        # 停止所有运动
        cof.commands[0] = 0.0
        cof.commands[1] = 0.0
        cof.commands[2] = 0.0
        
        logger.info("BLE服务器已停止")

# 全局BLE服务器实例
ble_only_server = BLE_Only_Server()

def start_ble_only_server_thread():
    """在新线程中启动纯BLE GATT服务器"""
    def run_server():
        try:
            # 首先强制设置BLE专用模式
            if not force_ble_only_mode():
                logger.error("BLE专用模式设置失败")
                return
            
            # 创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 运行BLE服务器
            loop.run_until_complete(ble_only_server.start_server())
        except Exception as e:
            logger.error(f"BLE服务器线程错误: {e}")
    
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    logger.info("BLE专用GATT服务器线程已启动")
    return thread

def stop_ble_only_server():
    """停止纯BLE GATT服务器"""
    asyncio.create_task(ble_only_server.stop_server())

# 测试代码
if __name__ == "__main__":
    async def main():
        try:
            print("启动纯BLE GATT服务器...")
            
            # 强制设置BLE专用模式
            if not force_ble_only_mode():
                print("❌ BLE专用模式设置失败")
                return
            
            # 启动BLE服务器
            await ble_only_server.start_server()
            
        except KeyboardInterrupt:
            print("\n用户中断，正在停止服务器...")
            await ble_only_server.stop_server()
        except Exception as e:
            print(f"测试失败: {e}")
            logger.error(f"服务器启动错误: {e}")
    
    # 运行测试
    if BLE_AVAILABLE:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("\n程序已退出")
    else:
        print("❌ BLE库不可用，无法启动GATT服务器")
        print("请安装: pip3 install bluez-peripheral")