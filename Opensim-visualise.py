from threading import Thread
import time,sys

#Opensim
import opensim as osim
from math import pi

#SSH
import paramiko
import os

#sEMG
import matplotlib.pyplot as plt
import matplotlib.animation as animation


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
        for file in to_collect:
            sftp.get(ubuntu_dir+file, os.getcwd() + "\\" + file) #maintain the same naming
        sftp.close()
        break

#recieve files
startTime = 0.0
f = open(to_collect[0],"r")
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
imuIK.set_time_range(0, startTime)
imuIK.set_time_range(1, endTime)

def OpenSimVisual():
    # Run IK
    imuIK.run(visualizeTracking)

def visualiseSEMG():
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    xs = []
    ys = []

    f = open(to_collect[3],"r")
    lines = f.readlines()

    sEMG_reading = []
    time_stamp = []

    for line in lines:
        sEMG,t = map(float,line.split("\t"))
        sEMG_reading.append(sEMG)
        time_stamp.append(t)

    time_interval = time_stamp[1]-time_stamp[0]

    def animate(i, xs, ys):
        # Add x and y to lists
        xs.append(sEMG_reading[i])
        ys.append(time_stamp[i])

        # Limit x and y lists to 20 items
        xs = xs[-20:]
        ys = ys[-20:]

        # Draw x and y lists
        ax.clear()
        ax.plot(xs, ys)

        # Format plot
        plt.xticks(rotation=45, ha='right')
        plt.subplots_adjust(bottom=0.30)


    # Set up plot to call animate() function periodically
    ani = animation.FuncAnimation(fig, animate, fargs=(xs, ys), interval=time_interval)
    plt.show()

Thread(target = OpenSimVisual).start() 
Thread(target = visualiseSEMG).start()