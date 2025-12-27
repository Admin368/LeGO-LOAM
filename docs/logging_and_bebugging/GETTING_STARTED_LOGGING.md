# Getting Started with File-Based Logging - Step by Step

## 📋 Quick Checklist

This checklist walks you through setting up and using the file-based logging system for your debugging session.

### Setup Phase

- [ ] **Step 1:** Read `FILE_LOGGING_QUICKREF.txt` for overview
- [ ] **Step 2:** Enable debug logging in code
- [ ] **Step 3:** Rebuild the project
- [ ] **Step 4:** Verify log directory exists

### Execution Phase

- [ ] **Step 5:** Start LeGO-LOAM with logging enabled
- [ ] **Step 6:** Play your bag file with `--clock` flag
- [ ] **Step 7:** Monitor logs in real-time (optional)
- [ ] **Step 8:** Stop execution after 30-60 seconds of data

### Analysis Phase

- [ ] **Step 9:** Collect and analyze logs
- [ ] **Step 10:** Review analysis output
- [ ] **Step 11:** Identify issues and fixes
- [ ] **Step 12:** Document findings

---

## 🚀 Detailed Steps

### **STEP 1: Read Quick Reference** (2 minutes)

Open and skim:
```bash
cat FILE_LOGGING_QUICKREF.txt
```

This gives you the executive summary of all tools and commands.

---

### **STEP 2: Enable Debug Logging** (2 minutes)

Edit the file that contains debug configuration:
```bash
nano LeGO-LOAM/include/utility.h
```

Find these lines (around line 50):
```cpp
#define LEGO_LOAM_DEBUG 1              // 1 = ON, 0 = OFF
#define LEGO_LOAM_FILE_DEBUG 1         // 1 = ON, 0 = OFF
```

Make sure BOTH are set to `1`. Save and close.

---

### **STEP 3: Rebuild Project** (5-10 minutes)

```bash
cd /catkin_ws
catkin_make
source devel/setup.bash
```

Wait for build to complete. Should see:
```
[100%] Built target lego_loam
```

---

### **STEP 4: Verify Setup** (1 minute)

Check that log directory can be created:
```bash
mkdir -p /tmp/lego_loam_logs
ls -la /tmp/lego_loam_logs/
```

Should show an empty directory.

---

### **STEP 5: Start LeGO-LOAM** (Ongoing)

Open a terminal in your Docker container and run:

```bash
roslaunch lego_loam run.launch
```

You should see:
- ROS node output
- **[DEBUG]** messages appearing in console
- Similar output to:
```
[DEBUG] ImageProjection: Received point cloud with 28000 points
[DEBUG] FeatureAssociation: Received segmented cloud with 15234 points
[DEBUG] MapOptimization: Publishing global map with 12 key poses
```

**Keep this terminal running.** Do not close it.

---

### **STEP 6: Play Bag File** (In new terminal)

In a new terminal:

```bash
rosbag play /workspace/data/2017-06-08-15-51-45_2.bag --clock
```

**Important:** Use `--clock` flag so timing is synchronized.

Watch the bag file play. You should see messages like:
```
[ 99.123] Playing /workspace/data/2017-06-08-15-51-45_2.bag
Waiting 0.1 seconds after /clock time jumps...
[ROSBAG PLAY] Topic /velodyne_points
...
```

**Keep both terminals running** (LeGO-LOAM and rosbag play).

---

### **STEP 7: Monitor Logs (Optional)** (In new terminal)

While everything is running, you can optionally watch logs in real-time:

```bash
python3 view_logs.py -f
```

This will show live log entries as they're written. You'll see:
```
14:30:45 [DEBUG] [ImageProjection] Received point cloud with 28000 points
14:30:45 [DEBUG] [FeatureAssociation] Received segmented cloud with 15234 points
14:30:45 [DEBUG] [MapOptimization] Publishing features - Sharp corners: 320
```

