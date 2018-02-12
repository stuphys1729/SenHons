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

basicConfig(level=DEBUG,
            format='(%(threadName)-14s) %(message)s',
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


    def time_step(self):
        


class Actor():
    """
    This is the generalised class for actors in the simulation
    """
    def __init__(self, position):
        self.position = position

    def distance_to(self, actor, system_size=None):
        """
        Calculates the euclidean distance from this actor to the passed one. If
        the straight-line distance is greater than half the system size, the
        periodic boundary means that the actors are actually closer.
        """
        # TODO: make this 2d

        this = self.position[0]
        that = actor.position[0]

        raw_dist = abs(this-that)
        if (system_size == None): return raw_dist
        elif (raw_dist > system_size/2):
            return system_size - raw_dist
        else:
            return raw_dist

    def make_dist_array(self, dependencies, system_size):

        self.distance_array = [self.distance_to(dependencies[i], system_size)
                                for i in range(len(dependencies))]

        if (type(self) == Seller):
            debug("Seller Distance Matrix: {}".format(self.distance_array))


class Patient(Actor):
    """
    This is the class to model each patient
    """

    def __init__(self, nj, position=(0,0)):
        super().__init__(position)

        # Initialise the array of trust scores for each seller
        self.trust_array = [ [0.5,0] for x in range(nj)]


class Seller(Actor):
    """
    This is the class to model a seller of medicine
    """

    def __init__(self, nk, init_supply=10, position=(0,0)):
        super().__init__(position)

        # Initialise the array of trust scores for each Supplier
        self.trust_array = [ [0.5,0] for x in range(nk)]

        # Initial stock and cash
        self.supply = init_supply
        self.cash   = 10

        # Initial price and quality are random
        self.price      = random() + 1
        self.strategy   = random()
        self.quality    = random()



class Supplier(Actor):
    """
    This is the class to model a wholesaler
    """

    def __init__(self, position=(0,0)):
        super().__init__(position)

        # Initial inventory and cash
        self.supply = 100
        self.cash   = 10 + random()

        # Start with random quality
        self.quality = random()
        self.strat  = self.quality

        # Initial cost random
        self.cost = 1 + random() # Could be dependent on quality?

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
