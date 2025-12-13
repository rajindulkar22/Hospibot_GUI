# Hospibot_GUI
## Step 1: Prepare the Docker Container

## Step 2: Create the "Helper Script"
This script is responsible for the Docker logic. It runs inside the terminal window.

### 1) Create the file: <br>

 nano /home/hospibot/run_docker_teleop.sh <br>

### 2) Paste this code <br>

#!/bin/bash <br>
echo "--- HOSPIBOT TELEOP LAUNCHER ---"<br>
cd /home/hospibot/hospibot_docker <br>
echo "Starting Docker Compose..." <br>
/usr/bin/docker compose up  <br>
echo "Entering Container..." <br> 
docker exec -it hospibot_container bash -c "source /opt/ros/humble/setup.bash && source install/setup.bash && ros2 launch hospibot_teleop teleop.launch.py" <br>
echo "Process ended." <br>
exec bash <br>

### 3) Save and exit (Ctrl+O, Enter, Ctrl+X).


## Step 3: Create the "Master Script" <br>
### 1) Create the file: <br>
nano /home/hospibot/start_hospibot.sh <br>

### 2) Paste this code <br>
#!/bin/bash <br>
exec > /tmp/hospibot_log.txt 2>&1 <br>
echo "Script started..." <br>
echo "Launching GUI..."
/usr/bin/python3 /home/hospibot/hospibot_ws/doctortrial/hospibot.py & <br>
echo "Waiting 5 seconds..." <br>
sleep 5 <br>
echo "Launching Terminal..." <br>
export DISPLAY=:0 <br>
/usr/bin/lxterminal --geometry=80x24 -e "/home/hospibot/run_docker_teleop.sh" <br>

### 3) Save and exit (Ctrl+O, Enter, Ctrl+X).<br>

## Step 4: Make Scripts Executable <br>
Run these two commands in the terminals:<br>
chmod +x /home/hospibot/run_docker_teleop.sh <br>
chmod +x /home/hospibot/start_hospibot.sh <br>

## Step 5: Configure Autostart
### 1) Create the desktop entry file:<br>
nano /home/hospibot/.config/autostart/hospibot.desktop <br>
### 2) Paste this configuration: <br>
[Desktop Entry] <br>
Type=Application <br>
Name=Hospibot Auto Start <br>
Comment=Starts GUI and Docker Teleop <br>
Exec=/home/hospibot/start_hospibot.sh <br>
WorkingDirectory=/home/hospibot <br>
Terminal=false <br>
X-GNOME-Autostart-enabled=true <br>

### 3) Save and exit (Ctrl+O, Enter, Ctrl+X). <br>
## Step 6: Test It!<br>
### 1) Reboot your Raspberry Pi:<br>
sudo reboot <br>













