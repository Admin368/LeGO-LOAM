# LeGO-LOAM Setup Progress Tracker

**Date Started:** December 26, 2025  
**Environment:** Ubuntu 24.04.3 LTS (Dev Container)  
**Goal:** Get LeGO-LOAM running with sample bag data before making any modifications

---

## Environment Information
- **Bag File:** `data/2017-06-08-15-52-45_3.bag` (226 MB) ✓
- **ROS Version Needed:** ROS 1 (Noetic recommended for Ubuntu 20.04, but need compatibility solution for 24.04)
- **GTSAM Version:** 4.0.0-alpha2 required

---

## Setup Steps

### Phase 1: Environment Setup

#### ☐ Step 1: ROS Installation
**Status:** Not Started  
**Goal:** Install ROS 1 (Noetic) or find compatibility solution for Ubuntu 24.04

**Options:**
- Option A: Install ROS Noetic from source (Ubuntu 24.04 not officially supported)
- Option B: Use Docker container with ROS Noetic
- Option C: Try ROS 2 bridge (complex, not recommended)

**Commands:**
```bash
# To be determined based on chosen approach
```

**Notes:**
- LeGO-LOAM requires ROS 1 (catkin build system)
- Ubuntu 24.04 officially supports ROS 2 Jazzy, not ROS 1
- Need to verify best compatibility approach

---

#### ✅ Step 2: Install GTSAM 4.0.0-alpha2
**Status:** COMPLETED  
**Goal:** Install Georgia Tech Smoothing and Mapping library (version 4.0.0-alpha2 specifically)

**Commands:**
```bash
wget -O ~/Downloads/gtsam.zip https://github.com/borglab/gtsam/archive/4.0.0-alpha2.zip
cd ~/Downloads/ && unzip gtsam.zip -d ~/Downloads/
cd ~/Downloads/gtsam-4.0.0-alpha2/
mkdir build && cd build
cmake ..
sudo make install
```

**Notes:**
- Specific version required (4.0.0-alpha2)
- Build dependencies: cmake, boost
- Installation location: typically /usr/local/lib

---

#### ☐ Step 3: Install PCL and OpenCV Dependencies
**Status:** Not Started  
**Goal:** Install Point Cloud Library and OpenCV

**Commands:**
```bash
sudo apt-get update
sudo apt-get install -y \
  libpcl-dev \
  libopencv-dev \
  libeigen3-dev \
  libboost-all-dev
```

**Notes:**
- PCL: Point cloud processing
- OpenCV: Image operations for range image projection
- Eigen3: Linear algebra
- Boost: Various utilities

---

### Phase 2: Workspace Setup

#### ☐ Step 4: Setup Catkin Workspace
**Status:** Not Started  
**Goal:** Create proper ROS catkin workspace structure

**Current Structure:**
```
/workspaces/LeGO-LOAM/
├── LeGO-LOAM/
├── cloud_msgs/
└── data/
```

**Target Structure:**
```
~/catkin_ws/
├── src/
│   ├── LeGO-LOAM/
│   └── cloud_msgs/
├── build/
└── devel/
```

**Commands:**
```bash
mkdir -p ~/catkin_ws/src
cd ~/catkin_ws/src
# Link or move LeGO-LOAM packages here
```

**Notes:**
- Standard ROS workspace structure
- Source code goes in src/
- Build artifacts in build/ and devel/

---

#### ☐ Step 5: Build LeGO-LOAM
**Status:** Not Started  
**Goal:** Compile the package using catkin_make

**Commands:**
```bash
cd ~/catkin_ws
catkin_make -j1  # First time requires -j1
source devel/setup.bash
```

**Notes:**
- `-j1` flag required for first build (generates message types)
- Subsequent builds can use `catkin_make` without flag
- Must source setup.bash after building

---

### Phase 3: Configuration & Testing

#### ☐ Step 6: Verify Launch Files
**Status:** Not Started  
**Goal:** Check and configure launch files for bag playback

**Files to Check:**
- `LeGO-LOAM/launch/run.launch`
- Verify `/use_sim_time` parameter is set to "true"

**Notes:**
- `/use_sim_time = true`: For bag file playback
- `/use_sim_time = false`: For real robot
- Topics: `/velodyne_points`, `/imu/data`

---

#### ☐ Step 7: Launch LeGO-LOAM
**Status:** Not Started  
**Goal:** Start all four nodes

