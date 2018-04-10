"""
This file runs a simulation of the evolution of trust in medicine.

The model consists of Patients, who go to Sellers to purchase medicine of an
unknown quality, and either get better or they do not (depending on medicine
quality and the placebo effect) and update their trust in that seller
accordingly. The Sellers themselves purchase their medicine from Suppliers, and
also develop trust in the same way.
"""
from random import random as rand, shuffle, uniform
import numpy as np
import matplotlib.pyplot as plt
from multiprocessing import Process, Queue, Pipe
from logging import basicConfig, debug, DEBUG
import time
import copy
from optparse import OptionParser

from actors import *
from animator import Animator

basicConfig(level=DEBUG,
            format='(%(threadName)-10s) %(message)s',
            )


class Simulation():
    """
    This is the class to hold the simulation parameters
    """

    def __init__(self, ni=1000, nj=100, nk=10, env_file=None, dynam_price=False, dynam_actors=False):

        self.ni = ni    # Initial number of patients
        self.nj = nj    # Initial number of sellers
        self.nk = nk    # Initial number of wholesalers
        self.dynamic_price = dynam_price # Whether or not sellers/suppliers can change their price
        self.dynamic_actors = dynam_actors # Whether we can create and destroy actors
        self.watcher = Watcher() # For keeping track of mean quality and such

        if env_file:
            self.environment = Environment(env_file)
            self.system_size = self.environment.system_size
        else:
            self.system_size = ni # 1D

        self.suppliers = [Supplier(k, self.system_size, self.watcher) for k in range(nk)]
        self.last_supp = nk # Used to create unique ids for new suppleirs

        #ratio = np.floor(self.ni/self.nj)
        self.sellers = [Seller(j, self.system_size, self.watcher, self.dynamic_price) for j in range(nj)]
        self.last_sell = nj

        self.patients = [Patient(i, self.system_size, self.watcher, self.dynamic_price) for i in range(ni)]
        self.last_pat = ni

        if env_file:
            self.set_positions(self.environment)
        else:
            self.environment = None
            self.set_positions()

        if self.sellers[0].cash > 0:    # We have chosen to give sellers some
            for seller in self.sellers: # initial cash to buy medicine
                seller.choose_best(self.suppliers)


    def __str__(self):
        suppliers   = "\n".join([str(s) for s in self.suppliers])
        sellers     = "\n".join([str(s) for s in self.sellers])
        patients    = "\n".join([str(p) for p in self.patients])
        sep         = "\n" + ("-" * 90) + "\n"

        return suppliers + sep + sellers + sep + patients


    def set_positions(self, environment=None):

        if environment == None:
            # If there is no environemt, we just space the actors out along a line
            ratio = 1.0
            pos = 0.0
            for patient in self.patients:
                patient.position = (pos+rand(), rand())
                pos += ratio
            debug("System size: " + str(self.system_size))
            debug("Pos of last patient: {}".format(pos-ratio))

            ratio = np.floor(self.ni/self.nj)
            debug("Ratio of Patients to Sellers: {}".format(ratio))
            pos = 0.0
            for seller in self.sellers:
                seller.position = (pos+rand(), rand())
                pos += ratio
            debug("Pos of last Seller: {}".format(pos-ratio))

            ratio = np.floor(self.ni/self.nk)
            debug("Ratio of Patients to Suppliers: {}".format(ratio))
            pos = 0.0
            for supplier in self.suppliers:
                supplier.position = (pos+rand(), rand())
                pos += ratio
            debug("Pos of last Supplier: {}\n".format(pos-ratio))

        else: # We have a set of towns to get our positions from
            debug("System size: " + str(self.system_size))

            for patient in self.patients:
                patient.position = environment.get_position()

            for seller in self.sellers:
                seller.position = environment.get_position()

            for supplier in self.suppliers:
                supplier.position = environment.get_position()


        for patient in self.patients:
            patient.make_dist_array(self.sellers)

        for seller in self.sellers:
            #debug("seller id: {}".format(seller.uid))
            seller.make_dist_array(self.suppliers)

        #for supplier in self.suppliers:
            #debug("Supplier id: {}".format(supplier.uid))

    def initialise_dist_arrays(self):

        seller_pos = [self.sellers[i].position for i in range(self.nj)]
        supplier_pos = [self.suppliers[i].position for i in range(self.nk)]

        for patient in self.patients:
            patient.update_distances(seller_pos)

        for seller in self.sellers:
            seller.update_distances(supplier_pos)



    def time_step_sweep(self):
        """ Method to have every patient purchase medicine """
        for patient in self.patients:
            # Each patient chooses their current best seller
            patient.choose_best(self.sellers)
            # This also handles the sale and healing of the medicine

        for seller in self.sellers:
            # Each seller chooses their current best supplier
            seller.choose_best(self.suppliers)
            # This also handles the sale and quality test

        for supplier in self.suppliers:
            # Supplier makes 'stuff' based on current strategy
            supplier.make_meds()

        return

    def make_new(self, old_actor):
        if self.environment:
            position = self.environment.get_position()
        else:
            x = uniform(0, self.system_size)
            y = rand()
            position = (x,y)

        if type(old_actor) is Seller:
            new_seller = old_actor.make_new(self.last_sell, position)
            new_seller.make_dist_array(self.suppliers)
            self.sellers.append(new_seller)
            self.last_sell += 1 # Set the id for the next seller
            debug(str(old_actor))
            debug("Making new seller: " + str(new_seller))
            for patient in self.patients:
                patient.make_vendor_link(old_actor.uid, new_seller.uid)

        else:
            new_supplier = old_actor.make_new(self.last_supp, position)
            self.suppliers.append(new_supplier)
            self.last_supp += 1
            debug(str(old_actor))
            debug("Making new supplier: " + str(new_supplier))
            for seller in self.sellers:
                seller.make_vendor_link(old_actor.uid, new_supplier.uid)

    def time_step_sto(self, n_samples=None):
        """ Method to randomly choose n patients to purchase medicine """
        if not n_samples:
            n = int(len(self.patients) / 5) # Defaults to 20% of the patients
        else:
            n = n_samples

        samples = list(range(len(self.patients)))
        shuffle(samples)
        for i in range(n):
            self.patients[samples[i]].choose_best(self.sellers)

        to_remove = []
        indices = list(range(len(self.sellers)))
        shuffle(indices)
        for i in indices:
            seller = self.sellers[i]
            # Each seller chooses their current best supplier
            function = seller.choose_best(self.suppliers)
            # This also handles the sale and quality test

            # If we are altering vendor numbers and this seller wants to do so
            if function and self.dynamic_actors:
                if function == "New": # Set up new premices
                    self.make_new(seller)

                if function == "End": # This seller has gone bust
                    to_remove.append(i) # Remove it after iterating through the rest
                    debug(str(seller) + " has gone bust")

        for i in sorted(to_remove, reverse=True):
            del self.sellers[i]

        to_remove = []
        for i in range(len(self.suppliers)):
            supplier = self.suppliers[i]
            # Supplier makes 'stuff' based on current strategy
            function = supplier.make_meds()

            # If we are altering vendor numbers and this supplier wants to do so
            if function and self.dynamic_actors:
                if function == "New":
                    self.make_new(supplier)

                if function == "End": # This seller has gone bust
                    to_remove.append(i) # Remove it after iterating through the rest
                    debug(str(supplier) + " has gone bust")

        for i in sorted(to_remove, reverse=True):
            del self.suppliers[i]


