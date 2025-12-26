#!/bin/bash
# LeGO-LOAM Test Script - Run inside Docker container

echo "=== LeGO-LOAM Test Runner ==="
echo ""

# Source ROS
source /opt/ros/melodic/setup.bash
source /catkin_ws/devel/setup.bash

# Set simulated time
rosparam set use_sim_time true

# Start roscore in background
echo "[1/4] Starting roscore..."
roscore &
sleep 3

# Start bag playback PAUSED in background
echo "[2/4] Starting bag (paused)..."
rosbag play /workspace/data/2017-06-08-15-52-45_3.bag --clock --pause --loop --topic /velodyne_points /imu/data &
BAG_PID=$!
sleep 2

# Launch LeGO-LOAM nodes (without roscore since it's already running)
echo "[3/4] Starting LeGO-LOAM nodes..."
roslaunch lego_loam run.launch --wait &
LOAM_PID=$!
sleep 3

echo ""
echo "[4/4] LeGO-LOAM ready! Press SPACE in this terminal to start bag playback..."
echo "      Or press Ctrl+C to stop everything."
echo ""

# Wait for user to unpause (bring bag to foreground)
wait $BAG_PID
