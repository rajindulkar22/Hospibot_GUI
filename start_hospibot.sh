#!/bin/bash
# /home/hospibot/start_hospibot.sh

# Log output for debugging
exec > /tmp/hospibot_log.txt 2>&1
echo "Script started at $(date)"

# --- PART 1: Start GUI ---
echo "Launching GUI..."
/usr/bin/python3 /home/hospibot/hospibot_ws/doctortrial/hospibot.py &

# --- PART 2: Wait for Desktop ---
echo "Waiting for desktop..."
sleep 5

# --- PART 3: Launch LXTerminal for Teleop ---
echo "Launching LXTerminal..."
# This command tells lxterminal to open a window and execute our helper script
export DISPLAY=:0
/usr/bin/lxterminal --geometry=80x24 -e "/home/hospibot/run_docker_teleop.sh"

echo "Script finished."
