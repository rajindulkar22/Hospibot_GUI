FROM ros:humble

# Install git, colcon, and the REQUIRED rosbridge-server
RUN apt-get update && apt-get install -y \
    git \
    python3-colcon-common-extensions \
    ros-humble-rosbridge-server \
    ros-humble-image-transport-plugins \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /root/ros2_ws/src

RUN git clone https://github.com/Chandrahas-kasoju/hospibot_teleop.git

WORKDIR /root/ros2_ws

RUN /bin/bash -c "source /opt/ros/humble/setup.bash && colcon build"

RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc
RUN echo "source /root/ros2_ws/install/setup.bash" >> /root/.bashrc

CMD ["bash"]
