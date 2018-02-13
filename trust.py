"""
This file runs a simulation of the evolution of trust in medicine.

The model consists of Patients, who go to Sellers to purchase medicine of an
unknown quality, and either get better or they do not (depending on medicine
quality and the placebo effect) and update their trust in that seller
accordingly. The Sellers themselves purchase their medicine from Suppliers.
"""
from random import random
import numpy as np
import matplotlib.pyplot as plt
from logging import basicConfig, debug, DEBUG

from actors import *

basicConfig(level=DEBUG,
            format='(%(threadName)-10s) %(message)s',
            )

class Watcher():
    """
    This class handles the clairvoyance of the system, watching all sales
    """

    def __init__(self):
        self.reset_mean()

    def reset_mean(self):
        self.num_purchases = 0
        self.mean_quality = 0.

    def update_mean(self, quality):
        self.mean_quality = (self.mean_quality*self.num_purchases + quality) / (self.num_purchases+1)
        self.num_purchases += 1
        

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

        self.patients = [Patient(self.nj) for i in range(ni)]

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



    def time_step(self):

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



def main():

    #sim = Simulation()
    sim = Simulation(200, 20, 2)

    plt.scatter([sim.patients[i].position[0] for i in range(len(sim.patients))],
                [sim.patients[i].position[1] for i in range(len(sim.patients))],
                c='red', label="Patients")
    plt.scatter([sim.sellers[i].position[0] for i in range(len(sim.sellers))],
                [sim.sellers[i].position[1] for i in range(len(sim.sellers))],
                c='blue', label="Sellers")
    plt.scatter([sim.suppliers[i].position[0] for i in range(len(sim.suppliers))],
                [sim.suppliers[i].position[1] for i in range(len(sim.suppliers))],
                c='green', label="Suppliers")
    plt.legend()
    plt.ylim( (-5,5) )
    plt.show()

    sim.time_step()

if __name__ == "__main__":
    main()
