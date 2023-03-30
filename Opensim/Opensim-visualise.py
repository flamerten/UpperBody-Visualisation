
import time,sys
from datetime import datetime

#Opensim
import opensim as osim
from math import pi

#SSH
import paramiko
import os

use_sEMG = False

ubuntu_dir = "/home/ubuntu/UpperBodyPOC/"
to_collect = [
    "motion_info.txt", #This is the one to check if data has been collected or not!
    "tiny_file.sto",
    "sEMG_data.txt"
    ]


orientationsFileName = 'tiny_file.sto'   # The path to orientation data for calibration 
visualizeTracking = True  # Boolean to Visualize the tracking simulation
OriginalmodelFileName = "Locked_Rajagopal_2015.osim"
Internal_modelFileName = 'Calibrated_' + OriginalmodelFileName

RPI_IP_Address = "192.168.1.111"
RPI_Username = "ubuntu"
RPI_Password = "rosaparks"

def get_IK_params(collection):
    f = open(collection[0],"r")
    startTime = 0.0
    errorHeading = float(f.readline())
    endTime = float(f.readline())
    f.close()
    return startTime, endTime, errorHeading

def setDirectory():
    today = datetime.now()
    dir = today.strftime("%d%m%y-%H%M")
    return dir

def moveFile(filename,NewDir):
    currentDir = os.getcwd() + "\\" + filename
    tagetDir = os.getcwd() + "\\" + NewDir + "\\" + filename

    os.replace(currentDir,tagetDir)
    print(tagetDir)


ssh_client = paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh_client.connect(RPI_IP_Address, port = 22, username = RPI_Username,password=RPI_Password)

sftp=ssh_client.open_sftp()
file_exists = False
target_file = ubuntu_dir + to_collect[0] #check to see if file exists before collecting all the data
if use_sEMG == False:
    to_collect = to_collect[:-1] #dont transfer semg data if not in use

while True:
    try:
        sftp.chdir(ubuntu_dir)
        sftp.stat(target_file) #check and see if target file exists
        file_exists = True
    except:
        time.sleep(1)
        #print(".",end = " ") #this doesnt work that well
    
    if file_exists:
        print("\nFiles Recieved:")
        for file in to_collect:
            sftp.get(ubuntu_dir+file, os.getcwd() + "\\" + file) #maintain the same naming
            print(os.getcwd() + "\\" + file)     
        print("")
        sftp.close()
        break


startTime, endTime, errorHeading = get_IK_params(to_collect)
sensor_to_opensim_rotation = osim.Vec3(-pi/2, errorHeading, 0) # The rotation of IMU data to the OpenSim world frame
resultsDirectory = "Results\\"+setDirectory()

#Calibrate_model
imuPlacer = osim.IMUPlacer()
imuPlacer.set_model_file(OriginalmodelFileName)
imuPlacer.set_orientation_file_for_calibration(orientationsFileName)
imuPlacer.set_sensor_to_opensim_rotations(sensor_to_opensim_rotation)
imuPlacer.run(False); #dont visualise placer

model = imuPlacer.getCalibratedModel()
model.printToXML(Internal_modelFileName) #Create the calibrated model based on t0 time stamp

# Instantiate an InverseKinematicsTool
imuIK = osim.IMUInverseKinematicsTool()
imuIK.set_model_file(Internal_modelFileName)
imuIK.set_orientations_file(orientationsFileName)
imuIK.set_sensor_to_opensim_rotations(sensor_to_opensim_rotation)
imuIK.set_results_directory(resultsDirectory)

# Set time range in seconds
imuIK.set_time_range(0, startTime)
imuIK.set_time_range(1, endTime)

imuIK.run(visualizeTracking)

Files_To_Move = to_collect + [Internal_modelFileName]
print("\nFiles moved to " + resultsDirectory)
for file in Files_To_Move:
    moveFile(file,resultsDirectory)

