#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bag File Sensor Analysis Tool (Python 2 compatible)
Analyzes the point cloud data in a bag file to determine:
1. Actual sensor type and configuration
2. Point distribution across scan lines
3. Vertical angle range
4. Recommended LeGO-LOAM parameters
"""

from __future__ import print_function
import rosbag
import struct
import sys
import os
import math
from collections import defaultdict

def analyze_point_cloud(bag_path, topic='/velodyne_points', max_frames=5):
    """Analyze point cloud data from bag file."""
    
    print("\n" + "="*70)
    print("BAG FILE SENSOR ANALYSIS")
    print("="*70)
    print("\nAnalyzing: {}".format(bag_path))
    print("Topic: {}".format(topic))
    print("Max frames to analyze: {}".format(max_frames))
    
    if not os.path.exists(bag_path):
        print("ERROR: Bag file not found: {}".format(bag_path))
        return None
    
    try:
        bag = rosbag.Bag(bag_path, 'r')
    except Exception as e:
        print("ERROR: Error opening bag: {}".format(e))
        return None
    
    # Get bag info
    info = bag.get_type_and_topic_info()
    topics = info.topics
    
    print("\n" + "="*70)
    print("BAG FILE INFO")
    print("="*70)
    
    print("\nTopics in bag:")
    for t, tinfo in topics.items():
        print("  {}: {} messages, type: {}".format(t, tinfo.message_count, tinfo.msg_type))
    
    if topic not in topics:
        print("\nERROR: Topic {} not found in bag!".format(topic))
        print("Available topics: {}".format(list(topics.keys())))
        bag.close()
        return None
    
    # Analyze point clouds
    print("\n" + "="*70)
    print("POINT CLOUD ANALYSIS")
    print("="*70)
    
    frame_count = 0
    all_stats = []
    ring_distributions = []
    vertical_angles_all = []
    
    for topic_name, msg, t in bag.read_messages(topics=[topic]):
        if frame_count >= max_frames:
            break
        
        frame_count += 1
        print("\n--- Frame {} ---".format(frame_count))
        
        # Parse point cloud
        stats = analyze_single_cloud(msg)
        if stats:
            all_stats.append(stats)
            if 'ring_counts' in stats:
                ring_distributions.append(stats['ring_counts'])
            if 'vertical_angles' in stats:
                vertical_angles_all.extend(stats['vertical_angles'])
    
    bag.close()
    
    if not all_stats:
        print("\nERROR: No valid point cloud data found!")
        return None
    
    # Aggregate analysis
    print("\n" + "="*70)
    print("AGGREGATED STATISTICS")
    print("="*70)
    
    avg_points = sum([s['num_points'] for s in all_stats]) / len(all_stats)
    print("\nAverage points per frame: {:,.0f}".format(avg_points))
    
    # Analyze ring values if present
    if ring_distributions:
        print("\n--- Ring Analysis (scan line detection) ---")
        combined_rings = defaultdict(int)
        for rd in ring_distributions:
            for ring, count in rd.items():
                combined_rings[ring] += count
        
        unique_rings = sorted(combined_rings.keys())
        print("Unique ring values found: {}".format(len(unique_rings)))
        print("Ring range: {} to {}".format(min(unique_rings), max(unique_rings)))
        
        if len(unique_rings) <= 64:
            print("\nRing distribution:")
            for ring in unique_rings:
                avg_count = combined_rings[ring] / len(ring_distributions)
                print("  Ring {:2d}: ~{:,.0f} points/frame".format(ring, avg_count))
    
    # Analyze vertical angles
    if vertical_angles_all:
        print("\n--- Vertical Angle Analysis ---")
        angles = vertical_angles_all
        min_angle = min(angles)
        max_angle = max(angles)
        print("Min vertical angle: {:.2f} deg".format(min_angle))
        print("Max vertical angle: {:.2f} deg".format(max_angle))
        print("Angle range: {:.2f} deg".format(max_angle - min_angle))
        
        # Estimate number of scan lines from angle distribution
        # Simple histogram
        num_bins = 128
        bin_size = (max_angle - min_angle) / num_bins
        bins = [0] * num_bins
        for a in angles:
            bin_idx = int((a - min_angle) / bin_size)
            if bin_idx >= num_bins:
                bin_idx = num_bins - 1
            bins[bin_idx] += 1
        
        non_empty_bins = sum(1 for b in bins if b > 50)
        print("Estimated scan lines (from angle distribution): ~{}".format(non_empty_bins))
    
    # Generate recommendations
    print("\n" + "="*70)
    print("SENSOR DETECTION & RECOMMENDATIONS")
    print("="*70)
    
    generate_recommendations(all_stats, ring_distributions, vertical_angles_all)
    
    return all_stats


def analyze_single_cloud(msg):
    """Analyze a single PointCloud2 message."""
    
    stats = {
        'num_points': msg.width * msg.height,
        'width': msg.width,
        'height': msg.height,
        'point_step': msg.point_step,
        'row_step': msg.row_step,
        'is_dense': msg.is_dense,
        'fields': [(f.name, f.offset, f.datatype) for f in msg.fields]
    }
    
    print("Points: {:,}".format(stats['num_points']))
    print("Dimensions: {} x {}".format(msg.width, msg.height))
    print("Fields: {}".format([f.name for f in msg.fields]))
    print("Point step: {} bytes".format(msg.point_step))
    
    # Check for ring field
    ring_field = None
    x_offset = y_offset = z_offset = None
    intensity_offset = None
    
    for f in msg.fields:
        if f.name == 'ring':
            ring_field = f
        elif f.name == 'x':
            x_offset = f.offset
        elif f.name == 'y':
            y_offset = f.offset
        elif f.name == 'z':
            z_offset = f.offset
        elif f.name == 'intensity':
            intensity_offset = f.offset
    
    # Sample points for analysis
    sample_size = min(10000, stats['num_points'])
    step = max(1, stats['num_points'] // sample_size)
    sample_indices = range(0, stats['num_points'], step)[:sample_size]
    
    x_vals = []
    y_vals = []
    z_vals = []
    ring_counts = defaultdict(int)
    vertical_angles = []
    
    data = msg.data
    
    for idx in sample_indices:
        offset = idx * msg.point_step
        
        try:
            x = struct.unpack_from('f', data, offset + x_offset)[0]
            y = struct.unpack_from('f', data, offset + y_offset)[0]
            z = struct.unpack_from('f', data, offset + z_offset)[0]
            
            # Skip invalid points
            if math.isnan(x) or math.isnan(y) or math.isnan(z):
                continue
            if x == 0 and y == 0 and z == 0:
                continue
                
            x_vals.append(x)
            y_vals.append(y)
            z_vals.append(z)
            
            # Calculate vertical angle
            range_xy = math.sqrt(x*x + y*y)
            if range_xy > 0.1:  # Avoid division by zero
                vert_angle = math.atan2(z, range_xy) * 180 / math.pi
                vertical_angles.append(vert_angle)
            
            # Extract ring if available
            if ring_field:
                if ring_field.datatype == 2:  # UINT8
                    ring = struct.unpack_from('B', data, offset + ring_field.offset)[0]
                elif ring_field.datatype == 4:  # UINT16
                    ring = struct.unpack_from('H', data, offset + ring_field.offset)[0]
                elif ring_field.datatype == 5:  # INT32
                    ring = struct.unpack_from('i', data, offset + ring_field.offset)[0]
                else:
                    ring = struct.unpack_from('H', data, offset + ring_field.offset)[0]
                ring_counts[ring] += 1
                
        except Exception as e:
            continue
    
    if x_vals:
        # Calculate ranges
        ranges = [math.sqrt(x*x + y*y + z*z) for x, y, z in zip(x_vals, y_vals, z_vals)]
        
        print("Valid sampled points: {:,}".format(len(x_vals)))
        print("Range - Min: {:.2f}m, Max: {:.2f}m, Avg: {:.2f}m".format(
            min(ranges), max(ranges), sum(ranges)/len(ranges)))
        print("Z range: {:.2f}m to {:.2f}m".format(min(z_vals), max(z_vals)))
        
        if vertical_angles:
            print("Vertical angles: {:.1f} deg to {:.1f} deg".format(
                min(vertical_angles), max(vertical_angles)))
            stats['vertical_angles'] = vertical_angles
    
    if ring_field:
        print("Ring field present: YES")
        print("Unique rings: {}".format(len(ring_counts)))
        stats['ring_counts'] = dict(ring_counts)
        stats['has_ring'] = True
    else:
        print("Ring field present: NO")
        stats['has_ring'] = False
    
    return stats


def generate_recommendations(all_stats, ring_distributions, vertical_angles_all):
    """Generate sensor configuration recommendations."""
    
    # Detect sensor type
    detected_sensor = "Unknown"
    n_scan = 16
    ang_bottom = 15.0
    ang_res_y = 2.0
    ground_scan_ind = 7
    
    # Check ring field
    has_ring = all_stats[0].get('has_ring', False) if all_stats else False
    
    if ring_distributions:
        combined_rings = defaultdict(int)
        for rd in ring_distributions:
            for ring, count in rd.items():
                combined_rings[ring] += count
        unique_rings = sorted(combined_rings.keys())
        num_rings = len(unique_rings)
        
        if num_rings == 16:
            detected_sensor = "VLP-16"
            n_scan = 16
            ang_res_y = 2.0
            ang_bottom = 15.0
            ground_scan_ind = 7
        elif num_rings == 32:
            detected_sensor = "HDL-32E"
            n_scan = 32
            ang_res_y = 41.33/31
            ang_bottom = 30.67
            ground_scan_ind = 20
        elif num_rings == 64:
            detected_sensor = "HDL-64E"
            n_scan = 64
            ang_res_y = 0.4
            ang_bottom = 24.9
            ground_scan_ind = 50
        elif num_rings == 128:
            detected_sensor = "VLS-128"
            n_scan = 128
            ang_res_y = 0.3
            ang_bottom = 25.0
            ground_scan_ind = 10
        else:
            detected_sensor = "Custom ({} rings)".format(num_rings)
            n_scan = num_rings
    
    # If no ring field, estimate from vertical angles
    elif vertical_angles_all:
        angles = vertical_angles_all
        angle_min = min(angles)
        angle_max = max(angles)
        angle_range = angle_max - angle_min
        
        # Estimate number of scan lines using histogram
        num_bins = 200
        bin_size = (angle_max - angle_min) / num_bins if angle_max != angle_min else 1
        hist = [0] * num_bins
        for a in angles:
            bin_idx = int((a - angle_min) / bin_size)
            if bin_idx >= num_bins:
                bin_idx = num_bins - 1
            hist[bin_idx] += 1
        
        threshold = len(angles) / 500
        significant_bins = sum(1 for h in hist if h > threshold)
        
        print("\nNo ring field - estimating from vertical angles:")
        print("  Angle range: {:.1f} deg to {:.1f} deg".format(angle_min, angle_max))
        print("  Total span: {:.1f} deg".format(angle_range))
        print("  Estimated scan lines: {}".format(significant_bins))
        
        # Guess sensor
        if significant_bins <= 18:
            detected_sensor = "VLP-16 (estimated)"
            n_scan = 16
            ang_res_y = 2.0
            ang_bottom = abs(angle_min) + 0.1
            ground_scan_ind = 7
        elif significant_bins <= 36:
            detected_sensor = "HDL-32E (estimated)"
            n_scan = 32
            ang_res_y = angle_range / 31
            ang_bottom = abs(angle_min) + 0.1
            ground_scan_ind = int(n_scan * 0.6)
        elif significant_bins <= 70:
            detected_sensor = "HDL-64E (estimated)"
            n_scan = 64
            ang_res_y = angle_range / 63
            ang_bottom = abs(angle_min) + 0.1
            ground_scan_ind = int(n_scan * 0.7)
        else:
            detected_sensor = "VLS-128 (estimated)"
            n_scan = 128
            ang_res_y = angle_range / 127
            ang_bottom = abs(angle_min) + 0.1
            ground_scan_ind = int(n_scan * 0.08)
    
    print("\n*** DETECTED SENSOR: {} ***".format(detected_sensor))
    print("    Ring field available: {}".format('Yes' if has_ring else 'No'))
    
    print("\n" + "="*50)
    print("RECOMMENDED utility.h CONFIGURATION:")
    print("="*50)
    print("""
