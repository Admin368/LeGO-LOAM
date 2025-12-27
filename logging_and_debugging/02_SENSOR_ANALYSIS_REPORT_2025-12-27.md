# LeGO-LOAM Sensor Analysis & Configuration Report

**Document:** 02_SENSOR_ANALYSIS_REPORT_2025-12-27.md  
**Created:** December 27, 2025  
**Status:** In Progress

---

## Executive Summary

Investigation of empty RViz visualization revealed a **sensor configuration mismatch**. The bag file contains VLP-16 data with ring field, but LeGO-LOAM was configured incorrectly.

| Finding | Details |
|---------|---------|
| **Sensor Detected** | Velodyne VLP-16 (16 scan lines) |
| **Ring Field** | Present ✓ |
| **Critical Issue** | `useCloudRing` was set to `false` |
| **Ground Points** | 0 (should be 2000-5000) |

---

## 1. Bag File Analysis Results

### 1.1 Bag File Information

**File:** `/workspace/data/2017-06-08-15-51-45_2.bag`

| Property | Value |
|----------|-------|
| Velodyne Messages | 572 |
| IMU Messages | 4,365 |
| Points per Frame | ~27,000 |
| Point Step | 32 bytes |

### 1.2 Point Cloud Fields

```
Fields: ['x', 'y', 'z', 'intensity', 'ring']
```

**Key Finding:** The `ring` field IS present in the data.

### 1.3 Sensor Detection

| Parameter | Detected Value |
|-----------|----------------|
| Scan Lines | 16 (rings 0-15) |
| Vertical Angle Range | -15° to +15° (30° total) |
| Points per Ring | ~600-700 average |
| Sensor Type | **VLP-16** |

### 1.4 Ring Distribution

```
Ring  0: ~694 points/frame
Ring  1: ~690 points/frame
Ring  2: ~705 points/frame
Ring  3: ~700 points/frame
Ring  4: ~700 points/frame
Ring  5: ~690 points/frame
Ring  6: ~667 points/frame
Ring  7: ~596 points/frame  ← groundScanInd boundary
Ring  8: ~523 points/frame
Ring  9: ~471 points/frame
Ring 10: ~559 points/frame
Ring 11: ~588 points/frame
Ring 12: ~606 points/frame
Ring 13: ~610 points/frame
Ring 14: ~598 points/frame
Ring 15: ~597 points/frame
```

---

## 2. Configuration Issues Identified

### 2.1 Original (Incorrect) Configuration

```cpp
// Was incorrectly set:
extern const bool useCloudRing = false;  // ← WRONG

// Was using HDL-32E parameters:
extern const int N_SCAN = 32;            // ← WRONG (should be 16)
extern const int groundScanInd = 20;     // ← WRONG (should be 7)
```

### 2.2 Why This Caused Problems

1. **`useCloudRing = false`**: LeGO-LOAM computed row indices from vertical angles instead of using the accurate ring values from the sensor. This caused incorrect point-to-row mapping.

2. **`N_SCAN = 32`**: With 16-ring data mapped to a 32-row structure, points were scattered across wrong rows, breaking the ground detection algorithm.

3. **Ground Detection Failure**: The `groundRemoval()` function checks angles between adjacent rows. With incorrect row mapping, no points satisfied the ground condition (`abs(angle - sensorMountAngle) <= 10`).

### 2.3 Corrected Configuration

```cpp
// LeGO-LOAM/include/utility.h

// CRITICAL: Use ring field from sensor data
extern const bool useCloudRing = true;

// VLP-16 parameters
extern const int N_SCAN = 16;
extern const int Horizon_SCAN = 1800;
extern const float ang_res_x = 0.2;
extern const float ang_res_y = 2.0;
extern const float ang_bottom = 15.0+0.1;
extern const int groundScanInd = 7;
```

---

## 3. Debug Log Analysis

### 3.1 Data Flow Before Fix

From session `session_20251227_011356`:

```
[ImageProjection] Received point cloud with 26942 points
[ImageProjection] After conversion, PCL cloud has 26942 points
[ImageProjection] Publishing clouds - Ground: 0, Segmented: 6793, Outliers: 1550
```

**Issue:** Ground = 0 in every frame

### 3.2 Expected Data Flow After Fix

```
[ImageProjection] Received point cloud with ~27000 points
[ImageProjection] Publishing clouds - Ground: 3000-5000, Segmented: 10000-15000
[FeatureAssociation] Publishing features - Sharp corners: 200-500
```

### 3.3 Point Flow Summary

| Stage | Before Fix | Expected After Fix |
|-------|------------|-------------------|
| Input | 27,000 | 27,000 |
| Ground | 0 ❌ | 3,000-5,000 ✓ |
| Segmented | 6,700 | 10,000-15,000 |
| Sharp Corners | 100 | 200-500 |
| Flat Surfaces | 170 | 300-600 |

---

## 4. RViz Visualization Issue

### 4.1 Current State

The RViz display shows only:
- TF coordinate frames (axes visible)
- Trajectory line (yellow line between frames)
- No point cloud data visible

### 4.2 Root Cause Chain

```
useCloudRing = false
        ↓
Incorrect row index calculation
        ↓
Points mapped to wrong scan lines
        ↓
Ground detection fails (Ground: 0)
        ↓
Segmentation quality degraded
        ↓
Map building produces sparse/empty output
        ↓
RViz shows empty visualization
```

### 4.3 Expected After Fix

With correct configuration:
- Point clouds should be visible
- Map should build incrementally
- Trajectory should have associated point data

---

## 5. Tools Created

### 5.1 Bag File Sensor Analyzer

**File:** `logging_and_debugging/analyze_bag_sensor.py`

