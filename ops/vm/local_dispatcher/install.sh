#!/bin/bash

# Setup script to deploy LOCAL-DISPATCHER-1 on the VM

set -e

if [ "$USER" != "ubuntu" ]; then
    echo "This script must only run on the VM (as user ubuntu)."
    exit 1
fi

# Create directories
mkdir -p /home/ubuntu/local_dispatcher
mkdir -p ~/.config/systemd/user

# Copy files
cp dispatcher.py /home/ubuntu/local_dispatcher/
cp LOCAL_FORMAT.md /home/ubuntu/local_dispatcher/
cp ga-local.service ~/.config/systemd/user/

# Enable lingering
loginctl enable-linger ubuntu

# Reload systemd and start service
systemctl --user daemon-reload
systemctl --user enable --now ga-local.service

# Retire the mock scripts (move to archive)
mkdir -p /home/ubuntu/archive_mock
for script in /home/ubuntu/poll_mailbox_daemon.py /home/ubuntu/send_loc*.py /home/ubuntu/scratch_report.py /home/ubuntu/send_report.py; do
    if [ -f "$script" ]; then
        mv "$script" /home/ubuntu/archive_mock/
    fi
done

echo "LOCAL-DISPATCHER-1 installed and started!"
echo "Check status with: systemctl --user status ga-local"
echo "View logs with: cat ~/ga-local.log"
