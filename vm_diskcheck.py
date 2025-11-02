#!/usr/bin/env python3
"""
VM Disk Space Check Script

This script checks disk space usage on multiple VMs via SSH connection.
It supports multiple output formats and can alert when disk usage exceeds thresholds.
"""

import argparse
import json
import subprocess
import sys
from typing import Dict, List, Optional, Tuple
import yaml


class VMDiskChecker:
    """Check disk space on virtual machines via SSH."""
    
    def __init__(self, config_file: str, threshold: int = 80):
        """
        Initialize the VM disk checker.
        
        Args:
            config_file: Path to YAML configuration file containing VM details
            threshold: Disk usage percentage threshold for warnings (default: 80%)
        """
        self.config_file = config_file
        self.threshold = threshold
        self.vms = self._load_config()
    
    def _load_config(self) -> List[Dict]:
        """Load VM configuration from YAML file."""
        try:
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)
                return config.get('vms', [])
        except FileNotFoundError:
            print(f"Error: Configuration file '{self.config_file}' not found.", file=sys.stderr)
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"Error parsing YAML configuration: {e}", file=sys.stderr)
            sys.exit(1)
    
    def check_vm_disk(self, vm: Dict) -> Optional[Dict]:
        """
        Check disk usage on a single VM.
        
        Args:
            vm: Dictionary containing VM connection details
        
        Returns:
            Dictionary with disk usage information or None on error
        """
        host = vm.get('host')
        user = vm.get('user', 'root')
        port = vm.get('port', 22)
        name = vm.get('name', host)
        ssh_key = vm.get('ssh_key', '')
        
        # Validate required parameters
        if not host:
            return {
                'name': name or 'Unknown',
                'host': 'N/A',
                'status': 'error',
                'error': 'Missing required parameter: host'
            }
        
        # Construct SSH command
        ssh_cmd = ['ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=10']
        
        if ssh_key:
            ssh_cmd.extend(['-i', ssh_key])
        
        ssh_cmd.extend(['-p', str(port), f'{user}@{host}'])
        
        # Command to get disk usage
        disk_cmd = "df -h | grep -E '^/dev/' | awk '{print $1,$2,$3,$4,$5,$6}'"
        ssh_cmd.append(disk_cmd)
        
        try:
            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return {
                    'name': name,
                    'host': host,
                    'status': 'error',
                    'error': result.stderr.strip() or 'Connection failed'
                }
            
            # Parse disk usage output
            disks = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split()
                    if len(parts) >= 6:
                        try:
                            # Parse usage percentage, handling various formats
                            usage_str = parts[4].rstrip('%')
                            usage_percent = int(usage_str)
                            
                            # Handle potential multi-line device names by taking the last 6 fields
                            if len(parts) > 6:
                                parts = parts[-6:]
                            
                            disks.append({
                                'device': parts[0],
                                'size': parts[1],
                                'used': parts[2],
                                'available': parts[3],
                                'usage_percent': usage_percent,
                                'mount': parts[5],
                                'warning': usage_percent >= self.threshold
                            })
                        except (ValueError, IndexError) as e:
                            # Skip malformed lines but log to stderr
                            print(f"Warning: Failed to parse disk line: {line}", file=sys.stderr)
                            continue
            
            return {
                'name': name,
                'host': host,
                'status': 'success',
                'disks': disks
            }
            
        except subprocess.TimeoutExpired:
            return {
                'name': name,
                'host': host,
                'status': 'error',
                'error': 'Connection timeout'
            }
        except Exception as e:
            return {
                'name': name,
                'host': host,
                'status': 'error',
                'error': str(e)
            }
    
    def check_all_vms(self) -> List[Dict]:
        """Check disk usage on all configured VMs."""
        results = []
        for vm in self.vms:
            result = self.check_vm_disk(vm)
            if result:
                results.append(result)
        return results
    
    def format_output_text(self, results: List[Dict]) -> str:
        """Format results as human-readable text."""
        output = []
        output.append("=" * 80)
        output.append("VM Disk Space Check Results")
        output.append("=" * 80)
        output.append("")
        
        for result in results:
            output.append(f"VM: {result['name']} ({result['host']})")
            output.append("-" * 80)
            
            if result['status'] == 'error':
                output.append(f"  ❌ ERROR: {result['error']}")
            else:
                for disk in result['disks']:
                    status = "⚠️  WARNING" if disk['warning'] else "✓ OK"
                    output.append(f"  {status} {disk['mount']}")
                    output.append(f"    Device: {disk['device']}")
                    output.append(f"    Size: {disk['size']}, Used: {disk['used']}, "
                                f"Available: {disk['available']}")
                    output.append(f"    Usage: {disk['usage_percent']}%")
            
            output.append("")
        
        return "\n".join(output)
    
    def format_output_json(self, results: List[Dict]) -> str:
        """Format results as JSON."""
        return json.dumps(results, indent=2)
    
    def get_summary(self, results: List[Dict]) -> Tuple[int, int, int]:
        """
        Get summary statistics.
        
        Returns:
            Tuple of (total_vms, vms_with_warnings, vms_with_errors)
        """
        total = len(results)
        errors = sum(1 for r in results if r['status'] == 'error')
        warnings = sum(
            1 for r in results 
            if r['status'] == 'success' and any(d['warning'] for d in r['disks'])
        )
        return total, warnings, errors


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Check disk space usage on multiple VMs via SSH',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -c vms.yml
  %(prog)s -c vms.yml --threshold 90
  %(prog)s -c vms.yml --format json
  %(prog)s -c vms.yml --format json > output.json
        """
    )
    
    parser.add_argument(
        '-c', '--config',
        required=True,
        help='Path to YAML configuration file containing VM details'
    )
    
    parser.add_argument(
        '-t', '--threshold',
        type=int,
        default=80,
        help='Disk usage percentage threshold for warnings (default: 80%%)'
    )
    
    parser.add_argument(
        '-f', '--format',
        choices=['text', 'json'],
        default='text',
        help='Output format (default: text)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )
    
    args = parser.parse_args()
    
    # Validate threshold
    if not 0 < args.threshold <= 100:
        print("Error: Threshold must be between 1 and 100", file=sys.stderr)
        sys.exit(1)
    
    # Create checker and run
    checker = VMDiskChecker(args.config, args.threshold)
    results = checker.check_all_vms()
    
    # Output results
    if args.format == 'json':
        print(checker.format_output_json(results))
    else:
        print(checker.format_output_text(results))
    
    # Exit with appropriate code
    total, warnings, errors = checker.get_summary(results)
    if errors > 0:
        sys.exit(2)  # Errors occurred
    elif warnings > 0:
        sys.exit(1)  # Warnings occurred
    else:
        sys.exit(0)  # All OK


if __name__ == '__main__':
    main()
