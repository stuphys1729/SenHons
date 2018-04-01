import numpy as np
import math
from random import gauss
from random import random as rand
from logging import basicConfig, debug, DEBUG

basicConfig(level=DEBUG,
            format='(%(threadName)-10s) %(message)s',
            )

class Environment():
    """ This class models the total environment of the simulaion. For now it
        only contains towns but this could be extended
    """

    def __init__(self, config_file):

        self.towns = []
        total = 0
        with open(config_file, 'r') as f:
            for line in f:
                data = line.split(" ")
                if data[0] == '#' or data[0] == '#\n':
                    continue

                self.towns.append( Town(data[0], int(data[1]), float(data[2]),
                    float(data[3]), float(data[4]), float(data[4])) )

                total += int(data[1])

        self.prob_dist = []
        self.system_size = [0., 0.]
        for town in self.towns:
            norm = town.size/total
            self.prob_dist.append(norm)

            xmax = town.x + 5*town.sigmax # probabilistic maximum
            if (xmax > self.system_size[0]):
                self.system_size[0] = xmax
            ymax = town.y + 5*town.sigmay
            if (ymax > self.system_size[1]):
                self.system_size[1] = ymax




    def get_position(self):
        # Choose a town to draw from
        town = np.random.choice(self.towns, p=self.prob_dist)
        # Get a new position from it
        return town.get_position()


class Town():
    """ This class models a town in the simulation """

    def __init__(self, name, size, x, y, sigmax, sigmay):

        self.name   = name
        self.size   = size
        self.x      = x
        self.y      = y
        self.sigmax = sigmax
        self.sigmay = sigmay

    def __str__(self):

        return( "Name: {0} | Size: {1:02d} | Position: ({2:6.02f},{3:6.02f}) | Variance: ({4:4.02f},{5:4.02f})".format(
            self.name, self.size, self.x, self.y, self.sigmax, self.sigmay) )

    def get_position(self):
         return ( gauss(self.x, self.sigmax),
                    gauss(self.y, self.sigmay) )




class Actor():
    """ This is the generalised class for actors in the simulation """
    # Constants for all actors
    distance_parameter = 0.005
    explore_parameter = 0.5
    top_n = 20
    epsilon = 0.1

    def __init__(self, position, uid, n=0, watcher=None):
        self.watcher = watcher
        self.position = position
        self.id = uid
        self.min_purchase = 1
        # Initialise the array of trust scores for each seller/supplier
        self.experiences = np.zeros((n,2), dtype=np.int16)
                            # successes , trials (of that seller/supplier)
        self.N = 0 # Total number of trials


    def distance_to(self, position, system_size=None):
        """
        Calculates the euclidean distance from this actor to the passed one. If
        the straight-line distance is greater than half the system size, the
        periodic boundary means that the actors are actually closer.
        """
        # TODO: make this 2d

        if type(system_size) is int: # 1D case
            this = self.position[0]
            that = position[0]

            raw_dist = abs(this-that)

            if (raw_dist > system_size/2):
                return system_size - raw_dist
            else:
                return raw_dist

        elif type(system_size) is list: # 2D case
            x_dist = abs(self.position[0] - position[0])
            y_dist = abs(self.position[1] - position[1])

            if x_dist > system_size[0]/2:
                x_dist = system_size[0] - x_dist
            if y_dist > system_size[1]/2:
                y_dist = system_size[1] - y_dist

            return np.sqrt( x_dist**2 + y_dist**2 )
        else:
            debug(system_size)

    def make_dist_array(self, dependencies, system_size):

        self.distance_array = [self.distance_to(dependencies[i].position,
                                system_size) for i in range(len(dependencies))]

        #if (type(self) == Seller):
            #debug("Seller Distance Matrix: {}".format(self.distance_array))


    def choose_best(self, actor_list):
        """ UCB formula to decide best actor to buy from """
        choices = []
        for i in range(len(actor_list)):
            dist_cont = Actor.distance_parameter*self.distance_array[i]
            assert(dist_cont >= 0)
            xn, n = self.experiences[i]
            x = xn / n
            if n != 0:
                ucb = x + Actor.explore_parameter*math.sqrt(
                                                        2*math.log(self.N)/n )
            else:
                ucb = 1.0 # avoiding division by 0
            #       trust - distance - price
            total = ucb - dist_cont - actor_list[i].price
            choices.append(total)
        self.N += 1

        consider = min(Actor.top_n, len(actor_list))
        top_n = np.argpartition(choices, range(len(choices)-consider,
                                    len(choices)))[len(choices)-consider:]
        #debug(top_n)
        self.watcher.inform_choice(top_n[-1])
        best = None
        for dep in reversed(top_n):
            if actor_list[dep].supply >= self.min_purchase:
                best = dep
                break
            else:
                self.watcher.inform_oos()
        t = actor_list[0].__class__.__name__
        if best == None:
            for dep in top_n:
                debug("{} number {} has supply {}".format(t, dep,
                                                        actor_list[dep].supply))
            raise AttributeError("Best {} were all sold out".format(top_n))

        #debug("Buying from {} number {}".format(t, best))
        result = self.buy_from(actor_list[best]) # specific to class
        if result:
            self.experiences[best][0] += 1
        self.experiences[best][1] += 1

        return




