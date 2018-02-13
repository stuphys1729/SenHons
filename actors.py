import numpy as np
import math
from random import random


class Actor():
    """ This is the generalised class for actors in the simulation """
    # Constants for all actors
    self.distance_parameter = 0.1
    self.explore_parameter = 0.5
    self.top_n = 10

    def __init__(self, position, n):
        self.position = position
        self.min_purchase = 1
        # Initialise the array of trust scores for each seller/supplier
        self.experiences = np.zeros((n,2), dtype=np.int16)
                            # successes , trials (of that seller/supplier)


    def distance_to(self, position, system_size=None):
        """
        Calculates the euclidean distance from this actor to the passed one. If
        the straight-line distance is greater than half the system size, the
        periodic boundary means that the actors are actually closer.
        """
        # TODO: make this 2d

        this = self.position[0]

        raw_dist = abs(this-position)
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
        choices = []
        for i in range(len(actor_list)):
            dist_cont = self.distance_parameter*self.distance_array[i]
            x, n = self.experiences[i]
            if n != 0:
                ucb = x + self.explore_parameter*math.sqrt( 2*math.log(self.N)/n )
            else:
                ucb = 1.0 # avoiding division by 0
            total = ucb - dist_cont - actor_list[i].price
        top_n = np.argpartition(choices, range(self.top_n))[:self.top_n]

        best = None
        for dep in top_n:
            if dep.supply >= self.min_purchase:
                best = dep
                break
        if not best:
            raise AttributeError("Best {} were all sold out".format(self.top_n))

        result = self.buy_from(best) # specific to class
        if result:
            self.experiences[j][0]++
        self.experiences[j][1]++



class Patient(Actor):
    """
    This is the class to model each patient
    """

    def __init__(self, nj, position=(0,0)):
        super().__init__(position, nj)
        return

    def buy_from(self, seller, j):
        medicine = seller.make_purchase(self)
        # Patient uses medicine straight away
        better = self.take(medicine)

        return better

    def take(medicine):
        """ This can be extended for more medicine types """
        return (medicine - random()) > 0


class Seller(Actor):
    """
    This is the class to model a seller of medicine
    """

    def __init__(self, nk, init_supply=10, position=(0,0)):
        super().__init__(position, nk)

        # Initial stock and cash
        self.supply = init_supply
        self.cash   = 10

        self.min_purchase = 10 # Overwrites '1' from parent class

        # Initial price and quality are random
        self.price      = random() + 1
        self.strategy   = random()
        self.quality    = random()

        return

    def make_purchase(self):
        self.supply--
        self.cash += self.price
        return self.price # in case we want patients to have money

    def buy_from(self, supplier):
        # Sellers want to buy as much as possible
        amount = min(np.floor(self.cash/supplier.price), supplier.supply)
        if amount > 0:
            supplier.make_purchase(amount)
            self.cash -= amount*supplier.price
            result = self.test_supply(supplier.quality)
            return result


    def test_supply(self, quality):
        """ Same as patient for now """
        return (medicine - random()) > 0


class Supplier(Actor):
    """ This is the class to model a wholesaler """

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
        # self.cost = self.quality + random()  ?

    def make_purchase(self, amount):
        self.supply -= amount
        self.cash += self.price*amount
        return self.price
