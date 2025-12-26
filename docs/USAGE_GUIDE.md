# LeGO-LOAM Usage Guide

This guide provides complete instructions for running LeGO-LOAM using Docker. Tested on Ubuntu 24.04 with Docker containerization for ROS Melodic compatibility.

---

## Prerequisites

- **Docker** installed and running
- **Bag file** with Velodyne VLP-16 data (or compatible LiDAR)
- Recommended: 4+ CPU cores, 8GB+ RAM

---

## Quick Start (One Command)

```bash
docker run -it --rm --name lego-loam-test \
  -v /workspaces/LeGO-LOAM:/workspace \
  -w /catkin_ws lego-loam:melodic bash -c "
source /opt/ros/melodic/setup.bash && \
ln -sf /workspace/LeGO-LOAM /catkin_ws/src/ && \
ln -sf /workspace/cloud_msgs /catkin_ws/src/ && \
catkin_make && \
source devel/setup.bash && \
roslaunch lego_loam run.launch &
sleep 5 && \
rosbag play /workspace/data/2017-06-08-15-52-45_3.bag --clock
"
```

---

## Full Setup Guide

### Step 1: Build Docker Image (First Time Only)

```bash
cd /workspaces/LeGO-LOAM
docker build -f Dockerfile.ros -t lego-loam:melodic .
```

This takes ~10-15 minutes and includes:
- ROS Melodic (Ubuntu 18.04)
- PCL 1.8
- GTSAM 4.0.0-alpha2
- All LeGO-LOAM dependencies

### Step 2: Verify Image

```bash
docker images | grep lego-loam
```

Expected output:
```
lego-loam    melodic    8de7f029e5c1   X minutes ago   4.57GB
```

---

## Running LeGO-LOAM

### Method 1: Single Command (Recommended)

```bash
docker run -it --rm --name lego-loam-test \
  -v $(pwd):/workspace \
  -w /catkin_ws lego-loam:melodic bash -c "
source /opt/ros/melodic/setup.bash && \
ln -sf /workspace/LeGO-LOAM /catkin_ws/src/ && \
ln -sf /workspace/cloud_msgs /catkin_ws/src/ && \
catkin_make && \
source devel/setup.bash && \
roslaunch lego_loam run.launch &
sleep 5 && \
rosbag play /workspace/data/YOUR_BAG_FILE.bag --clock
"
```

### Method 2: Interactive Session (For Development)

**Terminal 1 - Start Container:**
```bash
docker run -it --rm --name lego-loam-dev \
  -v $(pwd):/workspace \
  -w /catkin_ws lego-loam:melodic bash
```

**Inside Container:**
```bash
# Setup workspace
source /opt/ros/melodic/setup.bash
ln -sf /workspace/LeGO-LOAM /catkin_ws/src/
ln -sf /workspace/cloud_msgs /catkin_ws/src/

# Build
catkin_make

# Source and launch
source devel/setup.bash
roslaunch lego_loam run.launch
```

**Terminal 2 - Play Bag File:**
```bash
docker exec -it lego-loam-dev bash -c "
source /opt/ros/melodic/setup.bash && \
rosbag play /workspace/data/YOUR_BAG_FILE.bag --clock --loop
"
```

---

## Sensor Configuration

Edit `LeGO-LOAM/include/utility.h` before building:

### VLP-16 (Default)
```cpp
extern const int N_SCAN = 16;
extern const int Horizon_SCAN = 1800;
extern const float ang_res_x = 0.2;
extern const float ang_res_y = 2.0;
extern const float ang_bottom = 15.0+0.1;
extern const int groundScanInd = 7;
```

### HDL-32E
```cpp
extern const int N_SCAN = 32;
extern const int Horizon_SCAN = 1800;
extern const float ang_res_x = 360.0/float(Horizon_SCAN);
extern const float ang_res_y = 41.33/float(N_SCAN-1);
extern const float ang_bottom = 30.67;
extern const int groundScanInd = 20;
```

### HDL-64E
```cpp
extern const int N_SCAN = 64;
extern const int Horizon_SCAN = 1800;
extern const float ang_res_x = 0.2;
extern const float ang_res_y = 0.427;
extern const float ang_bottom = 24.9;
extern const int groundScanInd = 50;
```

### Cloud Ring Setting
If your point cloud does NOT have a "ring" channel:
```cpp
extern const bool useCloudRing = false;
```

---

## Topic Configuration

Default topics in `utility.h`:
```cpp
extern const string pointCloudTopic = "/velodyne_points";
extern const string imuTopic = "/imu/data";
```

