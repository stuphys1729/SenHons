"""
This file runs a simulation of the evolution of trust in medicine.

The model consists of Patients, who go to Sellers to purchase medicine of an
unknown quality, and either get better or they do not (depending on medicine
quality and the placebo effect) and update their trust in that seller
accordingly. The Sellers themselves purchase their medicine from Suppliers.
"""
from random import random, shuffle
import numpy as np
import matplotlib.pyplot as plt
from multiprocessing import Process, Queue
from logging import basicConfig, debug, DEBUG

from actors import *
from animator import Animator

basicConfig(level=DEBUG,
            format='(%(threadName)-10s) %(message)s',
            )

class Watcher():
    """
    This class handles the clairvoyance of the system, watching all sales
    """

    def __init__(self):
        self.reset()

    def reset(self):
        self.reset_sales()
        self.reset_stock()
        self.reset_choices()

    def reset_sales(self):
        self.num_purchases = 0
        self.mean_quality = 0.

    def reset_choices(self):
        self.choice_tally = {}

    def reset_stock(self):
        self.out_of_stock = 0

    def inform_sale(self, seller):
        self.mean_quality = (self.mean_quality*self.num_purchases +
                                seller.quality) / (self.num_purchases+1)
        self.num_purchases += 1

    def inform_choice(self, index):
        if index in self.choice_tally:
            self.choice_tally[index] += 1
        else:
            self.choice_tally[index] = 1

    def inform_oos(self):
        self.out_of_stock += 1

    def get_top(self):
        v = list(self.choice_tally.values())
        k = list(self.choice_tally.keys())
        return k[v.index(max(v))], max(v)

class Simulation():
    """
    This is the class to hold the simulation parameters
    """

    def __init__(self, ni=1000, nj=100, nk=10, cost=1.0):

        self.epsilon = 0.1 # Not sure what this is for
        self.ni = ni    # Number of patients
        self.nj = nj    # Number of sellers
        self.nk = nk    # Number of wholesalers
        self.cost = cost    # Default cost of medicine (before markup)
        self.watcher = Watcher() # For keeping track of mean quality and such

        self.suppliers = [Supplier() for k in range(nk)]

        #ratio = np.floor(self.ni/self.nj)
        self.sellers = [Seller(self.nk, self.watcher) for j in range(nj)]

        self.patients = [Patient(self.nj, self.watcher) for i in range(ni)]

        self.set_positions_line()


    def set_positions_line(self):

        ratio = 1.0
        pos = 0.0
        for patient in self.patients:
            patient.position = (pos+random(), random())
            pos += ratio
        self.system_size = pos
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
        debug("Pos of last Supplier: {}".format(pos-ratio))

        for patient in self.patients:
            patient.make_dist_array(self.sellers, self.system_size)

        for seller in self.sellers:
            seller.make_dist_array(self.suppliers, self.system_size)

    def intialise_dist_arrays(self):

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

        for seller in self.sellers:
            # Each seller chooses their current best supplier
            seller.choose_best(self.suppliers)
            # This also handles the sale and quality test

        for supplier in self.suppliers:
            # Supplier makes 'stuff' based on current strategy
            supplier.make_meds()


def main():

    #sim = Simulation(200, 20, 2)
    sim = Simulation()

    x = [seller.position[0] for seller in sim.sellers]
    y = [seller.position[1] for seller in sim.sellers]
    q = [seller.quality for seller in sim.sellers]

    plot_queue = Queue()
    #plot_queue.put( (x, y, q) )
    plot_queue.put( (x, q) )
    animator = Animator(plot_queue)

    animator_proc = Process(target=animator.animate)
    animator_proc.start()



    for i in range(1000):
        #debug("First Seller Quality: {}".format(sim.sellers[0].quality))

        #sim.time_step_sweep()
        sim.time_step_sto()

        x = [seller.position[0] for seller in sim.sellers]
        y = [seller.position[1] for seller in sim.sellers]
        q = [seller.quality for seller in sim.sellers]
        #plot_queue.put( (x, y, q) )
        plot_queue.put( (x, q) )

        if (i % 10 == 0):
            print("Mean Quality: {}".format(sim.watcher.mean_quality))
            quals = [s.quality for s in sim.sellers]
            top = np.argmax(quals)
            print("Top Quality:  {} from {}".format(quals[top], top))
            top, n = sim.watcher.get_top()
            print("Top seller: {}, picked {} times".format(top, n))
            print("Corresp Quality: {}".format(sim.sellers[top].quality))
            print("Number failed sales: {}".format(sim.watcher.out_of_stock))
            print("")
        sim.watcher.reset()



if __name__ == "__main__":
    main()
