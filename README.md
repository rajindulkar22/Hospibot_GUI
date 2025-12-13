# Hospibot_GUI
## Step 1: Prepare the Docker Container

## Step 2: Create the "Helper Script"
This script is responsible for the Docker logic. It runs inside the terminal window.

### 1) Create the file: <br>
```

 nano /home/hospibot/run_docker_teleop.sh 
```

### 2) Paste this code <br>
```
#!/bin/bash 
echo "--- HOSPIBOT TELEOP LAUNCHER ---"
cd /home/hospibot/hospibot_docker 
echo "Starting Docker Compose..." 
/usr/bin/docker compose up  
echo "Entering Container..."  
docker exec -it hospibot_container bash -c "source /opt/ros/humble/setup.bash && source install/setup.bash && ros2 launch hospibot_teleop teleop.launch.py" 
echo "Process ended." 
exec bash 
```

### 3) Save and exit (Ctrl+O, Enter, Ctrl+X).


## Step 3: Create the "Master Script" <br>
### 1) Create the file: <br>
```
nano /home/hospibot/start_hospibot.sh 
```

### 2) Paste this code <br>
```
#!/bin/bash 
exec > /tmp/hospibot_log.txt 2>&1 
echo "Script started..." 
echo "Launching GUI..."
/usr/bin/python3 /home/hospibot/hospibot_ws/doctortrial/hospibot.py & 
echo "Waiting 5 seconds..." 
sleep 5 
echo "Launching Terminal..." 
export DISPLAY=:0 
/usr/bin/lxterminal --geometry=80x24 -e "/home/hospibot/run_docker_teleop.sh" 
```
### 3) Save and exit (Ctrl+O, Enter, Ctrl+X).<br>

## Step 4: Make Scripts Executable <br>
Run these two commands in the terminals:<br>
```
chmod +x /home/hospibot/run_docker_teleop.sh 
chmod +x /home/hospibot/start_hospibot.sh 
```

## Step 5: Configure Autostart
### 1) Create the desktop entry file:<br>
```
nano /home/hospibot/.config/autostart/hospibot.desktop 
```
### 2) Paste this configuration: <br>
```
[Desktop Entry] 
Type=Application 
Name=Hospibot Auto Start 
Comment=Starts GUI and Docker Teleop 
Exec=/home/hospibot/start_hospibot.sh 
WorkingDirectory=/home/hospibot 
Terminal=false 
X-GNOME-Autostart-enabled=true 
```

### 3) Save and exit (Ctrl+O, Enter, Ctrl+X). <br>
## Step 6: Test It!<br>
### 1) Reboot your Raspberry Pi:<br>
```
sudo reboot 
```












