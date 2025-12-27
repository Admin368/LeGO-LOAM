# LeGO-LOAM Debugging & Logging Guide

**Document:** 01_DEBUGGING_GUIDE_2025-12-26.md  
**Created:** December 26, 2025  
**Version:** 1.0

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Setup & Configuration](#setup--configuration)
4. [Logging System](#logging-system)
5. [Analysis Tools](#analysis-tools)
6. [Troubleshooting Guide](#troubleshooting-guide)
7. [Common Issues & Solutions](#common-issues--solutions)
8. [Sensor Configuration Reference](#sensor-configuration-reference)
9. [Technical Reference](#technical-reference)

---

## Overview

This guide documents the complete debugging and logging system for LeGO-LOAM. The system provides:

- **Real-time console logging** during execution
- **File-based logging** for post-session analysis
- **Automated analysis tools** to identify data flow issues
- **Diagnostic scripts** for system health checks

### Quick Reference

| Component | Location |
|-----------|----------|
| Log output | `/tmp/lego_loam_logs/lego_loam_debug.log` |
| Analysis scripts | `/workspace/logging_and_debugging/` |
| Configuration | `LeGO-LOAM/include/utility.h` |
| Logger header | `LeGO-LOAM/include/lego_loam_logger.h` |

---

## System Architecture

### LeGO-LOAM Data Pipeline

```
┌─────────────────┐    ┌──────────────────────┐    ┌─────────────────┐
│  Point Cloud    │───▶│  ImageProjection     │───▶│FeatureAssociation│
│  (/velodyne_    │    │  - Range image       │    │  - Corner detect │
│   points)       │    │  - Ground removal    │    │  - Surface detect│
└─────────────────┘    │  - Segmentation      │    │  - Odometry est  │
                       └──────────────────────┘    └────────┬────────┘
                                                            │
                       ┌──────────────────────┐             │
                       │  TransformFusion     │◀────────────┤
                       │  - Final pose output │             │
                       └──────────────────────┘             │
                                ▲                           ▼
                       ┌────────┴─────────────────────────────────┐
                       │  MapOptimization                          │
                       │  - Loop closure                           │
                       │  - Graph optimization                     │
                       │  - Global map maintenance                 │
                       └──────────────────────────────────────────┘
```

### Logging Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     LeGOLOAMLogger (Singleton)                  │
├─────────────────────────────────────────────────────────────────┤
│  • Thread-safe mutex-protected writes                           │
│  • Millisecond timestamp precision                              │
│  • Dual output: Console + File                                  │
│  • Per-node logging macros                                      │
└─────────────────────────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
┌─────────────────┐           ┌─────────────────────────┐
│  Console Output │           │  /tmp/lego_loam_logs/   │
│  (Real-time)    │           │  lego_loam_debug.log    │
└─────────────────┘           └─────────────────────────┘
```

---

## Setup & Configuration

### Enabling Debug Logging

Edit `LeGO-LOAM/include/utility.h`:

```cpp
// Debug toggle (Line ~170)
#define LEGO_LOAM_DEBUG 1              // 1 = ON, 0 = OFF

// File logging toggle
#define LEGO_LOAM_FILE_DEBUG 1         // 1 = ON, 0 = OFF
```

### Rebuilding After Changes

```bash
cd /catkin_ws
catkin_make
source devel/setup.bash
```

### Verifying Setup

```bash
# Check that log directory can be created
mkdir -p /tmp/lego_loam_logs
ls -la /tmp/lego_loam_logs/
```

---

## Logging System

### Available Macros

| Macro | Purpose | Output |
|-------|---------|--------|
| `DEBUG_LOG(msg)` | General debug | Console + File |
| `LOG_IMG_PROJ(msg)` | ImageProjection | File only |
| `LOG_FEAT_ASSOC(msg)` | FeatureAssociation | File only |
| `LOG_MAP_OPT(msg)` | MapOptimization | File only |
| `LOG_TRANSFORM(msg)` | TransformFusion | File only |

### Usage Examples

```cpp
// In ImageProjection node
LOG_IMG_PROJ("Received point cloud with " << cloud->points.size() << " points");

// In FeatureAssociation node
LOG_FEAT_ASSOC("Sharp corners: " << cornerPointsSharp->points.size());

// In MapOptimization node
LOG_MAP_OPT("Publishing global map with " << cloudKeyPoses3D->points.size() << " key poses");
```

### Log Format

```
[YYYY-MM-DD HH:MM:SS.mmm] [LEVEL] [NODE_NAME] Message
```

Example output:
```
[2025-12-26 14:30:45.123] [DEBUG] [ImageProjection] Received point cloud with 28000 points
[2025-12-26 14:30:45.145] [DEBUG] [ImageProjection] After conversion, PCL cloud has 28712 points
[2025-12-26 14:30:45.234] [DEBUG] [ImageProjection] Publishing clouds - Ground: 3421, Segmented: 15234, Outliers: 892
[2025-12-26 14:30:45.312] [DEBUG] [FeatureAssociation] Received segmented cloud with 15234 points
[2025-12-26 14:30:45.456] [DEBUG] [FeatureAssociation] Publishing features - Sharp corners: 320
```

---

## Analysis Tools

All tools are located in `/workspace/logging_and_debugging/`

### 1. analyze_logs.py - Automated Log Analysis

Performs comprehensive analysis of collected logs.

**Usage:**
```bash
python3 analyze_logs.py /tmp/lego_loam_logs/lego_loam_debug.log
```

**Output Sections:**

1. **Point Cloud Flow Analysis**
   - Input point counts (raw from sensor)
   - Ground points removed
   - Segmented points after filtering
   - Feature counts (corners, surfaces)
   - Loss percentages between stages

2. **Data Synchronization Check**
   - Verifies all nodes are receiving data
   - Message counts per node
   - Publishing verification

3. **Performance Metrics**
   - Log duration
   - Average message rate
   - Total entries

4. **Issues & Recommendations**
   - Automatically identifies problems
   - Provides actionable fix suggestions

### 2. view_logs.py - Real-time Log Viewer

Monitor logs while LeGO-LOAM is running.

**Usage:**
```bash
# Follow mode (like tail -f)
python3 view_logs.py -f

# Filter by specific node
python3 view_logs.py -f -n ImageProjection
python3 view_logs.py -f -n FeatureAssociation
python3 view_logs.py -f -n MapOptimization

# Show last N lines
python3 view_logs.py -l 50

# Show statistics summary
python3 view_logs.py -s
```

**Color Coding:**
- 🟢 Green = ImageProjection
- 🟣 Magenta = FeatureAssociation
- 🔵 Cyan = MapOptimization
- 🟡 Yellow = TransformFusion

### 3. collect_logs.sh - Log Management

Collect and archive logs with timestamps.

**Usage:**
```bash
# Full workflow: collect + analyze
bash collect_logs.sh --run

# Just collect/archive logs
bash collect_logs.sh --collect

# Analyze most recent session
bash collect_logs.sh --analyze

# Clear old logs
bash collect_logs.sh --clear
```

**Archive Location:** `./lego_loam_debug_session/session_YYYYMMDD_HHMMSS/`

### 4. check_status.sh - System Diagnostics

Run diagnostics on a live LeGO-LOAM system.

**Usage (inside container):**
```bash
bash check_status.sh
```

**Checks:**
- ROS master status
- Active topics and rates
- Input topic health (/velodyne_points, /imu/data)
- Processing topic status
- TF transform publishing
- Point cloud sizes
- Debug logging status

---

## Troubleshooting Guide

### Step-by-Step Debug Workflow

1. **Enable debug logs** in utility.h
2. **Rebuild** the project
3. **Start LeGO-LOAM** and watch console output
4. **Play bag file** with `--clock` flag
5. **Let it run** for 30-60 seconds
6. **Collect logs**: `bash collect_logs.sh --run`
7. **Review analysis** for issues and recommendations
8. **Apply fixes** based on recommendations
9. **Disable debug** when done (set to 0)

### Reading the Analysis Output

**Healthy Example:**
```
📥 INPUT CLOUDS (ImageProjection):
   Total received: 143
   Min: 28,000  Max: 30,000  Avg: 28,900

🔍 SEGMENTED CLOUDS (ImageProjection output):
   Total published: 143
   Min: 15,000  Max: 18,000  Avg: 16,500
   Loss in segmentation: 43%            ← Normal loss

📌 FEATURE EXTRACTION (FeatureAssociation):
   Sharp corners: 143 messages
      Min: 280  Max: 350  Avg: 320      ← Good feature count

✓ No critical issues detected!
```

**Problematic Example:**
```
📥 INPUT CLOUDS (ImageProjection):
   Total received: 143
   Min: 28,000  Max: 30,000  Avg: 28,900

🔍 SEGMENTED CLOUDS (ImageProjection output):
   Total published: 143
   Min: 5  Max: 20  Avg: 15             ← PROBLEM: Too few!
   Loss in segmentation: 99.9%          ← CRITICAL

📌 FEATURE EXTRACTION (FeatureAssociation):
   Sharp corners: 0 messages            ← No features!

⚠️  Found 2 issue(s):
  1. ⚠️  CRITICAL: > 90% of points filtered out in segmentation!
  2. ⚠️  Very few corner features detected (< 10 per frame)

📋 RECOMMENDED ACTIONS:
  • Check sensor configuration in utility.h
  • Verify N_SCAN matches your LIDAR sensor
  • Review ground removal settings (groundScanInd)
```

---

## Common Issues & Solutions

### Issue 1: No Debug Messages Appearing

**Symptoms:** Launch looks normal but no [DEBUG] messages

**Solutions:**
- Rebuild after editing utility.h
- Verify `LEGO_LOAM_DEBUG 1` is set
- Check build completed without errors

### Issue 2: Very Few Points in Segmented Cloud

**Symptoms:** Debug shows < 100 segmented points

**Causes & Fixes:**

| Cause | Fix |
|-------|-----|
| Wrong sensor config | Set `N_SCAN` to match your LIDAR (16/32/64/128) |
| Ground removal too aggressive | Reduce `groundScanInd` value |
| Range filtering | Check `sensorMinimumRange` setting |
| Angle parameters wrong | Verify `ang_bottom` matches sensor |

### Issue 3: No Features Detected

**Symptoms:** Sharp corners: 0, Flat surfaces: 0

**Causes & Fixes:**

| Cause | Fix |
|-------|-----|
| No input to FeatureAssociation | Check ImageProjection is publishing |
| Thresholds too strict | Adjust feature detection parameters |
| Sensor orientation wrong | Check `sensorMountAngle` |

### Issue 4: RViz Shows Nothing

**Symptoms:** Analysis shows good data flow but RViz empty

**Solutions:**
1. Set Fixed Frame to `map` or `camera_init`
2. Enable displays in RViz left panel
3. Wait 10-20 seconds for data to accumulate
4. Check TF tree: `rosrun tf view_frames`

### Issue 5: Nodes Not Synchronized

**Symptoms:** Message count mismatches between nodes

**Solutions:**
1. Use `--clock` flag with rosbag play
2. Check ROS master is running
3. Verify all nodes started correctly
4. Check for clock time jumps in logs

---

## Sensor Configuration Reference

Edit these parameters in `LeGO-LOAM/include/utility.h`:

### VLP-16 (Velodyne Puck)
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
extern const float ang_res_x = 0.2;
extern const float ang_res_y = 1.33;
extern const float ang_bottom = 30.67;
extern const int groundScanInd = 20;
```

### VLS-128
```cpp
extern const int N_SCAN = 128;
extern const int Horizon_SCAN = 1800;
extern const float ang_res_x = 0.2;
extern const float ang_res_y = 0.3;
extern const float ang_bottom = 25.0;
extern const int groundScanInd = 10;
```

---

## Technical Reference

### Logger Class Implementation

File: `LeGO-LOAM/include/lego_loam_logger.h`

**Key Features:**
- Thread-safe with mutex protection
- Configurable console/file output
- Automatic directory creation
- Millisecond timestamp precision
- Multiple log levels (DEBUG, INFO, WARNING, ERROR)

**Static Members:**
```cpp
static std::mutex log_mutex_;           // Thread safety
static std::string log_dir_;            // Log directory path
static std::ofstream log_file_;         // Output file stream
static bool initialized_;               // Init state
static bool enable_console_output_;     // Console toggle
static bool enable_file_output_;        // File toggle
```

### Source Files Modified

| File | Changes |
|------|---------|
| `imageProjection.cpp` | Added LOG_IMG_PROJ calls for input/output tracking |
| `featureAssociation.cpp` | Added LOG_FEAT_ASSOC calls for feature tracking |
| `mapOptmization.cpp` | Added LOG_MAP_OPT calls for map state tracking |

### Log Levels

| Level | Use Case |
|-------|----------|
| DEBUG | Detailed processing information |
| INFO | General status updates |
| WARNING | Non-critical issues |
| ERROR | Critical failures |

---

## File Reference

### Logging & Debugging Folder Structure

```
logging_and_debugging/
├── QUICKSTART.md                    # Quick reference guide
├── 01_DEBUGGING_GUIDE_2025-12-26.md # This detailed guide
├── analyze_logs.py                  # Automated log analysis
├── view_logs.py                     # Real-time log viewer
├── collect_logs.sh                  # Log collection/archiving
└── check_status.sh                  # System diagnostics
```

### Related Source Files

```
LeGO-LOAM/
├── include/
│   ├── utility.h                    # Debug toggles, sensor config
│   └── lego_loam_logger.h           # Logger implementation
└── src/
    ├── imageProjection.cpp          # First processing stage
    ├── featureAssociation.cpp       # Feature extraction
    ├── mapOptmization.cpp           # Map building
    └── transformFusion.cpp          # Final output
```

---

*Document End - Version 1.0 - December 26, 2025*
