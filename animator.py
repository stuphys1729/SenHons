import numpy as np
import time
import sys
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-14s) %(message)s',
                    )

class Animator():

    def __init__(self, plot_queue):

        self.queue = plot_queue

        data = plot_queue.get()
        x = data[0]
        y = data[1]
        qual = data[2]

        self.fig, self.ax_array = plt.subplots()

        plt.scatter(x, y, c=qual, s=200, cmap='YlGn')
        #plt.gray()
        #plt.ylim( (-5,5 )


    def update(self, i):
        #logging.debug("Trying to update plot")
        if (self.queue.empty()):
            time.sleep(0.1)
        else:
            data = self.queue.get()
            #print(data)
            if data == "STOP":
                sys.exit("Stopped Animator")
            x = data[0]
            y = data[1]
            qual = data[2]
            plt.clf()
            #plt.gray()

            plt.scatter(x, y, c=qual, s=200, cmap='YlGn')

    def animate(self):

        anim = animation.FuncAnimation(self.fig, self.update)
        figManager = plt.get_current_fig_manager()
        figManager.window.showMaximized()
        plt.show()