def wait_for_input(sim, connection):
    pause = True
    debug("Animation Paused")
    while pause:
        while not connection.poll():
            time.sleep(0.05)
        request = connection.recv()

        if request == "Pause":
            pause = False
        elif request == "Stop":
            global stop
            stop = True
            break;
        else:
            actor, ind = request
            if actor == "Supplier":
                connection.send(sim.suppliers[ind])
            else:
                connection.send(sim.sellers[ind])

def run_sim(num_trials, sim):

    global stop

    x       = [seller.position[0] for seller in sim.sellers]
    y       = [seller.position[1] for seller in sim.sellers]
    q       = [seller.quality for seller in sim.sellers]
    supx    = [supplier.position[0] for supplier in sim.suppliers]
    supy    = [supplier.position[1] for supplier in sim.suppliers]
    supq    = [supplier.quality for supplier in sim.suppliers]

    plot_queue = Queue()
    mine, theirs = Pipe()
    towns   = []
    if sim.environment:
        towns = sim.environment.towns
        plot_queue.put( (x, y, q, supx, supy, supq, towns) )
    else:
        plot_queue.put( (x, q, supx, supq) )

    animator = Animator(plot_queue, theirs)
    animator_proc = Process(target=animator.animate)
    animator_proc.start()

    mean_qualities = []
    for i in range(num_trials):
        if (mine.poll()):
            request = mine.recv()
            if request == "Pause":
                wait_for_input(sim, mine)
            elif request == "Stop":
                global stop
                stop = True
                return # This stops everything
            else:
                actor, ind = request
                if actor == "Supplier":
                    mine.send([sim.suppliers[ind]])
                else:
                    mine.send([sim.sellers[ind]])

            if stop:
                return


        #debug("First Seller Quality: {}".format(sim.sellers[0].quality))

        #sim.time_step_sweep()
        sim.time_step_sto()

        if (i % 10 == 0):
            x       = [seller.position[0] for seller in sim.sellers]
            y       = [seller.position[1] for seller in sim.sellers]
            q       = [seller.quality for seller in sim.sellers]
            supx    = [supplier.position[0] for supplier in sim.suppliers]
            supy    = [supplier.position[1] for supplier in sim.suppliers]
            supq    = [supplier.quality for supplier in sim.suppliers]

            if sim.environment:
                plot_queue.put( (x, y, q, supx, supy, supq) )
            else:
                plot_queue.put( (x, q, supx, supq) )
            #plot_queue.put( (x, q, supx, supq) )
            qual = sim.watcher.get_mean_qual()
            mean_qualities.append(qual)
            print("Mean Quality: {}".format(qual))
            quals = [s.quality for s in sim.sellers]
            top = np.argmax(quals)
            print("Top Quality:  {} from {}".format(quals[top], top))
            top, n = sim.watcher.get_top()
            print("Top seller: {}, picked {} times".format(top, n))
            #print("Corresp Quality: {}".format(sim.sellers[top].quality))
            print("Number failed sales: {}".format(sim.watcher.out_of_stock))
            #print(sim.watcher.sup_no_sales)
            print("-" * 80)
        sim.watcher.reset()

    debug("Simulation was {} ahead of animation".format(plot_queue.qsize()))
    while not plot_queue.empty():
        time.sleep(0.05)
        if not (animator_proc.is_alive()):
            break

    plot_queue.put("Stop")
    if animator_proc.is_alive():
        wait_for_input(sim, mine)
        animator_proc.join()

    plt.clf()
    time.sleep(0.1)

    plt.plot(range(0, num_trials, 10), mean_qualities)
    plt.show()

