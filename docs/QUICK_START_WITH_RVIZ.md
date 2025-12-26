# LeGO-LOAM Quick Start with RViz Visualization

**Requirements:** Desktop Ubuntu with GUI and X11 server

---

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

Build the Docker image with RViz support:

```bash
cd /path/to/LeGO-LOAM
docker build -f Dockerfile.ros -t lego-loam:melodic .
```

Wait ~10-15 minutes for completion.

**Enable X11 forwarding:**

```bash
xhost +local:docker
```

(You only need to run this once per login session)

---

## Step 2: Running LeGO-LOAM with Visualization

You need **3 terminals**.

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

### Terminal 2: Launch RViz

Open a second terminal:

```bash
docker exec -it lego-loam bash -c "source /opt/ros/melodic/setup.bash && source /catkin_ws/devel/setup.bash && rviz -d /workspace/LeGO-LOAM/launch/test.rviz"
```

An RViz window will open. **Leave this running.**

---

### Terminal 3: Play Bag File

Open a third terminal:

```bash
docker exec -it lego-loam bash -c "source /opt/ros/melodic/setup.bash && rosbag play /workspace/data/2017-06-08-15-52-45_3.bag --clock"
```

Replace the bag path with your own file if needed.

---

## What You'll See in RViz

- **Point Clouds**: Raw input, ground points, segmented clouds
- **Odometry Path**: Real-time trajectory (orange/red lines)
- **Map**: Accumulated registered point cloud map
- **TF Frames**: Coordinate transformations

The visualization updates in real-time as the bag plays!

---

## Troubleshooting

### "cannot open display"
```bash
# Run on host machine
xhost +local:docker
echo $DISPLAY  # Should output something like :0 or :1
```

### RViz crashes or freezes
- Point cloud data is heavy - processing might be slow
- Reduce bag playback rate: `rosbag play ... --clock --rate 0.5`

### Black screen in RViz
- Wait a few seconds for topics to start publishing
- Check topics are publishing: `rostopic list`

---

## Stop Everything

Press `Ctrl+C` in all three terminals.

To disable X11 forwarding:
```bash
xhost -local:docker
```
