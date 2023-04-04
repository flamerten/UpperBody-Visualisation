#solving
import numpy as np
from ahrs.filters import Mahony

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

def Qto_sto(Q,sto_filename,new_sto_filename):
    #Copy format of the tiny_file.sto
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

def Generate_Quat_File(raw_imu_filename,t0_sto_file, targetQuatFile):
    imu_data = np.load(raw_imu_filename)
    Q = filterIMU(imu_data,t0_sto_file)
    Qto_sto(Q,t0_sto_file,targetQuatFile)   