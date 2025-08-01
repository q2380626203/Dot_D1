#!/bin/bash

sleep 5

echo "1234" | sudo -S cpufreq-set -c 0 -g performance
echo "1234" | sudo -S cpufreq-set -c 1 -g performance
echo "1234" | sudo -S cpufreq-set -c 2 -g performance
echo "1234" | sudo -S cpufreq-set -c 3 -g performance

echo "1234" | sudo -S chmod 777 /dev/ttyUSB0
echo "1234" | sudo -S ip link set down can0
echo "1234" | sudo -S ip link set can0 type can bitrate 1000000 loopback off
echo "1234" | sudo -S ip link set up can0

echo "1234" | sudo -S ip link set down can1
echo "1234" | sudo -S ip link set can1 type can bitrate 1000000 loopback off
echo "1234" | sudo -S ip link set up can1

cd /home/ub/Dot_D1/
python3 motor_disable_all.py