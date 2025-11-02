#!/bin/bash
# Setup script for vm_diskcheck

set -e

echo "==================================="
echo "VM Disk Check - Setup Script"
echo "==================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed."
    echo "Please install Python 3.6 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✓ Python version: $PYTHON_VERSION"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is not installed."
    echo "Please install pip for Python 3."
    exit 1
fi

echo "✓ pip3 is installed"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip3 install -r requirements.txt

echo ""
echo "✓ Dependencies installed successfully"

# Create configuration file if it doesn't exist
if [ ! -f "vms.yml" ]; then
    echo ""
    echo "Creating default configuration file..."
    cp vms.yml.example vms.yml
    echo "✓ Configuration file created: vms.yml"
    echo ""
    echo "⚠️  Please edit vms.yml with your VM details before running the script."
else
    echo ""
    echo "⚠️  Configuration file vms.yml already exists. Skipping."
fi

# Make script executable
chmod +x vm_diskcheck.py

echo ""
echo "==================================="
echo "Setup completed successfully!"
echo "==================================="
echo ""
echo "Next steps:"
echo "1. Edit vms.yml with your VM details"
echo "2. Ensure SSH access to your VMs is configured"
echo "3. Run: python3 vm_diskcheck.py -c vms.yml"
echo ""
echo "For help: python3 vm_diskcheck.py --help"
echo ""
