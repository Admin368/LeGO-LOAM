docker run -it --rm --name lego-loam-test -v /workspaces/LeGO-LOAM:/workspace -w /catkin_ws lego-loam:melodic bash -c "
source /opt/ros/melodic/setup.bash && \
ln -sf /workspace/LeGO-LOAM /catkin_ws/src/ && \
ln -sf /workspace/cloud_msgs /catkin_ws/src/ && \
catkin_make && \                              
source devel/setup.bash && \
roslaunch lego_loam run.launch &
sleep 5 && \
rosbag play /workspace/data/2017-06-08-15-52-45_3.bag --clock --loop
"