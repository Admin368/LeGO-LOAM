#!/bin/bash
# Script to build and run LeGO-LOAM in Docker

set -e

echo "Building Docker image with ROS Noetic and dependencies..."
docker build -f Dockerfile.ros -t lego-loam:noetic .

echo "Starting Docker container..."
docker run -it --rm \
    --name lego-loam-container \
    -v /workspaces/LeGO-LOAM:/workspace \
    -w /catkin_ws \
    lego-loam:noetic \
    bash -c "
        set -e
        echo '=== Setting up catkin workspace ==='
        source /opt/ros/noetic/setup.bash
        
        # Link packages to catkin workspace
        ln -sf /workspace/LeGO-LOAM /catkin_ws/src/
        ln -sf /workspace/cloud_msgs /catkin_ws/src/
        
        echo '=== Building LeGO-LOAM ==='
        catkin_make -j2
        
        echo '=== Sourcing workspace ==='
        source devel/setup.bash
        
        echo ''
        echo '✅ LeGO-LOAM build complete!'
        echo ''
        echo 'To run LeGO-LOAM:'
        echo '  roslaunch lego_loam run.launch'
        echo ''
        echo 'To play your bag file (in another terminal):'
        echo '  rosbag play /workspace/data/2017-06-08-15-52-45_3.bag --clock --topic /velodyne_points /imu/data'
        echo ''
        
        # Keep container running
        exec bash
    "