def main():
    global stop
    stop  = False

    parser = OptionParser("Usage: >> python trust.py [options] <config_file>")
    parser.add_option("-e", action="store_true", default=False,
        help="Use this option to use the environemt functionality")
    parser.add_option("-n", action="store", dest="n_runs", default=1000, type="int",
        help="Use this to specify the maximum number of runs (default: 1000)")
    parser.add_option("--dp", action="store_true", default=False,
        help="Use this option to enable dynamic pricing for vendors")
    parser.add_option("--da", action="store_true", default=False,
        help="Use this option to enable dynamic numbers of vendors")
    parser.add_option("--ni", action="store", default=1000, type="int",
        help="Use this option to specify the number of patients (default: 1000)")
    parser.add_option("--nj", action="store", default=100, type="int",
        help="Use this option to specify the number of sellers (default: 100)")
    parser.add_option("--nk", action="store", default=10, type="int",
        help="Use this option to specify the number of suppliers (default: 10)")

    (options, args) = parser.parse_args()

    num_trials = options.n_runs
    ni = options.ni
    nj = options.nj
    nk = options.nk
    dynam_price = options.dp
    dynam_actors = options.da


    if options.e:
        sim = Simulation(ni, nj, nk, env_file, dynam_price, dynam_actors)
    else:
        sim = Simulation(ni, nj, nk, None, dynam_price)

    run_sim(num_trials, sim)


if __name__ == "__main__":
    main()
