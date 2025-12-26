# LeGO-LOAM Quick Start Guide

## Step 0: Install Docker (Fresh Ubuntu Only)

Skip this if Docker is already installed.

```bash
# Install Docker
sudo apt update
sudo apt install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker

# Add yourself to docker group (avoids needing sudo)
sudo usermod -aG docker $USER
newgrp docker
```

---

## Step 1: First Time Setup (Run Once)

Build the Docker image:

```bash
cd /workspaces/LeGO-LOAM
docker build -f Dockerfile.ros -t lego-loam:melodic .
```

Wait ~10-15 minutes for completion.

**Enable X11 forwarding for RViz:**

```bash
xhost +local:docker
```

---

## Step 2: Running LeGO-LOAM

You need **2-3 terminals**.

### Terminal 1: Start LeGO-LOAM

```bash
# Enter the Docker container with X11 forwarding
docker run -it --rm --name lego-loam \
  -v $(pwd):/workspace \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -e DISPLAY=$DISPLAY \
  -w /catkin_ws lego-loam:melodic bash
```

Inside the container, run:

```bash
source /opt/ros/melodic/setup.bash
ln -sf /workspace/LeGO-LOAM /catkin_ws/src/
ln -sf /workspace/cloud_msgs /catkin_ws/src/
catkin_make
source devel/setup.bash
roslaunch lego_loam run.launch
```

You should see:
```
----> Image Projection Started.
----> Feature Association Started.
----> Map Optimization Started.
----> Transform Fusion Started.
```

**Leave this terminal running.**

---

### Terminal 2: Play Bag File

Open a new terminal, then:

```bash
docker exec -it lego-loam bash -c "source /opt/ros/melodic/setup.bash && rosbag play /workspace/data/2017-06-08-15-52-45_3.bag --clock"
```

Replace the bag path with your own file if needed.

---

### Terminal 3: Launch RViz (Optional)

Open a third terminal for visualization:

```bash
docker exec -it lego-loam bash -c "source /opt/ros/melodic/setup.bash && source /catkin_ws/devel/setup.bash && rviz -d /workspace/LeGO-LOAM/launch/test.rviz"
```

You should see the RViz window with point clouds and odometry visualization.

---

## Done!

LeGO-LOAM is now processing your data. Watch Terminal 1 for output.

To stop: Press `Ctrl+C` in both terminals.