**Commands:**
```bash
source ~/catkin_ws/devel/setup.bash
roslaunch lego_loam run.launch
```

**Expected Nodes:**
1. imageProjection
2. featureAssociation  
3. mapOptmization
4. transformFusion

**Notes:**
- All nodes should start without errors
- Check for topic connections
- Monitor console output

---

#### ☐ Step 8: Play Bag File
**Status:** Not Started  
**Goal:** Test system with recorded data

**Commands:**
```bash
# In new terminal:
source ~/catkin_ws/devel/setup.bash
rosbag play /workspaces/LeGO-LOAM/data/2017-06-08-15-52-45_3.bag --clock --topic /velodyne_points /imu/data
```

**Notes:**
- `--clock` flag: Publishes simulation time
- Topics: velodyne_points (required), imu/data (optional but improves accuracy)
- Expected: Real-time odometry and mapping output

---

#### ☐ Step 9: Visualize in RViz (Optional)
**Status:** Not Started  
**Goal:** Visualize mapping results

**Commands:**
```bash
# In new terminal:
source ~/catkin_ws/devel/setup.bash
rosrun rviz rviz -d ~/catkin_ws/src/LeGO-LOAM/launch/test.rviz
```

**Topics to Visualize:**
- `/laser_cloud_surround`: Surrounding map
- `/aft_mapped_to_init`: Optimized trajectory
- `/segmented_cloud`: Segmented point cloud
- `/ground_cloud`: Detected ground points

**Notes:**
- RViz config provided: `test.rviz`
- Helps verify system is working correctly

---

## Success Criteria

- [ ] All packages build without errors
- [ ] All four nodes launch successfully
- [ ] Bag file plays and is processed
- [ ] Odometry messages published on `/aft_mapped_to_init`
- [ ] Point cloud maps generated
- [ ] No critical errors in console output

---

## Troubleshooting Notes

### Common Issues
1. **GTSAM version mismatch:** Must use 4.0.0-alpha2 specifically
2. **Missing dependencies:** Install PCL, OpenCV, Eigen3, Boost
3. **ROS workspace not sourced:** Remember `source devel/setup.bash`
4. **First build fails:** Use `-j1` flag
5. **Ubuntu 24.04 compatibility:** ROS 1 not officially supported

### Additional Resources
- [LeGO-LOAM Paper](./Shan_Englot_IROS_2018_Preprint.pdf)
- [Sample Dataset](https://github.com/RobustFieldAutonomyLab/jackal_dataset_20170608)
- [GTSAM Documentation](https://gtsam.org/)

---

## Next Steps After Setup
- [ ] Verify vanilla system works correctly
- [ ] Baseline performance measurements
- [ ] Document current behavior
- [ ] Ready for research modifications

---

**Last Updated:** December 26, 2025

---

## Current Status Summary

### ✅ Successfully Installed:
1. **GTSAM 4.0.0-alpha2** - `/usr/local/lib/libgtsam.so.4.0.0`
2. **PCL 1.14.0** - Point Cloud Library with all plugins
3. **Eigen 3.4.0** - Linear algebra
4. **Boost 1.83.0** - C++ libraries  
5. **OpenCV** - Image processing
6. **All system dependencies** - liblz4, bz2, proj, etc.

### ⚠️ Current Challenge:
**ROS 1 Noetic on Ubuntu 24.04** - Ubuntu 24.04 is not officially supported for ROS 1 Noetic (designed for Ubuntu 20.04). Building from source encounters Python compatibility issues.

### � Chosen Approach: Docker (Option 1)

**Status:** Building Docker image with ROS Noetic  
**Reason:** Ubuntu 24.04 incompatibility with ROS 1 Noetic  

**What's Being Built:**
- Ubuntu 20.04 (Focal) base with ROS Noetic
- All ROS packages (cv_bridge, tf, pcl_ros, etc.)
- GTSAM 4.0.0-alpha2 from source
- PCL, Eigen, Boost libraries
- Complete build environment

**Files Created:**
- `Dockerfile.ros` - Docker configuration
- `run_lego_loam.sh` - Script to build and run container

### 📊 Progress: ~85% Complete
- Dependencies: ✅ 100%
- Docker Setup: 🔄 85% (building image)
- Compilation: ⏳ Pending
- Testing: ⏳ Pending
