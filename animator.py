import numpy as np
import time
import sys
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.lines import Line2D
import logging
from pprint import pprint

logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-14s) %(message)s',
                    )

class Animator():

    def __init__(self, plot_queue, callback_pipe):

        self.queue = plot_queue
        self.callback_pipe = callback_pipe
        self.fig, self.ax_array = plt.subplots()

        self.pause = False

        data = plot_queue.get()
        if len(data) == 3:
            self.init_map(data)
        elif len(data) == 4:
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
        supx = data[2]
        supq = data[3]
        Q_line = Line2D(x, qual, color="blue", label="Sellers", picker=5)
        plt.scatter(supx, supq, color='red', s=200, picker=5, label="Suppliers")

        self.max_x = max(x)
        self.ax_array.add_line(Q_line)
        self.ax_array.set_ylim(0, 1.1)
        self.ax_array.set_xlim(0, self.max_x)
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
        supx = data[2]
        supq = data[3]
        self.ax_array.cla()
        self.ax_array.set_ylim(0, 1.1)
        self.ax_array.set_xlim(0, self.max_x)

        Q_line = Line2D(x, qual, color="blue", label="Sellers", picker=2)
        plt.scatter(supx, supq, color='red', s=200, picker=5, label="Suppliers")
        self.ax_array.add_line(Q_line)

    def update(self, i):
        #logging.debug("Trying to update plot")
        if (self.queue.empty()):
            time.sleep(0.1)
        else:
            data = self.queue.get()
            #print(data)
            if data == "STOP":
                self.pause = True
            elif len(data) == 3:
                self.update_map()
            elif len(data) == 4:
                self.update_line(data)
            else:
                sys.exit("Something went wrong")

    def toggle_pause(self):
        if self.pause:
            self.pause = False
        else:
            self.pause = True
        self.callback_pipe.send("Pause")

    def animate(self):

        def onpick(event):
            if not self.pause:
                return
            actor_line = event.artist
            ind = event.ind[0] # If several points are in range, choose first
            x = event.mouseevent.xdata
            x = min(x, self.max_x/2) # 520 the rough width of text box
            y = event.mouseevent.ydata
            #logging.debug("Actor was clicked: {}".format(ind))
            #pprint(vars(actor_line))
            #logging.debug(actor_line._label)
            if actor_line._label == "Suppliers":
                self.callback_pipe.send( ["Supplier", ind] )
                supp = self.callback_pipe.recv()
                #pprint(vars(event.mouseevent))
                self.ax_array.text(x+1, y+0.01, repr(supp), size=20, bbox=dict(boxstyle="round"))
                #self.ax_array.annotate(str(supp), xy=(x,y), xytext=(x+1, y+0.01) )
            else:
                self.callback_pipe.send( ["Seller", ind] )
                sell = self.callback_pipe.recv()
                self.ax_array.text(x+1, y+0.01, repr(sell), size=20, bbox=dict(boxstyle="round"))


        def on_key(event):
            #print('you pressed', event.key, event.xdata, event.ydata)
            if event.key == " ":
                self.toggle_pause()

        self.fig.canvas.mpl_connect('key_press_event', on_key)
        self.fig.canvas.mpl_connect('pick_event', onpick)

        anim = animation.FuncAnimation(self.fig, self.update)
        figManager = plt.get_current_fig_manager()
        figManager.window.showMaximized()
        plt.show()

        self.callback_pipe.send("Pause")
