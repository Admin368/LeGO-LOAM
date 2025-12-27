#!/usr/bin/env python3
"""
LeGO-LOAM Log Viewer - Real-time log display and filtering
Helps visualize log flow while LeGO-LOAM is running
"""

import os
import sys
import time
import argparse
from datetime import datetime
from collections import defaultdict

class LogViewer:
    def __init__(self, log_file, follow=False, node_filter=None):
        self.log_file = log_file
        self.follow = follow
        self.node_filter = node_filter
        self.last_position = 0
        self.last_check = time.time()

    def colorize(self, text, level):
        """Add color to log level."""
        if level == "DEBUG":
            return f"\033[94m[DEBUG]\033[0m {text}"  # Blue
        elif level == "ERROR":
            return f"\033[91m[ERROR]\033[0m {text}"  # Red
        elif level == "WARN":
            return f"\033[93m[WARN ]\033[0m {text}"  # Yellow
        else:
            return f"[INFO ] {text}"

    def parse_log_line(self, line):
        """Parse a single log line."""
        import re
        # Format: [YYYY-MM-DD HH:MM:SS.mmm] [LEVEL] [NODE] Message
        pattern = r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\] \[(\w+)\] \[([^\]]+)\] (.+)'
        match = re.match(pattern, line)
        if match:
            timestamp, level, node, message = match.groups()
            return {
                'timestamp': timestamp,
                'level': level,
                'node': node,
                'message': message
            }
        return None

    def display_line(self, line):
        """Display a single log line with optional filtering."""
        parsed = self.parse_log_line(line)
        if not parsed:
            print(line)
            return

        # Apply node filter
        if self.node_filter and self.node_filter.lower() not in parsed['node'].lower():
            return

        # Format: [HH:MM:SS] [NODE] Message with color
        timestamp = parsed['timestamp'].split(' ')[1]  # Get time part
        node = f"[{parsed['node']}]"
        message = parsed['message']
        
        # Add colors
        if parsed['node'] == 'ImageProjection':
            node = f"\033[92m{node}\033[0m"  # Green
        elif parsed['node'] == 'FeatureAssociation':
            node = f"\033[95m{node}\033[0m"  # Magenta
        elif parsed['node'] == 'MapOptimization':
            node = f"\033[96m{node}\033[0m"  # Cyan
        elif parsed['node'] == 'TransformFusion':
            node = f"\033[93m{node}\033[0m"  # Yellow

        level = parsed['level']
        colored_level = self.colorize("", level).split(']')[0] + "]"
        
        print(f"{timestamp} {colored_level} {node} {message}")

    def view_file(self):
        """Display entire log file."""
        if not os.path.exists(self.log_file):
            print(f"❌ Log file not found: {self.log_file}")
            return False

        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    self.display_line(line.rstrip())
            
            self.last_position = os.path.getsize(self.log_file)
            return True
        except Exception as e:
            print(f"❌ Error reading log file: {e}")
            return False

    def follow_file(self):
        """Follow log file like 'tail -f'."""
        print(f"Following: {self.log_file}")
        print("Press Ctrl+C to stop\n")

        try:
            while True:
                if not os.path.exists(self.log_file):
                    print("⚠️  Log file deleted")
                    time.sleep(1)
                    continue

                file_size = os.path.getsize(self.log_file)
                
                # File was truncated or recreated
                if file_size < self.last_position:
                    self.last_position = 0

                if file_size > self.last_position:
                    with open(self.log_file, 'r') as f:
                        f.seek(self.last_position)
                        for line in f:
                            self.display_line(line.rstrip())
                        self.last_position = f.tell()

                time.sleep(0.5)  # Check for new data every 500ms

        except KeyboardInterrupt:
            print("\n\nStopped following log file")
            return True
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def run(self):
        """Run the log viewer."""
        if self.follow:
            return self.follow_file()
        else:
            return self.view_file()


class LogStats:
    """Calculate statistics from log file."""
    
    def __init__(self, log_file):
        self.log_file = log_file
        self.node_counts = defaultdict(int)
        self.level_counts = defaultdict(int)
        self.messages = []

    def parse_logs(self):
        """Parse and analyze logs."""
        if not os.path.exists(self.log_file):
            print(f"❌ Log file not found: {self.log_file}")
            return False

        import re
        pattern = r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\] \[(\w+)\] \[([^\]]+)\] (.+)'
        
        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    match = re.match(pattern, line)
                    if match:
                        timestamp, level, node, message = match.groups()
                        self.node_counts[node] += 1
                        self.level_counts[level] += 1
                        self.messages.append({
                            'timestamp': timestamp,
                            'level': level,
                            'node': node,
                            'message': message
                        })
            return True
        except Exception as e:
            print(f"❌ Error reading log file: {e}")
            return False

    def print_stats(self):
        """Print log statistics."""
        print("\n" + "="*60)
        print("LOG FILE STATISTICS")
        print("="*60)

        print(f"\nTotal messages: {len(self.messages)}")

        print("\nMessages by Node:")
        for node, count in sorted(self.node_counts.items()):
            pct = (count / len(self.messages) * 100) if self.messages else 0
            print(f"  {node:25} {count:5} ({pct:5.1f}%)")

        print("\nMessages by Level:")
        for level, count in sorted(self.level_counts.items()):
            pct = (count / len(self.messages) * 100) if self.messages else 0
            print(f"  {level:10} {count:5} ({pct:5.1f}%)")

        if self.messages:
            start = self.messages[0]['timestamp']
            end = self.messages[-1]['timestamp']
            print(f"\nTime Range:")
            print(f"  Start: {start}")
            print(f"  End:   {end}")

        print("\n" + "="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='LeGO-LOAM Log Viewer - View and analyze debug logs'
    )
    parser.add_argument('logfile', nargs='?', 
                        default='/tmp/lego_loam_logs/lego_loam_debug.log',
                        help='Log file to view (default: /tmp/lego_loam_logs/lego_loam_debug.log)')
    parser.add_argument('-f', '--follow', action='store_true',
                        help='Follow log file like tail -f')
    parser.add_argument('-n', '--node', type=str,
                        help='Filter by node name (ImageProjection, FeatureAssociation, etc.)')
    parser.add_argument('-s', '--stats', action='store_true',
                        help='Show log statistics and exit')
    parser.add_argument('-l', '--last', type=int, metavar='N',
                        help='Show last N lines')

    args = parser.parse_args()

    # Show stats if requested
    if args.stats:
        stats = LogStats(args.logfile)
        if stats.parse_logs():
            stats.print_stats()
        return 0

    # Show last N lines if requested
    if args.last:
        if not os.path.exists(args.logfile):
            print(f"❌ Log file not found: {args.logfile}")
            return 1
        
        with open(args.logfile, 'r') as f:
            lines = f.readlines()
            for line in lines[-args.last:]:
                print(line.rstrip())
        return 0

    # View log file
    viewer = LogViewer(args.logfile, follow=args.follow, node_filter=args.node)
    success = viewer.run()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
