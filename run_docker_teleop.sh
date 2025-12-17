#!/bin/bash
# /home/hospibot/run_docker_teleop.sh

echo "--- HOSPIBOT TELEOP LAUNCHER ---"
cd /home/hospibot/hospibot_docker

# 1. Start Docker
echo "Starting Docker Compose..."
/usr/bin/docker compose up -d

# 2. Run the Teleop
# IMPORTANT CHANGE: We added 'source install/setup.bash' below
echo "Entering Container..."
docker exec -it hospibot_container bash -c "source /opt/ros/humble/setup.bash && source install/setup.bash && ros2 launch hospibot_teleop teleop.launch.py"

# 3. Keep window open
echo "Teleop process ended."
exec bash
