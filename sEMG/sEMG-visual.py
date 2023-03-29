#sEMG
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import os
import time

fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)
xs = []
ys = []

f = open("sEMG_data.txt","r")
lines = f.readlines()

sEMG_readings = []
time_stamp = []

for line in lines:
    t,sEMG = map(float,line.split("\t"))
    sEMG_readings.append(sEMG)
    time_stamp.append(t)

time_interval = time_stamp[1]-time_stamp[0]

print(time_interval)
print(sEMG_readings)

def animate(i, xs, ys):
    # Add x and y to lists
    try:
        xs.append(time_stamp[i])
        ys.append(sEMG_readings[i])
    except:
        return #the graph will stay there

    # Limit x and y lists to 20 items
    xs = xs[-20:]
    ys = ys[-20:]

    # Draw x and y lists
    ax.clear()
    ax.plot(xs, ys)

    # Format plot
    plt.xticks(rotation=45, ha='right')
    plt.subplots_adjust(bottom=0.30)

while(os.path.exists("plot_now.txt") == False):
    time.sleep(1)

# Set up plot to call animate() function periodically
ani = animation.FuncAnimation(fig, animate, fargs=(xs, ys), interval=time_interval)
plt.show()