// Detected: {}
extern const bool useCloudRing = {};
extern const int N_SCAN = {};
extern const int Horizon_SCAN = 1800;
extern const float ang_res_x = 0.2;
extern const float ang_res_y = {:.2f};
extern const float ang_bottom = {:.1f};
extern const int groundScanInd = {};
""".format(
        detected_sensor,
        'true' if has_ring else 'false',
        n_scan,
        ang_res_y,
        ang_bottom,
        ground_scan_ind
    ))
    
    print("IMPORTANT NOTES:")
    if has_ring:
        print("  * Ring field IS present - set useCloudRing = true for best results")
    else:
        print("  * Ring field NOT present - using angle-based row calculation")
        print("  * Verify ang_bottom matches your sensor's lowest beam angle")
    
    print("\nNEXT STEPS:")
    print("  1. Update utility.h with the above configuration")
    print("  2. Rebuild: cd /catkin_ws && catkin_make")
    print("  3. Re-run and check logs for Ground point counts")
    
    return {
        'sensor': detected_sensor,
        'n_scan': n_scan,
        'ang_res_y': ang_res_y,
        'ang_bottom': ang_bottom,
        'ground_scan_ind': ground_scan_ind,
        'use_cloud_ring': has_ring
    }


def main():
    # Default bag path
    bag_path = "/workspace/data/2017-06-08-15-51-45_2.bag"
    topic = "/velodyne_points"
    
    if len(sys.argv) > 1:
        bag_path = sys.argv[1]
    if len(sys.argv) > 2:
        topic = sys.argv[2]
    
    analyze_point_cloud(bag_path, topic, max_frames=5)


if __name__ == "__main__":
    main()