class Patient(Actor):
    """
    This is the class to model each patient
    """

    def __init__(self, uid, nj, watcher=None, position=(0,0)):
        super().__init__(position, uid, nj, watcher)
        return

    def __str__(self):
        return "Patient {0:04d} |\tPosition ({1:6.02f},{2:6.02f})".format(
                    self.id, self.position[0], self.position[1])

    def __repr__(self):
        return "Patient {0:04d} | Psition: ({1:6.02f},{2:6.02f})".format(
                    self.id, self.position[0], self.position[1])

    def buy_from(self, seller):
        medicine = seller.make_purchase()
        # Patient uses medicine straight away
        better = self.take(medicine)

        return better

    def take(self, medicine):
        """ This can be extended for more medicine types """
        # TODO: Add in placebo effect
        return (medicine - rand()) > 0


class Seller(Actor):
    """
    This is the class to model a seller of medicine
    """

    def __init__(self, uid, nk, watcher=None, init_supply=0, init_cash=20, position=(0,0)):
        super().__init__(position, uid, nk, watcher)

        # Initial stock and cash
        self.supply = init_supply
        self.cash   = init_cash + rand()

        self.min_purchase = 10 # Overwrites '1' from parent class

        # Initial price and quality are random
        self.price      = rand() + 1
        self.strategy   = rand()  # He uses this as a multiplier for the trust
                                    # metric, not sure if I need it.
        self.quality    = rand()

        return

    def __str__(self):
        return "Seller {0:04d} |\tQuality: {1:04f} |\t Price: {2:04f} |\tPosition ({3:6.02f},{4:6.02f})".format(
                    self.id, self.quality, self.price, self.position[0], self.position[1])

    def __repr__(self):
        return "Seller {0:04d} | Quality: {1:04f} | Price: {2:04f} | Position ({3:6.02f},{4:6.02f})".format(
                    self.id, self.quality, self.price, self.position[0], self.position[1])

    def out_of_stock(self):
        debug("Seller increased their price")
        self.price += Actor.epsilon*rand()

    def make_purchase(self):
        #debug("Seller selling 1, supply: {} before" .format(self.supply))
        self.supply -= 1
        self.cash += self.price
        self.watcher.inform_sale(self) # keep track of average quality
        if self.supply < 1:
            self.out_of_stock()
        return self.price # in case we want patients to have money

    def buy_from(self, supplier):
        # Sellers want to buy as much as possible
        amount = int(min(np.floor(self.cash/supplier.price), supplier.supply))
        if amount > 0:
            supplier.make_purchase(amount)
            self.cash -= amount*supplier.price

            # New quality is average of old and new
            self.quality = (self.quality*self.supply
                            + supplier.quality*amount)/(self.supply + amount)
            self.supply += amount

            # Do a quality test
            result = self.test_supply(supplier.quality)
            return result
        else: # We ran out of money
            # not sure what to do here?
            self.generate_new_strategy()
            return 0

    def generate_new_strategy(self):
        pass


    def test_supply(self, quality): # same as patient for now
        return (quality - rand()) > 0


class Supplier(Actor):
    """ This is the class to model a wholesaler """

    def __init__(self, uid, watcher, position=(0,0)):
        super().__init__(position, uid, 0, watcher)

        # Initial inventory and cash
        self.supply = 300
        self.cash   = 10 + rand()

        # Start with random quality
        self.quality = rand()
        self.strat  = self.quality

        # Initial cost random
        self.price = 0.5 + rand() # Could be dependent on quality?
        # self.cost = self.quality + rand()  ?

        return

    def __str__(self):
        return "Supplier {0:04d} |\tQuality: {1:04f} |\t Price: {2:04f} |\tPosition ({3:6.02f},{4:6.02f})".format(
                        self.id, self.quality, self.price, self.position[0], self.position[1])

    def __repr__(self):
        return "Supplier {0:04d} | Quality: {1:04f} | Price: {2:04f} | Position ({3:6.02f},{4:6.02f})".format(
                        self.id, self.quality, self.price, self.position[0], self.position[1])


    def out_of_stock(self):
        debug("Supplier increased their price")
        self.price += Actor.epsilon*rand()

    def make_purchase(self, amount):
        #debug("Supplier selling {}, supply: {} before".format(
                                                        #amount, self.supply))
        self.supply -= amount
        self.cash += self.price*amount
        if self.supply < 1:
            self.out_of_stock()
        return self.price


    def make_meds(self):
        self.cash -= 2 # Running costs
        if self.cash > 1:
            amount = np.floor(self.cash)
            qual = self.supply*self.quality + amount*self.strat
            self.quality = qual / (self.supply + amount)
            self.supply += amount

        else:
            #debug("Supplier {} ran out of cash".format(self.id))
            self.watcher.inform_no_sup_sales(self.id)
            #self.generate_new_strategy()

        # Either way, self.cash is now between 0 and 1

    def generate_new_strategy(self):
        self.strat = abs(min((self.strat + Actor.epsilon*(rand()-0.5)), 1.0))
        self.price = rand() + 1 # depend on quality?
        return
