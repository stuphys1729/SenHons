"""
This file runs a simulation of the evolution of trust in medicine.

The model consists of Patients, who go to Sellers to purchase medicine of an
unknown quality, and either get better or they do not (depending on medicine
quality and the placebo effect) and update their trust in that seller
accordingly. The Sellers themselves purchase their medicine from Suppliers.
"""

from random import random
import numpy as np


class Simulation():
    """
    This is the class to hold the simulation parameters
    """

    def __init__(ni=1000, nj=100, nk=10, cost=1.0):

        self.ni = ni    # Number of patients
        self.nj = nj    # Number of sellers
        self.nk = nk    # Number of wholesalers
        self.cost = cost    # Default cost of medicine (before markup)

        self.patients = [Patient(self.nj) for i in range(ni)]
        for patient in self.patients:
            # TODO: allocate their position in line or ring
            patient.position = (0,0)


        self.sellers = [Seller(self.nk) for j in range(nj)]
        for seller in self.sellers:
            # TODO: allocate their position in line or ring
            seller.position = (0,0)

        self.suppliers = [Supplier() for k in range(nk)]
        for supplier in self.suppliers:
            # TODO: allocate their position in line or ring
            supplier.position = (0,0)

class Actor():
    """
    This is the generalised class for actors in the simulation
    """
    def __init__(position):
        self.position = position


class Patient(Actor):
    """
    This is the class to model each patient
    """

    def __init__(nj, position=0.0):
        # Initialise the array of trust scores for each seller
        self.trust_matrix = [ [0.5,0] for x in range(nj)]
        super().__ini__(position)

class Seller(Actor):
    """
    This is the class to model a seller of medicine
    """

    def __init__(nk, position=0.0):
        # Initialise the array of trust scores for each wholesaler
        self.trust_matrix = [ [0.5,0] for x in range(nk)]



        super().__init__(position)

class Supplier(Actor):
    """
    This is the class to model a wholesaler
    """
    # Initial inventory and cash
    self.supply = 100
    self.cash   = 10 + random()
