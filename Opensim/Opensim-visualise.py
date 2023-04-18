import Process_IMU as P
import time,sys
from datetime import datetime

#Opensim
import opensim as osim
from math import pi

#SSH
import paramiko
import os

use_sEMG = True
collect_Files = True #option to rerun on data that has been collected

Ubuntu_dir = "/home/ubuntu/UpperBodyPOC/"

Target_FileName = "motion_info.txt"
Rpi_quat_FileName = 'tiny_file.sto' #from rpi
#file will be fully filled if online, will use this to compare to the 
#com generated one

Rpi_t0quat_FileName = "timestamp_0.sto" #only has t0 inside
Generated_quat_FileName = 'generated_quat_file.sto' #to generate using com computer 
Original_model_FileName = "Locked_Rajagopal_2015.osim"
Calibrated_model_FileName = 'Calibrated_' + Original_model_FileName
Raw_IMU_FileName = "raw_imu.npy"
Semg_FileName = "semg_data.npy"

to_collect = [
    Target_FileName,
    Rpi_quat_FileName, #merely for checking
    Rpi_t0quat_FileName,
    Raw_IMU_FileName,
    Semg_FileName
]

RPI_IP_Address = "192.168.1.111"
RPI_Username = "ubuntu"
RPI_Password = "rosaparks"

visualize = True  # Boolean to Visualize the tracking simulation

def get_IK_params(Target_FileName):
    f = open(Target_FileName,"r")
    startTime = 0.0
    errorHeading = float(f.readline())
    endTime = float(f.readline())
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

if collect_Files:
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(RPI_IP_Address, port = 22, username = RPI_Username,password=RPI_Password)

    sftp=ssh_client.open_sftp()
    file_exists = False
    target_file = Ubuntu_dir + Target_FileName #check to see if file exists before collecting all the data

    if use_sEMG == False:
        to_collect.remove(Semg_FileName)

    while True:
        try:
            sftp.chdir(Ubuntu_dir)
            sftp.stat(target_file) #check and see if target file exists
            file_exists = True
        except:
            time.sleep(0.5)
            #print(".",end = " ") #this doesnt work that well
        
        if file_exists:
            print("\nFiles Recieved:")
            for file in to_collect:
                sftp.get(Ubuntu_dir+file, os.getcwd() + "\\" + file) #maintain the same naming
                print(os.getcwd() + "\\" + file)     
            print("")
            sftp.close()
            break

P.generate_Quat_File(Raw_IMU_FileName,Rpi_t0quat_FileName,Generated_quat_FileName)

startTime, endTime, errorHeading = get_IK_params(Target_FileName)
sensor_to_opensim_rotation = osim.Vec3(-pi/2, errorHeading, 0) # The rotation of IMU data to the OpenSim world frame
resultsDirectory = "Results\\"+setDirectory()


#ONE OF THEM
#quat_file = Rpi_quat_FileName #RPI filtering
quat_file = Generated_quat_FileName #Com filtering

#Calibrate_model
imuPlacer = osim.IMUPlacer()
imuPlacer.set_model_file(Original_model_FileName)
imuPlacer.set_orientation_file_for_calibration(quat_file)
imuPlacer.set_sensor_to_opensim_rotations(sensor_to_opensim_rotation)
imuPlacer.run(False); #dont visualise placer

model = imuPlacer.getCalibratedModel()
model.printToXML(Calibrated_model_FileName) #Create the calibrated model based on t0 time stamp

# Instantiate an InverseKinematicsTool
imuIK = osim.IMUInverseKinematicsTool()
imuIK.set_model_file(Calibrated_model_FileName)
imuIK.set_orientations_file(quat_file)
imuIK.set_sensor_to_opensim_rotations(sensor_to_opensim_rotation)
imuIK.set_results_directory(resultsDirectory) #the IK file is already saved in the results dir, no need to move it

# Set time range in seconds
imuIK.set_time_range(0, startTime)
imuIK.set_time_range(1, endTime)

imuIK.run(visualize)

#Move all files that were used to the results dir, and also the IK solved file
Files_To_Move = to_collect + [Calibrated_model_FileName] #move calibrated model
print("\nFiles moved to " + resultsDirectory)
for file in Files_To_Move:
    try:
        moveFile(file,resultsDirectory)
    except:
        print("Unable to move File",file)
moveFile(Generated_quat_FileName,resultsDirectory)

