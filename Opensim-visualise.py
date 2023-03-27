import opensim as osim
from math import pi
import paramiko
import os
import time

ubuntu_dir = "/home/ubuntu/UpperBodyPOC/"

to_collect = [
    "motion_info.txt", #This is the one to check if data has been collected or not!
    "calibrated_Rajagopal_2015.osim",
    "tiny_file.sto",
    "sEMG_data.txt"
    ]

target_file = ubuntu_dir + to_collect[0]

ssh_client = paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh_client.connect("192.168.1.111", port = 22, username = "ubuntu",password="rosaparks")

sftp=ssh_client.open_sftp()
file_exists = False

while True:
    try:
        sftp.chdir(ubuntu_dir)
        sftp.stat(target_file) #check and see if target file exists
        file_exists = True
    except:
        time.sleep(1)
        #print(".",end = " ") #this doesnt work that well
    
    if file_exists:
        for file in Collect_files:
            sftp.get(ubuntu_dir+Collect_file)

        sftp.get(model_file,os.getcwd()+"\\calibrated_Rajagopal_2015.osim")
        sftp.get(sto_file,os.getcwd()+"\\tiny_file.sto")
        sftp.get(target_file,os.getcwd()+"\\motion_info.txt")
        sftp.get(sEMG_file,os.getcwd()+"\\sEMG_data.txt")
        sftp.close()
        break

#recieve files
startTime = 0.0
f = open("motion_info.txt","r")
errorHeading = float(f.readline())
endTime = float(f.readline())
f.close()


modelFileName = 'calibrated_Rajagopal_2015.osim'                # The path to an input model
orientationsFileName = 'tiny_file.sto'   # The path to orientation data for calibration 
sensor_to_opensim_rotation = osim.Vec3(-pi/2, errorHeading, 0) # The rotation of IMU data to the OpenSim world frame
visualizeTracking = True;  # Boolean to Visualize the tracking simulation
resultsDirectory = 'IKResults'

# Instantiate an InverseKinematicsTool
imuIK = osim.IMUInverseKinematicsTool()
 
# Set tool properties
imuIK.set_model_file(modelFileName)
imuIK.set_orientations_file(orientationsFileName)
imuIK.set_sensor_to_opensim_rotations(sensor_to_opensim_rotation)
imuIK.set_results_directory(resultsDirectory)

# Set time range in seconds
imuIK.set_time_range(0, startTime); 
imuIK.set_time_range(1, endTime);   

# Run IK
imuIK.run(visualizeTracking)