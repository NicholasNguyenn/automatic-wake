# Dobby Tour Guide

Software for running LLM-driven tours with the Dobby system.

## Setup
Instructions for setup on Ubuntu 20.04
1. Clone the repository
```
git clone https://github.com/Living-With-Robots-Lab/DobbyTourGuide.git
cd DobbyTourGuide
```
2. Make a python virtual environment
```
python3 -m venv venv
source ./venv/bin/activate
```
3. Install pyaudio dependencies
```
sudo apt-get install python3-pyaudio
sudo apt install portaudio19-dev
```
4. Install pip requirements
```
pip3 install --upgrade pip
pip3 install -r requirements.txt
```

## Customization

Edit src/data.py to set the tour, prompt, and landmark files. You can also enable linear tours to force the robot to go to destinations in a certain order. New landmarks can be added using log_location.py. The information for each landmark should be added to the correct Data/knowledge yaml file. If using linear tours, set the tour sequence by adding the name of the desired destinations to the tour txt file.

## Running the Program

1. Start the docker
```
cd bwi-docker
bwi-start
bwi-shell
source catkin_ws/devel/setup.bash
source ../base_env/v4_env
```
3. Launch ros
```
roslaunch bwi_launch segbot_v4_ahg.launch
```
5. Open a new terminal in the docker and start the web republisher
```
sudo apt-get install ros-melodic-tf2-web-republisher
rosrun tf2_web_republisher tf2_web_republisher
```
7. Open a new terminal in the docker and start the robofleet client (for elevator calling)
```
cd robofleet_client
ROS_NAMESPACE="Dobby" make run
```
9. Activate the virtual environment and run driver.py

## Common Issues

Sidenote: If you run into any issues, feel free to document them here for future reference.

### ModuleNotFoundError: No module named '_tkinter'
tkinter requires the installation of python-tk. If it is not already installed on your Linux machine, run the following:
`sudo apt-get install python3-tk`
