
#!/bin/bash


sleep 5

echo "===== 配置CPU性能模式 ====="
echo "1234" | sudo -S cpufreq-set -c 0 -g performance
echo "1234" | sudo -S cpufreq-set -c 1 -g performance
echo "1234" | sudo -S cpufreq-set -c 2 -g performance
echo "1234" | sudo -S cpufreq-set -c 3 -g performance

echo "===== 初始化蓝牙BLE ====="
# 解除蓝牙rfkill阻塞
echo "1234" | sudo -S rfkill unblock bluetooth
sleep 1

# 启动蓝牙适配器
echo "1234" | sudo -S hciconfig hci0 up
sleep 2

# 验证蓝牙状态
echo "检查蓝牙适配器状态:"
hciconfig hci0 | head -3

# 检查蓝牙服务状态
echo "检查蓝牙服务状态:"
systemctl is-active bluetooth

echo "===== 配置串口和CAN总线 ====="
echo "1234" | sudo -S chmod 777 /dev/ttyUSB0
echo "1234" | sudo -S ip link set down can0
echo "1234" | sudo -S ip link set can0 type can bitrate 1000000 loopback off
echo "1234" | sudo -S ip link set up can0

echo "1234" | sudo -S ip link set down can1
echo "1234" | sudo -S ip link set can1 type can bitrate 1000000 loopback off
echo "1234" | sudo -S ip link set up can1

echo "检查CAN总线状态:"
ip link show can0 | head -1
ip link show can1 | head -1

#python3 /home/cw/Dot_D1/ps2_demo.py

echo "===== 启动Dot_D1机器人程序 ====="
cd /home/ub/Dot_D1/
python3 Dot_D1_run.py