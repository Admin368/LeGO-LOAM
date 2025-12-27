# File-Based Logging System for LeGO-LOAM Debugging

## Overview

The enhanced LeGO-LOAM debugging system now includes **file-based logging** that captures all debug information to disk. This allows you to:

1. **Capture debug data** while running LeGO-LOAM with a bag file
2. **Share log files** for remote analysis
3. **Identify data flow issues** with automated analysis tools
4. **Verify system health** at each processing stage

## Quick Start

### 1. Enable Debug Logging

Edit `LeGO-LOAM/include/utility.h`:

```cpp
#define LEGO_LOAM_DEBUG 1              // Enable debug logs
#define LEGO_LOAM_FILE_DEBUG 1         // Enable file-based logging
```

Then rebuild:

```bash
cd /catkin_ws
catkin_make
source devel/setup.bash
```

### 2. Run LeGO-LOAM and Collect Data

**Terminal 1 - Start LeGO-LOAM:**
```bash
roslaunch lego_loam run.launch
```

Watch for debug output. Logs are being written to: `/tmp/lego_loam_logs/lego_loam_debug.log`

**Terminal 2 - Play bag file:**
```bash
rosbag play /path/to/your.bag --clock
```

**Terminal 3 - Collect and analyze logs:**
```bash
cd /workspace
bash collect_logs.sh --run
```

### 3. Review Analysis Results

The analysis script will output:

```
════════════════════════════════════════════════════════════════
POINT CLOUD FLOW ANALYSIS
════════════════════════════════════════════════════════════════

📥 INPUT CLOUDS (ImageProjection):
   Total received: 143
   Min: 28,000  Max: 30,000  Avg: 28,900

🔍 SEGMENTED CLOUDS (ImageProjection output):
   Total published: 143
   Min: 15,000  Max: 18,000  Avg: 16,500
   Loss in segmentation: 43%
```

## File Locations

| File | Purpose |
|------|---------|
| `/tmp/lego_loam_logs/lego_loam_debug.log` | Main debug log (active) |
| `./lego_loam_debug_session/session_*/` | Archived logs for analysis |

## Logging Macros

The system provides several logging macros for different needs:

### Console + File Logging
```cpp
DEBUG_LOG("message");  // Outputs to both console and file
```

### File-Only Logging
```cpp
LOG_IMG_PROJ("message");      // ImageProjection node
LOG_FEAT_ASSOC("message");    // FeatureAssociation node
LOG_MAP_OPT("message");       // MapOptimization node
LOG_TRANSFORM("message");     // TransformFusion node
```

### Example Usage
```cpp
LOG_IMG_PROJ("Received " << cloud->points.size() << " points");
```

## Log Format

Each log entry has the format:

```
[YYYY-MM-DD HH:MM:SS.mmm] [LEVEL] [NODE_NAME] Message
```

Example:
```
[2025-12-26 14:30:45.123] [DEBUG] [ImageProjection] Received point cloud with 28000 points
[2025-12-26 14:30:45.145] [DEBUG] [ImageProjection] After conversion, PCL cloud has 28712 points
[2025-12-26 14:30:45.234] [DEBUG] [ImageProjection] Publishing clouds - Ground: 3421, Segmented: 15234, Outliers: 892
```

## Using the Analysis Tools

### Automatic Analysis

Collect logs and analyze them automatically:

```bash
./collect_logs.sh --run
```

This will:
1. Collect logs from `/tmp/lego_loam_logs/`
2. Archive them with timestamp
3. Run automated analysis
4. Display results and recommendations

### Manual Analysis

To analyze existing logs:

```bash
python3 analyze_logs.py /tmp/lego_loam_logs/lego_loam_debug.log
```

Or with a specific log file:

```bash
python3 analyze_logs.py ./lego_loam_debug_session/session_20251226_143045/lego_loam_debug.log
```

## Analysis Output

The analyzer checks four main areas:

### 1. Point Cloud Flow

Shows how many points are at each stage:
- Input points (raw from sensor)
- Ground points (removed)
- Segmented points (after segmentation)
- Feature counts (sharp corners, flat surfaces)
- Map points (final map)

**Typical healthy flow:**
```
Input: 28,000 → Ground removed: 3,500 → Segmented: 15,000 → Features: 320
```

**Problematic flow:**
```
Input: 28,000 → Segmented: 15 → Features: 0  ❌ (Sensor config issue!)
```

### 2. Data Synchronization

Verifies all nodes are receiving and publishing data:
- ImageProjection: receives input, publishes segmented clouds
- FeatureAssociation: receives segmented clouds, publishes features
- MapOptimization: receives features, publishes map

### 3. Performance Metrics

- Total log duration
- Average message rate
- Total log entries

### 4. Issues and Recommendations

Identifies problems and provides actionable fixes:

| Issue | Cause | Fix |
|-------|-------|-----|
| Very low input points | Wrong sensor config | Update N_SCAN in utility.h |
| > 90% points filtered | Ground removal too aggressive | Adjust groundScanInd |
| Few corner features | Weak input signal | Check sensor alignment |
| Nodes not synchronized | Timing issue | Check ROS clock setup |

