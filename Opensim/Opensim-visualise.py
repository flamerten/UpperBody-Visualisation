
import time,sys
from datetime import datetime

#Opensim
import opensim as osim
from math import pi

#SSH
import paramiko
import os

#solving
import numpy as np
from ahrs.filters import Mahony

use_sEMG = False

ubuntu_dir = "/home/ubuntu/UpperBodyPOC/"
to_collect = [
    "motion_info.txt", #This is the one to check if data has been collected or not!
    "tiny_file.sto",
    "raw_imu.npy",
    "sEMG_data.txt"
    ]


orientationsFileName = 'tiny_file.sto'   # The path to orientation data for calibration 
neworientations = 'new_tiny_file.sto'
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
    #endTime = float(f.readline())
    endTime = UpdateEndTime(neworientations)
    f.close()
    return startTime, endTime, errorHeading

def setDirectory():
    today = datetime.now()
    #dir = today.strftime("%d%m%y-%H%M")
    dir = today.strftime("%y-%m-%d_%H%M")
    return dir

def moveFile(filename,NewDir):
    currentDir = os.getcwd() + "\\" + filename
    tagetDir = os.getcwd() + "\\" + NewDir + "\\" + filename

    os.replace(currentDir,tagetDir)
    print(tagetDir)

def filterIMU(imu_data, sto_filename):
    rows = imu_data.shape[0]
    Q = np.tile([1., 0., 0., 0.], (rows, 6))
    Q[0],IMU_rate = get_t0_IMUrate(sto_filename)

    mahony = Mahony(frequency = IMU_rate)
    
    for row in range(1,rows):
        for sn in range(6):
            imu_readings = imu_data[row,sn*6:sn*6 + 6]
            accel_imu = imu_readings[:3]
            gyro_imu = imu_readings[3:]

            Q[row,4*(sn):4*(sn+1)] = mahony.updateIMU(
                Q[row-1,4*(sn):4*(sn+1)],
                gyr=gyro_imu,
                acc=accel_imu)

    return Q

def get_t0_IMUrate(sto_filename):
    f = open(sto_filename,"r")
    lines = f.readlines()
    quat_t0 = lines[6].split("\t") #take the t = 0 timestamp

    IMU_rate = int(lines[0].split("=")[1])
    
    res = []
    for item in quat_t0[1:]: #dont consider the t0 timestamp
        res = res + list(map(float,item.split(",")))
    
    return res,IMU_rate

def create_sto(Q,sto_filename,new_sto_filename):
    f = open(sto_filename,"r")
    lines = f.readlines()

    new_file = open(new_sto_filename,"w")
    for i in range(6):
        new_file.write(lines[i])

    data_rate = float(lines[0].split("=")[-1])
    dt = 1/data_rate

    for i in range(Q.shape[0]):
        time_stamp = i*dt
        new_file.write("{}".format(round(time_stamp,2)))

        for sensor in range(6):
            start_index = sensor * 4
            new_file.write("\t{},{},{},{}".format(
                Q[i,start_index],
                Q[i,start_index+1],
                Q[i,start_index+2],
                Q[i,start_index+3]))
        new_file.write("\n")
    
    new_file.close()

def UpdateEndTime(new_sto_filename):
    f = open(new_sto_filename,"r")
    lines = f.readlines()
    end_time = lines[-1].split("\t")[0]
    return float(end_time)


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

imu_data = np.load("raw_imu.npy")
Q = filterIMU(imu_data,orientationsFileName)
create_sto(Q,orientationsFileName,neworientations)

startTime, endTime, errorHeading = get_IK_params(to_collect)

sensor_to_opensim_rotation = osim.Vec3(-pi/2, errorHeading, 0) # The rotation of IMU data to the OpenSim world frame
resultsDirectory = "Results\\"+setDirectory()

#Calibrate_model
imuPlacer = osim.IMUPlacer()
imuPlacer.set_model_file(OriginalmodelFileName)
imuPlacer.set_orientation_file_for_calibration(neworientations)
imuPlacer.set_sensor_to_opensim_rotations(sensor_to_opensim_rotation)
imuPlacer.run(False); #dont visualise placer

model = imuPlacer.getCalibratedModel()
model.printToXML(Internal_modelFileName) #Create the calibrated model based on t0 time stamp

# Instantiate an InverseKinematicsTool
imuIK = osim.IMUInverseKinematicsTool()
imuIK.set_model_file(Internal_modelFileName)
imuIK.set_orientations_file(neworientations)
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

moveFile(neworientations,resultsDirectory)

