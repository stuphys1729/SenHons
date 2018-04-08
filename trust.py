"""
This file runs a simulation of the evolution of trust in medicine.

The model consists of Patients, who go to Sellers to purchase medicine of an
unknown quality, and either get better or they do not (depending on medicine
quality and the placebo effect) and update their trust in that seller
accordingly. The Sellers themselves purchase their medicine from Suppliers, and
also develop trust in the same way.
"""
from random import random, shuffle
import numpy as np
import matplotlib.pyplot as plt
from multiprocessing import Process, Queue, Pipe
from logging import basicConfig, debug, DEBUG
import time
import copy

from actors import *
from animator import Animator

basicConfig(level=DEBUG,
            format='(%(threadName)-10s) %(message)s',
            )


class Simulation():
    """
    This is the class to hold the simulation parameters
    """

    def __init__(self, ni=1000, nj=100, nk=10, env_file=None, cost=1.0):

        self.epsilon = 0.1 # Not sure what this is for
        self.ni = ni    # Initial number of patients
        self.nj = nj    # Initial number of sellers
        self.nk = nk    # Initial number of wholesalers
        self.cost = cost    # Default cost of medicine (before markup)
        self.watcher = Watcher() # For keeping track of mean quality and such

        if env_file:
            self.environment = Environment(env_file)
            self.system_size = self.environment.system_size
        else:
            self.system_size = ni # 1D

        self.suppliers = [Supplier(k, self.system_size, self.watcher) for k in range(nk)]
        self.last_supp = nk # Used to create unique ids for new suppleirs

        #ratio = np.floor(self.ni/self.nj)
        self.sellers = [Seller(j, self.system_size, self.watcher) for j in range(nj)]
        self.last_sell = nj

        self.patients = [Patient(i, self.system_size, self.watcher) for i in range(ni)]
        self.last_pat = ni

        if env_file:
            self.set_positions(self.environment)
        else:
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
            # If there is no environemt, we just space the actor out along a line
            ratio = 1.0
            pos = 0.0
            for patient in self.patients:
                patient.position = (pos+random(), random())
                pos += ratio
            debug("System size: " + str(self.system_size))
            debug("Pos of last patient: {}".format(pos-ratio))

            ratio = np.floor(self.ni/self.nj)
            debug("Ratio of Patients to Sellers: {}".format(ratio))
            pos = 0.0
            for seller in self.sellers:
                seller.position = (pos+random(), random())
                pos += ratio
            debug("Pos of last Seller: {}".format(pos-ratio))

            ratio = np.floor(self.ni/self.nk)
            debug("Ratio of Patients to Suppliers: {}".format(ratio))
            pos = 0.0
            for supplier in self.suppliers:
                supplier.position = (pos+random(), random())
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

    def time_step_sto(self, n_samples=None):
        """ Method to randomly choose n patients to purchase medicine """
        if not n_samples:
            n = len(self.sellers)
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

            if function: # The seller wants to do something
                if function == "New": # Set up new premices
                    position = self.environment.get_position()
                    new_seller = seller.make_new(self.last_sell, position)
                    new_seller.make_dist_array(self.suppliers)
                    self.sellers.append(new_seller)
                    self.last_sell += 1 # Set the id for the next seller
                    debug(str(seller))
                    debug("Making new seller: " + str(new_seller))

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

            if function: # The supplier wants us to do something
                if function == "New":
                    position = self.environment.get_position()
                    new_supplier = supplier.make_new(self.last_supp, position)
                    self.suppliers.append(new_supplier)
                    self.last_supp += 1
                    debug(str(supplier))
                    debug("Making new supplier: " + str(new_supplier))

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

def run_sim(num_trials, env_file=None):

    sim = Simulation(100, 20, 5, env_file)
    #sim = Simulation(1000, 100, 10, env_file)
    global stop

    x       = [seller.position[0] for seller in sim.sellers]
    y       = [seller.position[1] for seller in sim.sellers]
    q       = [seller.quality for seller in sim.sellers]
    supx    = [supplier.position[0] for supplier in sim.suppliers]
    supy    = [supplier.position[1] for supplier in sim.suppliers]
    supq    = [supplier.quality for supplier in sim.suppliers]
    towns   = []
    if sim.environment:
        towns = sim.environment.towns

    plot_queue = Queue()
    mine, theirs = Pipe()
    plot_queue.put( (x, y, q, supx, supy, supq, towns) )
    #plot_queue.put( (x, q, supx, supq) )
    animator = Animator(plot_queue, theirs)

    animator_proc = Process(target=animator.animate)
    animator_proc.start()


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

            plot_queue.put( (x, y, q, supx, supy, supq) )
            #plot_queue.put( (x, q, supx, supq) )
            print("Mean Quality: {}".format(sim.watcher.get_mean_qual()))
            quals = [s.quality for s in sim.sellers]
            top = np.argmax(quals)
            print("Top Quality:  {} from {}".format(quals[top], top))
            top, n = sim.watcher.get_top()
            print("Top seller: {}, picked {} times".format(top, n))
            #print("Corresp Quality: {}".format(sim.sellers[top].quality))
            print("Number failed sales: {}".format(sim.watcher.out_of_stock))
            max_cash = max([sell.cash for sell in sim.sellers])
            print("Maximum cash on sellers: {}".format(max_cash))
            #print(sim.watcher.sup_no_sales)
            print("-" * 80)
        sim.watcher.reset()

    debug("Simulation was {} ahead of animation".format(plot_queue.qsize()))
    while not plot_queue.empty():
        time.sleep(0.05)

    plot_queue.put("Stop")
    wait_for_input(sim, mine)
    animator_proc.join()

def main():
    #num_trials = 21
    num_trials = 400

    global stop
    stop  = False
    env = Environment("trust.config")
    run_sim(num_trials, 'trust.config')
    #sim = Simulation(200, 20, 2)
    #print(sim)


if __name__ == "__main__":
    main()