**Colors indicate node:**
- 🟢 Green = ImageProjection
- 🟣 Magenta = FeatureAssociation  
- 🟦 Cyan = MapOptimization
- 🟨 Yellow = TransformFusion

To stop monitoring: `Ctrl+C`

---

### **STEP 8: Stop Execution** (When ready)

Let the bag file play for **30-60 seconds** (or until it completes).

Then stop in this order:

1. **Terminal with rosbag play:** `Ctrl+C` to stop playback
2. **Terminal with LeGO-LOAM:** `Ctrl+C` to stop node
3. **Terminal with log viewer (if running):** `Ctrl+C` to stop monitoring

All three should cleanly shut down.

---

### **STEP 9: Collect and Analyze Logs** (In new terminal)

Now collect the logs you just recorded and analyze them:

```bash
cd /workspace
bash collect_logs.sh --run
```

This will:
1. ✓ Copy logs from `/tmp/lego_loam_logs/` to timestamped session folder
2. ✓ Run automated analysis
3. ✓ Display results and recommendations

Output will look like:

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

... [more analysis] ...
```

**This is the key output!** This shows exactly what's happening in your system.

---

### **STEP 10: Review Analysis** (5 minutes)

Look at the four main sections:

1. **POINT CLOUD FLOW ANALYSIS**
   - Are point counts reasonable?
   - Is loss percentage acceptable (< 50%)?
   - Are features being detected?

2. **DATA SYNCHRONIZATION CHECK**
   - Do all nodes show received messages?
   - Are counts similar across nodes?

3. **PERFORMANCE ANALYSIS**
   - How long did the log capture last?
   - What's the message rate?

4. **SUMMARY & RECOMMENDATIONS**
   - Any issues detected?
   - What are the recommended fixes?

---

### **STEP 11: Identify Issues** (5-10 minutes)

Based on the analysis, you'll see one of these patterns:

**✓ Healthy System:**
```
✓ No critical issues detected!
  → Data pipeline appears to be functioning normally
  → All nodes are receiving and publishing data
```

**⚠️ Problem: Sensor Configuration**
```
⚠️  > 90% of points filtered out in segmentation!

RECOMMENDED ACTIONS:
  • Check sensor configuration in utility.h
  • Verify N_SCAN matches your LIDAR sensor
```

**❌ Problem: No Features**
```
⚠️  Very few corner features detected (< 10 per frame)

RECOMMENDED ACTIONS:
  • Verify input has sufficient features
  • Check feature extraction thresholds
  • Increase corner feature sensitivity
```

**❌ Problem: Data Not Flowing**
```
❌ FeatureAssociation not receiving data
❌ MapOptimization not receiving data
```

---

### **STEP 12: Document Findings** (5 minutes)

Create a simple text file summarizing what you found:

```bash
cat > debug_session_results.txt << 'EOF'
LeGO-LOAM Debug Session Results
================================
Date: 2025-12-26
Bag File: 2017-06-08-15-51-45_2.bag
LIDAR Type: [VLP-16 / HDL-32E / Other]

FINDINGS:
---------
[Copy key metrics from analysis]
Input points: 28,000
Segmented points: 15,000
Features: 320 sharp corners

ISSUES IDENTIFIED:
------------------
[List any issues found]
- Example: Points dropping from 28k to 100 indicates sensor config issue

RECOMMENDED NEXT STEPS:
----------------------
[Copy recommendations from analysis output]
1. Check N_SCAN parameter in utility.h
2. Verify sensor matches configuration
3. Rebuild and re-test

EOF
cat debug_session_results.txt
```

---

## 🎯 Expected Workflows

### **Workflow A: Quick Health Check** (15 minutes)

```bash
# 1. Start LeGO-LOAM (Terminal 1)
roslaunch lego_loam run.launch

# 2. Play bag file (Terminal 2)  
rosbag play data.bag --clock

# 3. Wait 60 seconds, then stop both
# Ctrl+C in both terminals

# 4. Quick analysis (Terminal 3)
bash collect_logs.sh --run