## Common Scenarios

### Scenario 1: No RViz Output, But Logs Show Good Data

**Symptom:** Analyzer shows healthy point counts, but RViz is empty

**Diagnosis:** Visualization configuration issue

**Fix:**
```bash
1. Check RViz Fixed Frame: should be "map" or "camera_init"
2. Enable displays in RViz left panel
3. Check Global Status for TF errors
4. Verify frame_id in published messages matches Fixed Frame
```

### Scenario 2: Point Counts Drop Off Immediately

**Symptom:**
```
Input: 28,000  →  Segmented: 15  ❌  Features: 0
```

**Diagnosis:** Sensor parameter mismatch

**Fix:**
1. Check what LIDAR is used (VLP-16, HDL-32E, VLS-128, etc.)
2. Update N_SCAN, ang_res_y, groundScanInd in utility.h
3. Rebuild and test again

**Examples:**

For VLP-16:
```cpp
extern const int N_SCAN = 16;
extern const float ang_res_y = 2.0;
extern const int groundScanInd = 7;
```

For HDL-32E:
```cpp
extern const int N_SCAN = 32;
extern const float ang_res_y = 1.33;
extern const int groundScanInd = 20;
```

### Scenario 3: Sensor Works, But No Map Builds

**Symptom:** Features detected fine, but no global map

**Diagnosis:** Map optimization issue

**Fix:**
```bash
1. Check /laser_odom_to_init topic is publishing
2. Verify TF transforms exist
3. Check initialization parameters
4. Run: rosrun tf view_frames
```

## Workflow: Debug Session

### Step 1: Setup
```bash
# Terminal 1: Prepare container
docker run -it --rm --name lego-loam \
  -v $(pwd):/workspace \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -w /catkin_ws lego-loam:melodic bash

source /opt/ros/melodic/setup.bash
ln -sf /workspace/LeGO-LOAM /catkin_ws/src/
ln -sf /workspace/cloud_msgs /catkin_ws/src/
catkin_make
source devel/setup.bash
```

### Step 2: Enable Logging and Run
```bash
# Inside container - Terminal 1
roslaunch lego_loam run.launch
```

Watch console output for [DEBUG] messages.

### Step 3: Play Data
```bash
# Inside container - Terminal 2
rosbag play /workspace/data/your.bag --clock
```

Let run for 30-60 seconds to get good data.

### Step 4: Collect Logs
```bash
# Inside container - Terminal 3
cd /workspace
bash collect_logs.sh --collect
```

### Step 5: Analyze
```bash
# Still inside container - Terminal 3
bash collect_logs.sh --analyze
```

### Step 6: Share Results
```bash
# Copy results to your host
exit  # from container
ls -la lego_loam_debug_session/
# Share the session directory with developers
```

## Disable Logging for Production

When you've identified and fixed the issue, disable logging:

```cpp
#define LEGO_LOAM_DEBUG 0
#define LEGO_LOAM_FILE_DEBUG 0
```

Then rebuild.

## Logger Implementation Details

The logging system is implemented in `LeGO-LOAM/include/lego_loam_logger.h`:

- **Thread-safe:** Uses mutex for concurrent writes
- **Buffered:** Flushes to disk immediately for no data loss
- **Timestamped:** Includes millisecond precision timestamps
- **Configurable:** Can enable/disable file and console output
- **Memory efficient:** No log buffering in memory

## Troubleshooting the Logging System

### Logs not being created

**Check:**
```bash
ls -la /tmp/lego_loam_logs/
```

**Solution:**
1. Ensure `LEGO_LOAM_FILE_DEBUG 1` in utility.h
2. Rebuild: `catkin_make`
3. Restart LeGO-LOAM

### Log file too large

The log file can grow quickly. To archive and clear:

```bash
# Archive before clearing
bash collect_logs.sh --collect

# Clear old logs
bash collect_logs.sh --clear
```

### Permission denied errors

If you get permission errors reading logs:

```bash
# Make writable if needed
chmod 666 /tmp/lego_loam_logs/lego_loam_debug.log
```

## Next Steps

1. ✅ **Enable debug logging** in utility.h
2. ✅ **Rebuild** the project
3. ✅ **Run with bag file** and collect logs
4. ✅ **Analyze logs** automatically
5. ✅ **Follow recommendations** to fix issues
6. ✅ **Share logs** for remote debugging if needed

## Files Modified

- `LeGO-LOAM/include/utility.h` - Added logging macros
- `LeGO-LOAM/include/lego_loam_logger.h` - Logger implementation
- `LeGO-LOAM/src/imageProjection.cpp` - Added log calls
- `LeGO-LOAM/src/featureAssociation.cpp` - Added log calls
- `LeGO-LOAM/src/mapOptmization.cpp` - Added log calls
- `analyze_logs.py` - Log analysis tool
- `collect_logs.sh` - Log collection and management script

## Questions?

See docs/DEBUGGING_GUIDE.md for general debugging information.
