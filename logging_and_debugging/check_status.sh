#!/bin/bash
# LeGO-LOAM Diagnostic Script
# Run this inside the Docker container to check system status

echo "========================================="
echo "LeGO-LOAM Diagnostic Report"
echo "========================================="
echo ""

# Check if ROS master is running
echo "1. ROS Master Status:"
if rostopic list > /dev/null 2>&1; then
    echo "   ✓ ROS master is running"
else
    echo "   ✗ ROS master is NOT running"
    echo "   Run: roslaunch lego_loam run.launch"
    exit 1
fi
echo ""

# Check active topics
echo "2. Active Topics:"
TOPIC_COUNT=$(rostopic list 2>/dev/null | wc -l)
echo "   Total topics: $TOPIC_COUNT"
echo ""

# Check key input topics
echo "3. Input Topics Status:"
for topic in /velodyne_points /imu/data; do
    if rostopic list 2>/dev/null | grep -q "^${topic}$"; then
        RATE=$(timeout 3 rostopic hz $topic 2>&1 | grep "average rate:" | awk '{print $3}')
        if [ -z "$RATE" ]; then
            echo "   ⚠ $topic - EXISTS but NO DATA"
        else
            echo "   ✓ $topic - Publishing at ${RATE} Hz"
        fi
    else
        echo "   ✗ $topic - NOT FOUND"
    fi
done
echo ""

# Check LeGO-LOAM processing topics
echo "4. Processing Topics Status:"
for topic in /full_cloud_projected /segmented_cloud /laser_cloud_less_sharp /laser_cloud_less_flat; do
    if rostopic list 2>/dev/null | grep -q "^${topic}$"; then
        # Try to get message count
        MSG_INFO=$(timeout 2 rostopic echo $topic --noarr 2>&1 | head -5)
        if echo "$MSG_INFO" | grep -q "header:"; then
            echo "   ✓ $topic - Publishing data"
        else
            echo "   ⚠ $topic - Exists but no data yet"
        fi
    else
        echo "   ✗ $topic - NOT FOUND"
    fi
done
echo ""

# Check output topics
echo "5. Output Topics Status:"
for topic in /laser_cloud_surround /registered_cloud /laser_odom_to_init; do
    if rostopic list 2>/dev/null | grep -q "^${topic}$"; then
        echo "   ✓ $topic - EXISTS"
    else
        echo "   ✗ $topic - NOT FOUND"
    fi
done
echo ""

# Check TF
echo "6. Transform (TF) Status:"
if rostopic list 2>/dev/null | grep -q "^/tf$"; then
    TF_COUNT=$(timeout 2 rostopic echo /tf --noarr 2>&1 | grep "frame_id:" | wc -l)
    if [ "$TF_COUNT" -gt 0 ]; then
        echo "   ✓ TF transforms publishing ($TF_COUNT transforms in 2 sec)"
    else
        echo "   ⚠ /tf topic exists but no transforms yet"
    fi
else
    echo "   ✗ /tf topic NOT FOUND"
fi
echo ""

# Check for running nodes
echo "7. Running Nodes:"
rosnode list 2>/dev/null | grep -E "(imageProjection|featureAssociation|mapOptmization|transformFusion)" | while read node; do
    echo "   ✓ $node"
done
echo ""

# Check point cloud sizes
echo "8. Point Cloud Diagnostics:"
echo "   Checking /velodyne_points..."
PC_INFO=$(timeout 3 rostopic echo /velodyne_points --noarr 2>&1 | grep -E "(width|height):" | head -2)
if [ ! -z "$PC_INFO" ]; then
    WIDTH=$(echo "$PC_INFO" | grep "width:" | awk '{print $2}')
    HEIGHT=$(echo "$PC_INFO" | grep "height:" | awk '{print $2}')
    TOTAL=$((WIDTH * HEIGHT))
    echo "   Input cloud: ${WIDTH} x ${HEIGHT} = ${TOTAL} points"
    
    if [ "$TOTAL" -lt 1000 ]; then
        echo "   ⚠ WARNING: Very few input points!"
    fi
else
    echo "   ⚠ Could not read point cloud data"
fi
echo ""

echo "   Checking /segmented_cloud..."
SEG_INFO=$(timeout 3 rostopic echo /segmented_cloud --noarr 2>&1 | grep -E "(width|height):" | head -2)
if [ ! -z "$SEG_INFO" ]; then
    WIDTH=$(echo "$SEG_INFO" | grep "width:" | awk '{print $2}')
    HEIGHT=$(echo "$SEG_INFO" | grep "height:" | awk '{print $2}')
    TOTAL=$((WIDTH * HEIGHT))
    echo "   Segmented cloud: ${WIDTH} x ${HEIGHT} = ${TOTAL} points"
    
    if [ "$TOTAL" -lt 100 ]; then
        echo "   ⚠ WARNING: Very few segmented points! Check sensor params in utility.h"
    fi
else
    echo "   ⚠ Could not read segmented cloud data"
fi
echo ""

# Check for debug logs
echo "9. Debug Logging Status:"
if rostopic echo /rosout --noarr 2>&1 | timeout 2 grep -q "\[DEBUG\]"; then
    echo "   ✓ Debug logs are ENABLED"
else
    echo "   ⚠ Debug logs are DISABLED or no recent messages"
    echo "   To enable: Set LEGO_LOAM_DEBUG to 1 in utility.h and rebuild"
fi
echo ""

# Summary
echo "========================================="
echo "Summary:"
echo "========================================="

ISSUES=0

# Count issues
if ! rostopic list 2>/dev/null | grep -q "^/velodyne_points$"; then
    echo "✗ Input topic /velodyne_points missing"
    ISSUES=$((ISSUES + 1))
fi

if ! rostopic list 2>/dev/null | grep -q "^/segmented_cloud$"; then
    echo "✗ Processing topic /segmented_cloud missing"
    ISSUES=$((ISSUES + 1))
fi

if ! rostopic list 2>/dev/null | grep -q "^/laser_cloud_surround$"; then
    echo "✗ Output topic /laser_cloud_surround missing"
    ISSUES=$((ISSUES + 1))
fi

if [ "$ISSUES" -eq 0 ]; then
    echo "✓ All critical topics found!"
    echo ""
    echo "If RViz is still empty:"
    echo "1. Check RViz Fixed Frame is set to 'map' or 'camera_init'"
    echo "2. Enable displays in RViz left panel"
    echo "3. Check Global Status in RViz for errors"
    echo "4. Wait 10-20 seconds for data to accumulate"
    echo "5. Review /workspaces/LeGO-LOAM/docs/DEBUGGING_GUIDE.md"
else
    echo ""
    echo "⚠ Found $ISSUES critical issue(s)"
    echo "See DEBUGGING_GUIDE.md for troubleshooting steps"
fi

echo ""
echo "========================================="
