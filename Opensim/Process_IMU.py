#solving
import numpy as np
from ahrs.filters import Mahony

def filterIMU(imu_data, sto_filename):
    rows = imu_data.shape[0]
    Q = np.tile([1., 0., 0., 0.], (rows, 6))
    Q[0],IMU_rate = get_t0_IMUrate(sto_filename)

    print("Mahony Filter with IMU frequency rate of",IMU_rate,"selected")
    print(Q[0])
    print("..................................")

    mahony = Mahony(frequency = IMU_rate)
    
    for row in range(1,rows):
        for sn in range(6):
            imu_readings = imu_data[row,sn*6:sn*6 + 6] #use row - 1 to take the first raw imu reading
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
    IMU_rate = int(lines[0].split("=")[1])

    t0_data = lines[6].split("\t") #take the t = 0 timestamp
    t0_quats = []
    for item in t0_data[1:]: #ignore timestamp
        t0_quats = t0_quats + list(map(float,item.split(",")))
    
    return t0_quats,IMU_rate

def quat_to_sto(Q,sto_filename,new_sto_filename):
    #Copy format of the tiny_file.sto
    f = open(sto_filename,"r")
    lines = f.readlines()

    new_file = open(new_sto_filename,"w")
    for i in range(7):
        new_file.write(lines[i]) #include the first time stamp

    print("timestamp = 0")
    print(lines[6])

    data_rate = float(lines[0].split("=")[-1])
    dt = 1/data_rate

    print("dt used:",dt)

    for i in range(1,Q.shape[0]): #do not write the first quat, part of calibration
        time_stamp = (i)*dt
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

def rotate_imus(rot_mat_filename,imu_data):
    rot_mats = np.load(rot_mat_filename)

    for i in range(6):
        s_off = i*6
        accel = np.matmul(imu_data[:,s_off:s_off+3],rot_mats[i,:,:])
        gyro = np.matmul(imu_data[:,s_off+3:s_off+6],rot_mats[i,:,:])

        imu_data[:,s_off:s_off+3] = accel
        imu_data[:,s_off+3:s_off+6] = gyro

    return imu_data


def generate_Quat_File(raw_imu_filename,t0_sto_file, targetQuatFile):
    #as long as the position of the sensors are the same, the rot mat should not change
    rot_mat_filename = r"C:\Users\chris\Documents\Visualisation\Opensim\rot_mats.npy"

    imu_data = np.load(raw_imu_filename)
    imu_data = rotate_imus(rot_mat_filename,imu_data)
    Q = filterIMU(imu_data,t0_sto_file)
    quat_to_sto(Q,t0_sto_file,targetQuatFile)   