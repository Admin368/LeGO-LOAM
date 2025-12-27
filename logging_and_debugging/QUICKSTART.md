# LeGO-LOAM Debugging Quick Start Guide

> **Quick reference for enabling debugging and analyzing LeGO-LOAM data flow**

## 🚀 5-Minute Setup

### Step 1: Enable Debug Logging

Edit `LeGO-LOAM/include/utility.h`:

```cpp
#define LEGO_LOAM_DEBUG 1              // Enable debug logs (1=ON, 0=OFF)
#define LEGO_LOAM_FILE_DEBUG 1         // Enable file-based logging
```

### Step 2: Rebuild

```bash
cd /catkin_ws
catkin_make
source devel/setup.bash
```

### Step 3: Run LeGO-LOAM

**Terminal 1** - Start LeGO-LOAM:
```bash
roslaunch lego_loam run.launch
```

**Terminal 2** - Play your bag file:
```bash
rosbag play /path/to/your.bag --clock
```

### Step 4: Analyze Logs

**Terminal 3** - Collect and analyze:
```bash
cd /workspace/logging_and_debugging
bash collect_logs.sh --run
```

---

## 📁 Key Locations

| Item | Location |
|------|----------|
| Log output | `/tmp/lego_loam_logs/lego_loam_debug.log` |
| Analysis tools | `/workspace/logging_and_debugging/` |
| Config file | `LeGO-LOAM/include/utility.h` |

---

## 🔧 Available Tools

### Real-time Log Viewer
```bash
# Watch logs live (like tail -f)
python3 view_logs.py -f

# Filter by node
python3 view_logs.py -f -n ImageProjection
python3 view_logs.py -f -n FeatureAssociation
python3 view_logs.py -f -n MapOptimization

# Show last N lines
python3 view_logs.py -l 50

# Show statistics
python3 view_logs.py -s
```

### Log Analysis
```bash
# Full automated analysis
bash collect_logs.sh --run

# Or separately:
bash collect_logs.sh --collect    # Archive logs
bash collect_logs.sh --analyze    # Analyze logs

# Manual analysis of specific file
python3 analyze_logs.py /tmp/lego_loam_logs/lego_loam_debug.log
```

### System Diagnostics
```bash
# Run inside container while LeGO-LOAM is active
bash check_status.sh
```

---

## 📊 Understanding Output

### Healthy Data Flow
```
Input: 28,000 → Segmented: 15,000 → Features: 320 ✓
```

### Problem Indicators
```
Input: 28,000 → Segmented: 15 → Features: 0 ✗  (Sensor config issue!)
```

---

## ⚡ Quick Troubleshooting

| Problem | Quick Fix |
|---------|-----------|
| Very few points (< 1000) | Check `N_SCAN` in utility.h matches your LIDAR (16/32/64/128) |
| No features detected | Verify sensor orientation and `groundScanInd` setting |
| Nodes not synchronized | Ensure bag plays with `--clock` flag |
| Logs not created | Enable both `LEGO_LOAM_DEBUG` and `LEGO_LOAM_FILE_DEBUG` |
| RViz empty | Set Fixed Frame to `map` or `camera_init`, enable displays |

---

## 🔗 More Details

For complete documentation, see: [01_DEBUGGING_GUIDE_2025-12-26.md](01_DEBUGGING_GUIDE_2025-12-26.md)
