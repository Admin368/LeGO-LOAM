# LeGO-LOAM Debugging Guide

## Current Issue Analysis

Based on the topic comparison and RViz screenshots, the visualization appears empty/incomplete because:

### Missing Data Flow
1. **Point Cloud Data**: The bag file contains `/velodyne_points` (143 messages), but LeGO-LOAM may not be processing all points correctly
2. **IMU Data**: The bag has `/imu/data` (1066 messages), which LeGO-LOAM is configured to use
3. **Visualization Topics**: RViz displays are configured but may not be receiving enough data

### Root Cause Hypothesis
The most likely issues are:
1. **Point cloud segmentation filtering out too many points** - Check sensor parameters in utility.h
2. **IMU not initialized properly** - The algorithm may be waiting for IMU data to stabilize
3. **Coordinate frame issues** - TF transforms may not be publishing correctly
4. **Timing synchronization** - Clock may not be advancing properly with `--clock` flag

---

## Debug Logging System

I've added a simple debug logging system that can be toggled on/off with a single line change.

### How to Enable/Disable Debug Logs

Edit `/workspaces/LeGO-LOAM/LeGO-LOAM/include/utility.h`:

```cpp
// Set to 1 to enable debug logs, 0 to disable
#define LEGO_LOAM_DEBUG 1  // Change to 0 to disable
```

After changing this value, you must rebuild:
```bash
cd /catkin_ws
catkin_make
source devel/setup.bash
```

### What Gets Logged

With debug enabled, you'll see:

1. **ImageProjection Node**:
   - Received point cloud size
   - PCL conversion results
   - Published cloud sizes (ground, segmented, outliers)

2. **FeatureAssociation Node**:
   - Segmented cloud reception
   - Outlier cloud reception
   - Cloud info messages
   - Feature counts (sharp/flat surfaces)

3. **MapOptimization Node**:
   - Corner cloud reception
   - Surface cloud reception
   - Odometry updates
   - Global map key poses count
   - Published map point counts

### Example Debug Output

```
[DEBUG] ImageProjection: Received point cloud with 28800 points
[DEBUG] ImageProjection: After conversion, PCL cloud has 28712 points
[DEBUG] ImageProjection: Publishing clouds - Ground: 3421, Segmented: 15234, Outliers: 892
[DEBUG] FeatureAssociation: Received segmented cloud with 15234 points
[DEBUG] FeatureAssociation: Publishing features - Sharp corners: 320, Less sharp: 640, Flat surf: 640, Less flat: 1280
[DEBUG] MapOptimization: Received corner cloud with 640 points
[DEBUG] MapOptimization: Publishing global map with 12 key poses
```

---

## Testing Steps

### 1. Start LeGO-LOAM with Debug Logs

Terminal 1:
```bash
docker run -it --rm --name lego-loam \
  -v $(pwd):/workspace \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -e DISPLAY=$DISPLAY \
  -w /catkin_ws lego-loam:melodic bash

# Inside container:
source /opt/ros/melodic/setup.bash
ln -sf /workspace/LeGO-LOAM /catkin_ws/src/
ln -sf /workspace/cloud_msgs /catkin_ws/src/
catkin_make
source devel/setup.bash
roslaunch lego_loam run.launch
```

**Watch the debug output carefully!** You should see messages indicating data reception and processing.

### 2. Launch RViz

Terminal 2:
```bash
docker exec -it lego-loam bash -c "source /opt/ros/melodic/setup.bash && source /catkin_ws/devel/setup.bash && rviz -d /workspace/LeGO-LOAM/launch/test.rviz"
```

### 3. Play Bag File

Terminal 3:
```bash
docker exec -it lego-loam bash -c "source /opt/ros/melodic/setup.bash && rosbag play /workspace/data/2017-06-08-15-52-45_3.bag --clock"
```

### 4. Monitor Topics

