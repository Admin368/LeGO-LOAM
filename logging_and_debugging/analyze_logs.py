#!/usr/bin/env python3
"""
LeGO-LOAM Log Analysis Tool
Analyzes debug logs to identify data flow issues and performance problems.
"""

import os
import sys
import re
from collections import defaultdict
from datetime import datetime

class LogAnalyzer:
    def __init__(self, log_file):
        self.log_file = log_file
        self.logs = []
        self.stats = defaultdict(lambda: {
            'count': 0,
            'samples': []
        })
        self.issues = []
        self.timeline = []

    def parse_logs(self):
        """Parse log file and extract structured data."""
        if not os.path.exists(self.log_file):
            print(f"❌ Log file not found: {self.log_file}")
            return False

        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    self.logs.append(line.strip())
            print(f"✓ Loaded {len(self.logs)} log entries")
            return True
        except Exception as e:
            print(f"❌ Error reading log file: {e}")
            return False

    def extract_point_counts(self):
        """Extract point cloud sizes at each stage."""
        print("\n" + "="*70)
        print("POINT CLOUD FLOW ANALYSIS")
        print("="*70)

        input_points = []
        ground_points = []
        segmented_points = []
        corner_points = []
        feature_counts = defaultdict(list)

        for log_line in self.logs:
            # ImageProjection: Input - handle [ImageProjection] format
            if "[ImageProjection]" in log_line and "Received point cloud with" in log_line:
                match = re.search(r'(\d+)\s+points', log_line)
                if match:
                    count = int(match.group(1))
                    input_points.append(count)
                    self.timeline.append(('INPUT', count, log_line))

            # ImageProjection: After PCL conversion
            elif "After conversion, PCL cloud has" in log_line:
                match = re.search(r'(\d+)\s+points', log_line)
                if match:
                    count = int(match.group(1))
                    self.timeline.append(('CONVERSION', count, log_line))

            # ImageProjection: Publishing
            elif "Publishing clouds - Ground:" in log_line:
                ground_match = re.search(r'Ground:\s*(\d+)', log_line)
                seg_match = re.search(r'Segmented:\s*(\d+)', log_line)
                if ground_match:
                    ground_points.append(int(ground_match.group(1)))
                    self.timeline.append(('GROUND', int(ground_match.group(1)), log_line))
                if seg_match:
                    segmented_points.append(int(seg_match.group(1)))
                    self.timeline.append(('SEGMENTED', int(seg_match.group(1)), log_line))

            # FeatureAssociation: Features
            elif "Publishing features" in log_line:
                sharp_match = re.search(r'Sharp corners:\s*(\d+)', log_line)
                flat_match = re.search(r'Flat surf:\s*(\d+)', log_line)
                if sharp_match:
                    corner_points.append(int(sharp_match.group(1)))
                    feature_counts['sharp_corners'].append(int(sharp_match.group(1)))
                if flat_match:
                    feature_counts['flat_surfaces'].append(int(flat_match.group(1)))
                self.timeline.append(('FEATURES', int(sharp_match.group(1)) if sharp_match else 0, log_line))

            # MapOptimization: Map state
            elif "Publishing global map with" in log_line:
                match = re.search(r'(\d+)\s+key poses', log_line)
                if match:
                    count = int(match.group(1))
                    self.timeline.append(('MAP_POSES', count, log_line))

            elif "Global map frame has" in log_line:
                match = re.search(r'(\d+)\s+points', log_line)
                if match:
                    count = int(match.group(1))
                    self.timeline.append(('MAP_POINTS', count, log_line))

        # Print analysis
        if input_points:
            print(f"\n📥 INPUT CLOUDS (ImageProjection):")
            print(f"   Total received: {len(input_points)}")
            print(f"   Min: {min(input_points):,}  Max: {max(input_points):,}  Avg: {sum(input_points)//len(input_points):,}")
            if any(p < 1000 for p in input_points):
                self.issues.append("⚠️  Very low input point counts detected (< 1000)")

        if segmented_points:
            print(f"\n🔍 SEGMENTED CLOUDS (ImageProjection output):")
            print(f"   Total published: {len(segmented_points)}")
            print(f"   Min: {min(segmented_points):,}  Max: {max(segmented_points):,}  Avg: {sum(segmented_points)//len(segmented_points):,}")
            
            if input_points and segmented_points:
                loss_percent = ((sum(input_points) - sum(segmented_points)) / sum(input_points) * 100) if sum(input_points) > 0 else 0
                print(f"   Loss in segmentation: {loss_percent:.1f}%")
                if loss_percent > 90:
                    self.issues.append("⚠️  CRITICAL: > 90% of points filtered out in segmentation!")

        if ground_points:
            print(f"\n🌍 GROUND CLOUDS:")
            print(f"   Total: {len(ground_points)}")
            print(f"   Min: {min(ground_points):,}  Max: {max(ground_points):,}  Avg: {sum(ground_points)//len(ground_points):,}")

        if corner_points:
            print(f"\n📌 FEATURE EXTRACTION (FeatureAssociation):")
            print(f"   Sharp corners: {len(corner_points)} messages")
            if corner_points:
                print(f"      Min: {min(corner_points)}  Max: {max(corner_points)}  Avg: {sum(corner_points)//len(corner_points)}")
                if all(c < 10 for c in corner_points):
                    self.issues.append("⚠️  Very few corner features detected (< 10 per frame)")

        if feature_counts['flat_surfaces']:
            print(f"   Flat surfaces: {len(feature_counts['flat_surfaces'])} messages")
            if feature_counts['flat_surfaces']:
                flat = feature_counts['flat_surfaces']
                print(f"      Min: {min(flat)}  Max: {max(flat)}  Avg: {sum(flat)//len(flat)}")

        return {
            'input': input_points,
            'ground': ground_points,
            'segmented': segmented_points,
            'corners': corner_points
        }

    def check_data_synchronization(self):
        """Check if all nodes are receiving data and synchronized."""
        print("\n" + "="*70)
        print("DATA SYNCHRONIZATION CHECK")
        print("="*70)

        nodes_seen = set()
        receive_counts = defaultdict(int)
        publish_counts = defaultdict(int)

        for log_line in self.logs:
            if "Received" in log_line:
                # Handle format: [ImageProjection] Received (with brackets)
                if "[ImageProjection]" in log_line and "Received" in log_line:
                    receive_counts['ImageProjection'] += 1
                    nodes_seen.add('ImageProjection')
                elif "[FeatureAssociation]" in log_line and "Received" in log_line:
                    receive_counts['FeatureAssociation'] += 1
                    nodes_seen.add('FeatureAssociation')
                elif "[MapOptimization]" in log_line and "Received" in log_line:
                    receive_counts['MapOptimization'] += 1
                    nodes_seen.add('MapOptimization')

            if "Publishing" in log_line:
                # Handle format: [ImageProjection] Publishing (with brackets)
                if "[ImageProjection]" in log_line and "Publishing" in log_line:
                    publish_counts['ImageProjection'] += 1
                elif "[FeatureAssociation]" in log_line and "Publishing" in log_line:
                    publish_counts['FeatureAssociation'] += 1
                elif "[MapOptimization]" in log_line and "Publishing" in log_line:
                    publish_counts['MapOptimization'] += 1

        print(f"\n📡 Nodes detected: {', '.join(sorted(nodes_seen))}")
        
        print(f"\n📥 Data Reception:")
        for node, count in sorted(receive_counts.items()):
            status = "✓" if count > 0 else "✗"
            print(f"   {status} {node}: {count} messages")

        print(f"\n📤 Data Publishing:")
        for node, count in sorted(publish_counts.items()):
            status = "✓" if count > 0 else "✗"
            print(f"   {status} {node}: {count} messages")

        # Check for data flow issues
        if receive_counts['ImageProjection'] == 0:
            self.issues.append("❌ ImageProjection not receiving input data")
        if receive_counts['FeatureAssociation'] == 0:
            self.issues.append("❌ FeatureAssociation not receiving data")
        if receive_counts['MapOptimization'] == 0:
            self.issues.append("❌ MapOptimization not receiving data")

        # Check for message mismatches
        if abs(receive_counts.get('FeatureAssociation', 0) - publish_counts.get('ImageProjection', 0)) > 2:
            self.issues.append("⚠️  Possible synchronization issue between ImageProjection and FeatureAssociation")

    def analyze_performance(self):
        """Analyze processing performance and latency."""
        print("\n" + "="*70)
        print("PERFORMANCE ANALYSIS")
        print("="*70)

        # Extract timestamps
        timestamps = []
        for log_line in self.logs:
            # Parse timestamp format: [YYYY-MM-DD HH:MM:SS.mmm]
            match = re.match(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\]', log_line)
            if match:
                try:
                    ts = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S.%f")
                    timestamps.append(ts)
                except:
                    pass

        if len(timestamps) > 1:
            start = timestamps[0]
            end = timestamps[-1]
            duration = (end - start).total_seconds()
            msg_rate = len(self.logs) / duration if duration > 0 else 0
            
            print(f"\n⏱️  Log Duration: {duration:.2f} seconds")
            print(f"📊 Average Message Rate: {msg_rate:.1f} messages/sec")
            print(f"📝 Total Log Entries: {len(self.logs)}")

        print("\n✓ Performance metrics extracted")

    def print_summary(self):
        """Print summary and recommendations."""
        print("\n" + "="*70)
        print("SUMMARY & RECOMMENDATIONS")
        print("="*70)

        if not self.issues:
            print("\n✓ No critical issues detected!")
            print("  → Data pipeline appears to be functioning normally")
            print("  → All nodes are receiving and publishing data")
        else:
            print(f"\n⚠️  Found {len(self.issues)} issue(s):\n")
            for i, issue in enumerate(self.issues, 1):
                print(f"  {i}. {issue}")

            print("\n📋 RECOMMENDED ACTIONS:")
            if any("Very low input" in issue for issue in self.issues):
                print("  • Check sensor configuration in utility.h")
                print("  • Verify N_SCAN matches your LIDAR sensor")
                print("  • Check sensorMinimumRange and angle parameters")
            
            if any("filtered out" in issue for issue in self.issues):
                print("  • Review ground removal settings (groundScanInd)")
                print("  • Adjust segmentation parameters in utility.h")
                print("  • Check if sensor orientation is correct")
            
            if any("few corner" in issue for issue in self.issues):
                print("  • Verify input has sufficient features")
                print("  • Check feature extraction thresholds")
                print("  • Increase corner feature sensitivity")

        print("\n" + "="*70 + "\n")

    def run(self):
        """Run complete analysis."""
        print("\n🔍 LeGO-LOAM Log Analysis Tool")
        print("="*70)
        
        if not self.parse_logs():
            return False

        self.extract_point_counts()
        self.check_data_synchronization()
        self.analyze_performance()
        self.print_summary()

        return True


def main():
    log_file = "/tmp/lego_loam_logs/lego_loam_debug.log"
    
    if len(sys.argv) > 1:
        log_file = sys.argv[1]

    analyzer = LogAnalyzer(log_file)
    success = analyzer.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
