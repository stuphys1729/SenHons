import numpy as np
import time
import sys
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.lines import Line2D
from matplotlib.patches import Ellipse
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
        if len(data) == 7:
            self.init_map(data)
        elif len(data) == 4:
            self.init_line(data)

    def init_map(self, data):
        logging.debug("Initialising Map")
        x = data[0]
        y = data[1]
        qual = data[2]
        supx = data[3]
        supy = data[4]
        supq = data[5]
        self.towns = data[6]
        patches = []

        plt.scatter(x, y, c=qual, s=200, cmap='YlGn', label="Sellers", vmin=0, vmax=1, picker=5)
        plt.scatter(supx, supy, c=supq, s=400, label="Suppliers", cmap='YlGn', marker='X', vmin=0, vmax=1, picker=5)
        if self.towns != []:
            self.max_x = max( [ t.x + 5*t.sigmax for t in self.towns] )
            self.max_y = max( [ t.y + 5*t.sigmay for t in self.towns] )
        else:
            self.max_x = max(x) + 10
            self.max_y = max(y) + 0.1
        self.ax_array.set_xlim(0, self.max_x)
        self.ax_array.set_ylim(0, self.max_y)

        for town in self.towns:
            patches.append( Ellipse( (town.x,town.y), 2*town.sigmax, 2*town.sigmay, fill=False, color='r' ) )
            patches.append( Ellipse( (town.x,town.y), 4*town.sigmax, 4*town.sigmay, fill=False, color='r' ) )
            patches.append( Ellipse( (town.x,town.y), 6*town.sigmax, 6*town.sigmay, fill=False, color='r' ) )

        for patch in patches:
            self.ax_array.add_artist(patch)
        #plt.gray()
        #plt.ylim( (-5,5 )

    def init_line(self, data):
        self.data = data
        x = data[0]
        qual = data[1]
        supx = data[2]
        supq = data[3]
        Q_line = Line2D(x, qual, color="blue", alpha=0.5)
        plt.scatter(x, qual, color="blue", s=50, picker=2, label="Sellers")
        plt.scatter(supx, supq, color='red', s=200, picker=5, label="Suppliers")

        self.max_x = max(x)
        self.ax_array.add_line(Q_line)
        self.ax_array.set_ylim(0, 1.1)
        self.ax_array.set_xlim(0, self.max_x)
        return

    def update_map(self, data):
        logging.debug("Updating Map")
        self.data = data
        x = data[0]
        y = data[1]
        qual = data[2]
        supx = data[3]
        supy = data[4]
        supq = data[5]
        plt.cla()
        self.ax_array.set_xlim(0, self.max_x)
        self.ax_array.set_ylim(0, self.max_y)
        #plt.gray()

        scatters = []
        scatters.append(plt.scatter(x, y, c=qual, s=200, cmap='YlGn', vmin=0, vmax=1, label="Sellers", picker=5) )
        scatters.append(plt.scatter(supx, supy, c=supq, s=400, label="Suppliers", picker=5, cmap='YlGn', vmin=0, vmax=1, marker='X') )

        patches = []
        for town in self.towns:
            patches.append( Ellipse( (town.x,town.y), 2*town.sigmax, 2*town.sigmay, fill=False, color='r' ) )
            patches.append( Ellipse( (town.x,town.y), 4*town.sigmax, 4*town.sigmay, fill=False, color='r' ) )
            patches.append( Ellipse( (town.x,town.y), 6*town.sigmax, 6*town.sigmay, fill=False, color='r' ) )

        for patch in patches:
            self.ax_array.add_artist(patch)

        return patches + scatters


    def update_line(self, data):
        self.data = data
        x = data[0]
        qual = data[1]
        supx = data[2]
        supq = data[3]
        self.ax_array.cla()
        self.ax_array.set_ylim(0, 1.1)
        self.ax_array.set_xlim(0, self.max_x)

        Q_line = Line2D(x, qual, color="blue", alpha=0.5)
        plt.scatter(x, qual, color="blue", s=50, picker=2, label="Sellers")
        plt.scatter(supx, supq, color='red', s=200, picker=5, label="Suppliers")
        self.ax_array.add_line(Q_line)

    def update(self, i):
        #logging.debug("Trying to update plot")
        if (self.queue.empty()):
            time.sleep(0.1)
        else:
            data = self.queue.get()
            #print(data)
            if data == "Stop":
                self.pause = True
            elif len(data) == 6:
                return self.update_map(data)
            elif len(data) == 4:
                return self.update_line(data)
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
                self.ax_array.text(x+1, y+0.01, repr(supp), size=20,
                                    bbox=dict(boxstyle="round"))
                #self.ax_array.annotate(str(supp), xy=(x,y), xytext=(x+1, y+0.01) )
            else:
                self.callback_pipe.send( ["Seller", ind] )
                sell = self.callback_pipe.recv()
                self.ax_array.text(x+1, y+0.01, repr(sell), size=20,
                            backgroundcolor='cyan', bbox=dict(boxstyle="round"))


        def on_key(event):
            #print('you pressed', event.key, event.xdata, event.ydata)
            if event.key == " ":
                self.toggle_pause()

            if event.key == "c":
                if len(self.data) == 6:
                    self.update_map(self.data)
                else:
                    self.update_line(self.data)

        def stop_sim(event):
            self.callback_pipe.send("Stop")
            logging.debug("Stopping animator")
            sys.exit()

        self.fig.canvas.mpl_connect('key_press_event', on_key)
        self.fig.canvas.mpl_connect('pick_event', onpick)
        self.fig.canvas.mpl_connect('close_event', stop_sim)

        anim = animation.FuncAnimation(self.fig, self.update)
        figManager = plt.get_current_fig_manager()
        figManager.window.showMaximized()
        plt.show()

        #self.callback_pipe.send("Pause")