**Purpose:** Automatically detect sensor type from bag file data

**Usage:**
```bash
# Inside Docker container
source /opt/ros/melodic/setup.bash
python2 /workspace/logging_and_debugging/analyze_bag_sensor.py
```

**Output:**
- Sensor type detection (VLP-16, HDL-32E, etc.)
- Ring field presence check
- Recommended utility.h configuration
- Vertical angle analysis

### 5.2 Log Analyzer (Updated)

**File:** `logging_and_debugging/analyze_logs.py`

**Fix Applied:** Updated pattern matching for log format `[NodeName]` instead of `NodeName:`

---

## 6. Action Items

### 6.1 Completed

- [x] Created bag file sensor analysis tool
- [x] Detected VLP-16 sensor with ring field
- [x] Updated utility.h with correct configuration
- [x] Set `useCloudRing = true`
- [x] Set `N_SCAN = 16`
- [x] Set `groundScanInd = 7`
- [x] Rebuilt LeGO-LOAM

### 6.2 Pending Verification

- [ ] Restart LeGO-LOAM with new configuration
- [ ] Run bag file and collect new logs
- [ ] Verify Ground points > 0
- [ ] Confirm RViz visualization works
- [ ] Collect success logs for documentation

---

## 7. Commands to Verify Fix

### 7.1 Restart LeGO-LOAM

**Terminal 1 (Docker):**
```bash
source /catkin_ws/devel/setup.bash
roslaunch lego_loam run.launch
```

**Terminal 2 (Docker):**
```bash
rosbag play /workspace/data/2017-06-08-15-51-45_2.bag --clock
```

### 7.2 Collect New Logs

**Terminal 3 (Docker):**
```bash
cd /workspace/logging_and_debugging
bash collect_logs.sh --run
```

### 7.3 Expected Success Indicators

In the log output, look for:
```
Ground: XXXX  (where XXXX > 0)
```

In RViz:
- Point cloud displays showing data
- Map building visible
- Colored feature points

---

## 8. Technical Reference

### 8.1 Ground Detection Algorithm

Location: `imageProjection.cpp`, function `groundRemoval()`

```cpp
for (size_t j = 0; j < Horizon_SCAN; ++j){
    for (size_t i = 0; i < groundScanInd; ++i){
        // Get points from adjacent rows
        lowerInd = j + ( i )*Horizon_SCAN;
        upperInd = j + (i+1)*Horizon_SCAN;
        
        // Calculate angle between points
        angle = atan2(diffZ, sqrt(diffX*diffX + diffY*diffY)) * 180 / M_PI;
        
        // Mark as ground if angle is close to sensor mount angle
        if (abs(angle - sensorMountAngle) <= 10){
            groundMat.at<int8_t>(i,j) = 1;
        }
    }
}
```

### 8.2 Row Index Calculation

**When `useCloudRing = true`:**
```cpp
rowIdn = laserCloudInRing->points[i].ring;
```

**When `useCloudRing = false`:**
```cpp
verticalAngle = atan2(thisPoint.z, sqrt(thisPoint.x*thisPoint.x + thisPoint.y*thisPoint.y)) * 180 / M_PI;
rowIdn = (verticalAngle + ang_bottom) / ang_res_y;
```

The ring-based method is more accurate when ring data is available.

### 8.3 VLP-16 Specifications

| Parameter | Value |
|-----------|-------|
| Channels | 16 |
| Vertical FOV | 30° (-15° to +15°) |
| Vertical Resolution | 2.0° |
| Horizontal FOV | 360° |
| Horizontal Resolution | 0.1° - 0.4° |
| Range | 100m |
| Points per Second | ~300,000 |

---

## 9. Appendix

### A. Full Sensor Analysis Output

```
======================================================================
BAG FILE SENSOR ANALYSIS
======================================================================

Analyzing: /workspace/data/2017-06-08-15-51-45_2.bag
Topic: /velodyne_points
Max frames to analyze: 5

======================================================================
BAG FILE INFO
======================================================================

Topics in bag:
  /velodyne_points: 572 messages, type: sensor_msgs/PointCloud2
  /imu/data: 4365 messages, type: sensor_msgs/Imu
  [+ 15 other topics]

======================================================================
POINT CLOUD ANALYSIS
======================================================================

--- Frame 1 ---
Points: 26,942
Dimensions: 26942 x 1
Fields: ['x', 'y', 'z', 'intensity', 'ring']
Point step: 32 bytes
Valid sampled points: 10,000
Range - Min: 1.11m, Max: 88.45m, Avg: 13.99m
Z range: -2.75m to 18.72m
Vertical angles: -15.0 deg to 15.0 deg
Ring field present: YES
Unique rings: 16

======================================================================
SENSOR DETECTION & RECOMMENDATIONS
======================================================================

*** DETECTED SENSOR: VLP-16 ***
    Ring field available: Yes

==================================================
RECOMMENDED utility.h CONFIGURATION:
==================================================

// Detected: VLP-16
extern const bool useCloudRing = true;
extern const int N_SCAN = 16;
extern const int Horizon_SCAN = 1800;
extern const float ang_res_x = 0.2;
extern const float ang_res_y = 2.00;
extern const float ang_bottom = 15.0;
extern const int groundScanInd = 7;
```

### B. Files Modified

| File | Change |
|------|--------|
| `LeGO-LOAM/include/utility.h` | Set `useCloudRing = true`, VLP-16 params |
| `logging_and_debugging/analyze_logs.py` | Fixed pattern matching for log format |
| `logging_and_debugging/analyze_bag_sensor.py` | Created (new) |

---

*Report End - Version 1.0 - December 27, 2025*
