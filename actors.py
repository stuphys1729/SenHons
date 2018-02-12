import numpy as np
from random import random


class Actor():
    """
    This is the generalised class for actors in the simulation
    """
    def __init__(self, position, n):
        self.position = position

        # Initialise the array of trust scores for each seller/supplier
        self.experiences = np.zeros((n,2), dtype=np.int16)
                            # successes , trials (of that seller/supplier)
        self.UCB_scores = np.zeros(n)
        self.distances = np.zeros(n)
        self.total_scores = np.zeros(n)


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

    def choose_best(self, actor_list):
        """ UCB formula to decide best actor to buy from """
        return np.argmax(self.total_scores)


class Patient(Actor):
    """
    This is the class to model each patient
    """

    def __init__(self, nj, position=(0,0)):
        super().__init__(position, nj)
        return

    def buy_from(self, seller):
        pass



class Seller(Actor):
    """
    This is the class to model a seller of medicine
    """

    def __init__(self, nk, init_supply=10, position=(0,0)):
        super().__init__(position, nk)

        # Initial stock and cash
        self.supply = init_supply
        self.cash   = 10

        # Initial price and quality are random
        self.price      = random() + 1
        self.strategy   = random()
        self.quality    = random()

        return

    def buy_from(self, supplier):
        """ Should I make it more general? """
        pass


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
