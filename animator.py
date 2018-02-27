import numpy as np
import time
import sys
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.lines import Line2D
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-14s) %(message)s',
                    )

class Animator():

    def __init__(self, plot_queue):

        self.queue = plot_queue

        self.fig, self.ax_array = plt.subplots()

        data = plot_queue.get()
        if len(data) == 3:
            self.init_map(data)
        elif len(data) == 2:
            self.init_line(data)

    def init_map(self, data):
        x = data[0]
        y = data[1]
        qual = data[2]

        plt.scatter(x, y, c=qual, s=200, cmap='YlGn')
        #plt.gray()
        #plt.ylim( (-5,5 )

    def init_line(self, data):
        x = data[0]
        qual = data[1]
        self.Q_line = Line2D(x, qual, color="blue", label="Medicine Quality")
        self.ax_array.add_line(self.Q_line)
        self.ax_array.set_xlim(0, max(x))
        return

    def update_map(self, data):
        x = data[0]
        y = data[1]
        qual = data[2]
        plt.clf()
        #plt.gray()

        plt.scatter(x, y, c=qual, s=200, cmap='YlGn')

    def update_line(self, data):
        x = data[0]
        qual = data[1]
        self.Q_line.set_data(x, qual)

    def update(self, i):
        #logging.debug("Trying to update plot")
        if (self.queue.empty()):
            time.sleep(0.1)
        else:
            data = self.queue.get()
            #print(data)
            if data == "STOP":
                sys.exit("Stopped Animator")
            elif len(data) == 3:
                self.update_map()
            elif len(data) == 2:
                self.update_line(data)
            else:
                sys.exit("Something went wrong")


    def animate(self):

        anim = animation.FuncAnimation(self.fig, self.update)
        figManager = plt.get_current_fig_manager()
        figManager.window.showMaximized()
        plt.show()
