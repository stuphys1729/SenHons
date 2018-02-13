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

        self.suppliers = [Supplier() for k in range(nk)]

        ratio = np.floor(self.ni/self.nj)
        self.sellers = [Seller(self.nk, ratio) for j in range(nj)]

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

        # Loop over patients
            # Each patient chooses their current best Seller
            # Update seller's money from sale
            # Patient gets better or worse based on quality and placebo
            # Update stats on patient's experience
            # Keep track of mean quality

        # Loop over Sellers
            # Each Seller chooses their current best Supplier
            # They fill their stock with that Supplier's stuff
            # Update the inventories of both involved
            # update quality of Seller's stock based on average of existing and new
            # Update trust based on quality check

        # Loop over Suppliers
            # Supplier makes 'stuff' based on current strategy
            # Quality is updated as average of old and new
            # Supplier's cash goes down for costs
            # If it goes to zero, they generate new strategy and price

        pass



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

if __name__ == "__main__":
    main()
