import sys
from pip._internal import main as pip_main

def install(package):
    try:
        result = pip_main(['install', package.strip()])
        return result == 0  # Return True if installation was successful
    except Exception as e:
        print(f"Failed to install {package.strip()}: {e}")
        return False

if __name__ == '__main__':
    successful_packages = []
    with open("requirements.txt", "r") as f:
        for line in f:
            package = line.strip()
            if package and install(package):
                successful_packages.append(package)

    # Write successfully installed packages to a new file
    with open("successful_requirements.txt", "w") as success_file:
        for package in successful_packages:
            success_file.write(f"{package}\n")

    print("Successfully installed packages have been saved to 'successful_requirements.txt'.")