Terminal 4 (optional):
```bash
docker exec -it lego-loam bash

# Check if topics are publishing
rostopic hz /full_cloud_projected
rostopic hz /laser_cloud_less_sharp
rostopic hz /laser_cloud_surround

# Check point counts in published clouds
rostopic echo /full_cloud_projected --noarr | grep -E "(width|height):"
```

---

## Common Issues and Solutions

### Issue 1: No Debug Messages Appearing
**Symptom**: Launch looks normal but no [DEBUG] messages
**Solution**: 
- Rebuild after editing utility.h
- Make sure `LEGO_LOAM_DEBUG 1` is set
- Check that the build didn't have errors

### Issue 2: Very Few Points in Clouds
**Symptom**: Debug shows very low point counts (< 100 points)
**Possible Causes**:
1. **Sensor parameters mismatch** - Check in utility.h:
   ```cpp
   extern const int N_SCAN = 16;           // Should match your sensor
   extern const float sensorMinimumRange = 1.0;  // May filter too aggressively
   extern const float sensorMountAngle = 0.0;    // Mounting angle
   ```

2. **Ground removal too aggressive** - Try adjusting:
   ```cpp
   extern const int groundScanInd = 7;     // Rings used for ground detection
   ```

3. **Segmentation threshold too strict**:
   ```cpp
   extern const float segmentTheta = 60.0/180.0*M_PI;
   extern const int segmentValidPointNum = 5;
   extern const int segmentValidLineNum = 3;
   ```

### Issue 3: Empty RViz Displays
**Symptom**: Topics publishing but RViz shows nothing
**Checks**:
1. Frame IDs - Check the terminal, RViz may show "Transform [frame] does not exist"
2. Global Status in RViz - Look for red error indicators
3. Fixed Frame - Should be set to "map" or "camera_init"
4. Enable specific displays - Some are disabled by default in test.rviz

### Issue 4: Point Clouds Appear But No Path/Trajectory
**Symptom**: See point clouds but no odometry path
**Solution**: 
- Check `/laser_odom_to_init` and `/aft_mapped_to_init` topics are publishing
- Verify TF transforms: `rosrun tf view_frames` (creates frames.pdf)
- Path may take time to accumulate - let bag play longer

---

## Advanced Debugging

### Check Transform Tree
```bash
docker exec -it lego-loam bash -c "source /opt/ros/melodic/setup.bash && rosrun tf view_frames && cat frames.pdf"
```

### Monitor All Topic Rates
```bash
docker exec -it lego-loam bash -c "source /opt/ros/melodic/setup.bash && rostopic hz /velodyne_points & rostopic hz /segmented_cloud & rostopic hz /laser_cloud_less_sharp"
```

### Check for Warnings/Errors
```bash
# Watch rosout for errors
docker exec -it lego-loam bash -c "source /opt/ros/melodic/setup.bash && rostopic echo /rosout | grep -E '(ERROR|WARN)'"
```

### Verify IMU Data
```bash
docker exec -it lego-loam bash -c "source /opt/ros/melodic/setup.bash && rostopic echo /imu/data --noarr"
```

---

## Next Steps

1. **Run with debug logs** and observe the point counts at each stage
2. **If point counts are very low** (< 1000), adjust sensor parameters
3. **If point counts are good but visualization empty**, check frame IDs and TF
4. **If everything processes but no trajectory**, check odometry topics

After identifying the issue, you can disable debug logs by setting:
```cpp
#define LEGO_LOAM_DEBUG 0
```

And rebuild for production use.

---

## Quick Fix Checklist

- [ ] Debug logs enabled and rebuild completed
- [ ] Can see debug messages showing data reception
- [ ] Point counts in debug logs look reasonable (> 1000 points)
- [ ] All expected topics are publishing (rostopic list)
- [ ] RViz Global Status shows "Ok" (not error)
- [ ] Fixed Frame in RViz set correctly
- [ ] TF transforms are being published (rostopic echo /tf)
- [ ] Bag plays with --clock flag
- [ ] Waited at least 10 seconds for initialization

If all checkboxes pass but still empty, the issue is likely in sensor parameter configuration in utility.h.
