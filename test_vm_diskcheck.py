#!/usr/bin/env python3
"""
Unit tests for vm_diskcheck script
"""

import json
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock
import subprocess
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from vm_diskcheck import VMDiskChecker


class TestVMDiskChecker(unittest.TestCase):
    """Test cases for VMDiskChecker class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary config file
        self.config_content = """
vms:
  - name: "Test VM 1"
    host: "192.168.1.10"
    user: "admin"
    port: 22
  - name: "Test VM 2"
    host: "192.168.1.20"
    user: "root"
"""
        self.config_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yml')
        self.config_file.write(self.config_content)
        self.config_file.close()
    
    def tearDown(self):
        """Clean up test fixtures."""
        os.unlink(self.config_file.name)
    
    def test_load_config(self):
        """Test loading configuration from YAML file."""
        checker = VMDiskChecker(self.config_file.name)
        self.assertEqual(len(checker.vms), 2)
        self.assertEqual(checker.vms[0]['name'], "Test VM 1")
        self.assertEqual(checker.vms[1]['host'], "192.168.1.20")
    
    def test_load_config_file_not_found(self):
        """Test handling of missing config file."""
        with self.assertRaises(SystemExit):
            VMDiskChecker('/nonexistent/file.yml')
    
    def test_threshold_initialization(self):
        """Test threshold initialization."""
        checker = VMDiskChecker(self.config_file.name, threshold=90)
        self.assertEqual(checker.threshold, 90)
    
    @patch('subprocess.run')
    def test_check_vm_disk_success(self, mock_run):
        """Test successful disk check."""
        # Mock successful SSH command output
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "/dev/sda1 100G 45G 50G 47% /\n/dev/sda2 50G 42G 5G 89% /var\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        checker = VMDiskChecker(self.config_file.name, threshold=80)
        vm = checker.vms[0]
        result = checker.check_vm_disk(vm)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['name'], 'Test VM 1')
        self.assertEqual(len(result['disks']), 2)
        self.assertEqual(result['disks'][0]['usage_percent'], 47)
        self.assertFalse(result['disks'][0]['warning'])
        self.assertTrue(result['disks'][1]['warning'])
    
    @patch('subprocess.run')
    def test_check_vm_disk_connection_error(self, mock_run):
        """Test handling of connection errors."""
        # Mock failed SSH command
        mock_result = Mock()
        mock_result.returncode = 255
        mock_result.stdout = ""
        mock_result.stderr = "Connection refused"
        mock_run.return_value = mock_result
        
        checker = VMDiskChecker(self.config_file.name)
        vm = checker.vms[0]
        result = checker.check_vm_disk(vm)
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('Connection refused', result['error'])
    
    @patch('subprocess.run')
    def test_check_vm_disk_timeout(self, mock_run):
        """Test handling of SSH timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired('ssh', 30)
        
        checker = VMDiskChecker(self.config_file.name)
        vm = checker.vms[0]
        result = checker.check_vm_disk(vm)
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('timeout', result['error'].lower())
    
    @patch('subprocess.run')
    def test_check_all_vms(self, mock_run):
        """Test checking all VMs."""
        # Mock successful response
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "/dev/sda1 100G 45G 50G 47% /\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        checker = VMDiskChecker(self.config_file.name)
        results = checker.check_all_vms()
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['name'], 'Test VM 1')
        self.assertEqual(results[1]['name'], 'Test VM 2')
    
    def test_format_output_json(self):
        """Test JSON output formatting."""
        checker = VMDiskChecker(self.config_file.name)
        results = [
            {
                'name': 'Test VM',
                'host': '192.168.1.10',
                'status': 'success',
                'disks': [
                    {
                        'device': '/dev/sda1',
                        'size': '100G',
                        'used': '45G',
                        'available': '50G',
                        'usage_percent': 47,
                        'mount': '/',
                        'warning': False
                    }
                ]
            }
        ]
        
        output = checker.format_output_json(results)
        parsed = json.loads(output)
        
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]['name'], 'Test VM')
    
    def test_format_output_text(self):
        """Test text output formatting."""
        checker = VMDiskChecker(self.config_file.name)
        results = [
            {
                'name': 'Test VM',
                'host': '192.168.1.10',
                'status': 'success',
                'disks': [
                    {
                        'device': '/dev/sda1',
                        'size': '100G',
                        'used': '45G',
                        'available': '50G',
                        'usage_percent': 47,
                        'mount': '/',
                        'warning': False
                    }
                ]
            }
        ]
        
        output = checker.format_output_text(results)
        
        self.assertIn('Test VM', output)
        self.assertIn('192.168.1.10', output)
        self.assertIn('/dev/sda1', output)
        self.assertIn('47%', output)
    
    def test_get_summary(self):
        """Test summary statistics."""
        checker = VMDiskChecker(self.config_file.name)
        results = [
            {
                'name': 'VM1',
                'status': 'success',
                'disks': [{'warning': True}]
            },
            {
                'name': 'VM2',
                'status': 'success',
                'disks': [{'warning': False}]
            },
            {
                'name': 'VM3',
                'status': 'error',
                'error': 'Connection failed'
            }
        ]
        
        total, warnings, errors = checker.get_summary(results)
        
        self.assertEqual(total, 3)
        self.assertEqual(warnings, 1)
        self.assertEqual(errors, 1)


if __name__ == '__main__':
    unittest.main()