Change these to match your bag file topics.

---

## Output Topics

| Topic | Description |
|-------|-------------|
| `/aft_mapped_to_init` | Final odometry (nav_msgs/Odometry) |
| `/laser_odom_to_init` | Laser odometry |
| `/integrated_to_init` | IMU-integrated odometry |
| `/registered_cloud` | Registered point cloud map |
| `/segmented_cloud` | Segmented point cloud |
| `/ground_cloud` | Ground points |
| `/full_cloud_projected` | Full projected cloud |

---

## Checking Output

While running, verify data flow:

```bash
# Check odometry output
docker exec -it lego-loam-dev bash -c "
source /opt/ros/melodic/setup.bash && \
rostopic echo /aft_mapped_to_init -n 1
"

# Check topic rates
docker exec -it lego-loam-dev bash -c "
source /opt/ros/melodic/setup.bash && \
rostopic hz /velodyne_points /segmented_cloud /aft_mapped_to_init
"

# List all topics
docker exec -it lego-loam-dev bash -c "
source /opt/ros/melodic/setup.bash && \
rostopic list
"
```

---

## Saving Output

### Save Map to PCD
Maps are automatically saved to `/tmp/` inside the container. To copy out:

```bash
docker cp lego-loam-dev:/tmp/cornerMap.pcd ./output/
docker cp lego-loam-dev:/tmp/surfaceMap.pcd ./output/
docker cp lego-loam-dev:/tmp/trajectoryCloud.pcd ./output/
```

### Record Topics to Bag
```bash
docker exec -it lego-loam-dev bash -c "
source /opt/ros/melodic/setup.bash && \
rosbag record -O /workspace/output/lego_loam_output.bag \
  /aft_mapped_to_init \
  /laser_odom_to_init \
  /registered_cloud
"
```

---

## Troubleshooting

### "no messages received and simulated time is active"
- Start the bag file BEFORE or immediately after launching LeGO-LOAM
- Ensure `use_sim_time` is set to `true` in launch file
- Verify bag has `/clock` topic when using `--clock` flag

### No processing output
- LeGO-LOAM processes silently by default
- Check output topics: `rostopic hz /segmented_cloud`
- Add debug output to `imageProjection.cpp` if needed

### Point cloud not processed
- Check topic name matches `pointCloudTopic` in utility.h
- Verify sensor configuration (N_SCAN, Horizon_SCAN) matches your LiDAR
- Set `useCloudRing = false` if cloud lacks ring channel

### Container issues
```bash
# Stop and remove container
docker stop lego-loam-dev 2>/dev/null
docker rm lego-loam-dev 2>/dev/null

# Check running containers
docker ps -a
```

---

## File Structure

```
LeGO-LOAM/
├── Dockerfile.ros          # Docker build configuration
├── USAGE_GUIDE.md          # This guide
├── cloud_msgs/             # Custom message definitions
│   └── msg/cloud_info.msg
├── LeGO-LOAM/
│   ├── include/utility.h   # Sensor configuration
│   ├── launch/run.launch   # Launch file
│   └── src/
│       ├── imageProjection.cpp
│       ├── featureAssociation.cpp
│       ├── mapOptmization.cpp
│       └── transformFusion.cpp
└── data/                   # Bag files (user provided)
    └── *.bag
```

---

## Pipeline Overview

1. **imageProjection**: Projects point cloud to range image, segments ground
2. **featureAssociation**: Extracts edge/planar features, scan-to-scan matching
3. **mapOptmization**: Scan-to-map matching, loop closure with GTSAM
4. **transformFusion**: Fuses odometry from different sources

---

## Performance Tips

- Use `--clock` flag when playing bags for proper time synchronization
- For large bags, consider playing at slower rate: `rosbag play --rate 0.5`
- Monitor CPU usage with `htop` - LeGO-LOAM is CPU intensive
- Increase Docker memory limit if processing stalls

---

## Example Commands

### Run with loop playback
```bash
rosbag play /workspace/data/test.bag --clock --loop
```

### Run at half speed
```bash
rosbag play /workspace/data/test.bag --clock --rate 0.5
```

### Skip first 10 seconds
```bash
rosbag play /workspace/data/test.bag --clock --start 10
```

---

## Version Information

- **ROS**: Melodic
- **PCL**: 1.8
- **GTSAM**: 4.0.0-alpha2
- **OpenCV**: 3.2
- **Ubuntu**: 18.04 (inside Docker)

---

## License

BSD License - See LICENSE file