# 5. Review output for issues
```

### **Workflow B: Real-time Monitoring** (30 minutes)

```bash
# 1. Start LeGO-LOAM (Terminal 1)
roslaunch lego_loam run.launch

# 2. Watch logs live (Terminal 2)
python3 view_logs.py -f -n ImageProjection

# 3. In another terminal - watch features (Terminal 3)
python3 view_logs.py -f -n FeatureAssociation

# 4. Play bag file (Terminal 4)
rosbag play data.bag --clock

# 5. Observe real-time data flow
# Stop and collect logs when done
bash collect_logs.sh --run
```

### **Workflow C: Filter by Node** (15 minutes)

```bash
# Start system and let it run (as above)

# View only specific node logs:
python3 view_logs.py -f -n MapOptimization

# Or show statistics:
python3 view_logs.py -s

# Or show last 100 lines:
python3 view_logs.py -l 100
```

---

## 📊 Interpreting Common Results

### Result 1: Healthy Data Flow
```
INPUT: 28,000 → SEGMENTED: 15,000 → FEATURES: 320 ✓
```
**Interpretation:** System working normally. Points processed as expected.

### Result 2: Aggressive Ground Removal
```
INPUT: 28,000 → GROUND: 5,000 → SEGMENTED: 20,000 → FEATURES: 150
```
**Interpretation:** About 18% of points removed as ground (reasonable).

### Result 3: Sensor Config Issue
```
INPUT: 28,000 → SEGMENTED: 15 → FEATURES: 0 ✗
```
**Interpretation:** Something wrong with sensor parameters. Check N_SCAN in utility.h.

### Result 4: Weak Signal
```
INPUT: 28,000 → SEGMENTED: 15,000 → FEATURES: 0 ✗
```
**Interpretation:** Features not detected despite adequate input. Check sensor quality or feature thresholds.

---

## 🛠️ Troubleshooting

### Problem: No log file created
```bash
# Check if directory exists
ls -la /tmp/lego_loam_logs/

# Check debug is enabled
grep "LEGO_LOAM_DEBUG\|LEGO_LOAM_FILE_DEBUG" LeGO-LOAM/include/utility.h

# Rebuild if needed
catkin_make
```

### Problem: Log file empty
```bash
# Make sure LeGO-LOAM got data
# Try: python3 view_logs.py -l 20
# Should show some lines even if few

# Check that bag file was played with --clock
```

### Problem: Can't analyze - script not found
```bash
# Make sure you're in right directory
pwd  # Should be /workspace

# Check analyze_logs.py exists
ls -la analyze_logs.py

# Try full path if needed
python3 /workspace/analyze_logs.py /tmp/lego_loam_logs/lego_loam_debug.log
```

---

## ✅ After Debugging is Complete

Once you've identified and fixed your issues:

1. **Disable logging:**
   ```cpp
   #define LEGO_LOAM_DEBUG 0
   #define LEGO_LOAM_FILE_DEBUG 0
   ```

2. **Rebuild:**
   ```bash
   catkin_make
   ```

3. **Archive your logs for reference:**
   ```bash
   tar czf lego_loam_debug_archive.tar.gz lego_loam_debug_session/
   ```

---

## 📚 For More Information

- **Quick Commands:** See `FILE_LOGGING_QUICKREF.txt`
- **Full Documentation:** See `docs/FILE_BASED_LOGGING.md`
- **Analysis Details:** See `FILE_BASED_LOGGING_SUMMARY.md`

---

## 🎓 Summary

You now have tools to:

1. ✅ **Capture** - Automatically log all debug data to disk
2. ✅ **Monitor** - Watch logs in real-time while system runs
3. ✅ **Analyze** - Automatically identify issues and problems
4. ✅ **Share** - Archive logs for remote debugging help
5. ✅ **Fix** - Get specific recommendations for issues

**The next time you run into problems, you'll have concrete data showing exactly what's happening!**
