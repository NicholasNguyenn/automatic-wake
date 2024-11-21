# Dobby
## Setup
Instructions for setup on Ubuntu 20.04
1. Clone the repository
```
git clone https://github.com/Carson-Stark/Dobby.git
cd Dobby
```
2. Make a python virtual environment
```
python3 -m venv venv
source ./venv/bin/activate
python -m pip install --upgrade pip
```
3. Install pyaudio dependencies
```
sudo apt-get install python3-pyaudio
sudo apt install portaudio19-dev
```
4. Install pip requirements
```
pip3 install --upgrade pip
pip3 install -r bwi_requirements.txt
```
Use requirements_311.txt if using python 3.11. New requirements can be added using `pip3 freeze > bwi_requirements.txt`

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
