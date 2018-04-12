import numpy as np
import math
from random import gauss, random as rand
from logging import basicConfig, debug, DEBUG
import copy

basicConfig(level=DEBUG,
            format='(%(threadName)-10s) %(message)s',
            )

class Watcher():
    """
    This class handles the clairvoyance of the system, watching all sales
    """

    def __init__(self):
        self.reset()
        self.mean_quality_list = []
        self.sup_no_sales = {}

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

    def get_mean_qual(self):
        self.mean_quality_list.append(self.mean_quality)
        return self.mean_quality

    def inform_sale(self, seller):
        self.mean_quality = (self.mean_quality*self.num_purchases +
                                seller.quality) / (self.num_purchases+1)
        self.num_purchases += 1

    def inform_choice(self, uid):
        if uid in self.choice_tally:
            self.choice_tally[uid] += 1
        else:
            self.choice_tally[uid] = 1

    def inform_oos(self):
        self.out_of_stock += 1

    def inform_no_sup_sales(self, sup_id):
        if sup_id in self.sup_no_sales:
            self.sup_no_sales[sup_id] += 1
        else:
            self.sup_no_sales[sup_id] = 1

    def get_top(self):
        v = list(self.choice_tally.values())
        k = list(self.choice_tally.keys())
        return k[v.index(max(v))], max(v)

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
                    float(data[3]), float(data[4]), float(data[5])) )

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
    cost_parameter = 0.5

    top_n = 20
    epsilon = 0.1
    bust_number = 20

    def __init__(self, position, uid, system_size, watcher=None, dynam_price=False):
        self.watcher        = watcher
        self.position       = position
        self.uid            = uid
        self.min_purchase   = 1
        self.dynamic_price  = dynam_price

        self.system_size    = system_size
        # Initialise the array of trust scores for each seller/supplier
        self.experiences    = {}
        self.distances      = {}
                            # successes , trials (of that seller/supplier)
        self.N              = 0 # Total number of trials


    def distance_to(self, position):
        """
        Calculates the euclidean distance from this actor to the passed one. If
        the straight-line distance is greater than half the system size, the
        periodic boundary means that the actors are actually closer.
        """

        if type(self.system_size) is float or type(self.system_size) is int: # 1D case
            this = self.position[0]
            that = position[0]

            raw_dist = abs(this-that)

            if (raw_dist > self.system_size/2):
                return self.system_size - raw_dist
            else:
                return raw_dist

        elif type(self.system_size) is list: # 2D case
            x_dist = abs(self.position[0] - position[0])
            y_dist = abs(self.position[1] - position[1])

            if x_dist > self.system_size[0]/2:
                x_dist = self.system_size[0] - x_dist
            if y_dist > self.system_size[1]/2:
                y_dist = self.system_size[1] - y_dist

            return np.sqrt( x_dist**2 + y_dist**2 )
        else:
            raise AttributeError(self.system_size)


    def make_dist_array(self, dependencies):

        for actor in dependencies:
            #debug("Actor id: {}".format(actor.uid))
            actor_uid = actor.uid
            self.distances[actor_uid] = self.distance_to(actor.position)
            if actor_uid not in self.experiences:
                #debug("Actor id: {}".format(actor.uid))
                self.experiences[actor_uid] = np.zeros(2, dtype=np.int16)
                # We also initialise the experiences counter here
        #debug(self.experiences)


    def choose_best(self, actor_list):
        """ UCB formula to decide best actor to buy from """
        assert len(actor_list) > 0
        choices = []
        for actor in actor_list:
            actor_id = actor.uid # This might be a new actor in the system
            if not (actor_id in self.experiences):
                # Start tracking the new actor
                self.experiences[actor_id] = np.zeros(2, dtype=np.int16)
            if not (actor_id in self.distances):
                # We might have inherited experiences, but not the distance
                self.distances[actor_id] = self.distance_to(actor.position)

            dist_cont = Actor.distance_parameter*self.distances[actor_id]

            xn, n = self.experiences[actor_id]
            x = xn / n
            if n != 0:
                ucb = x + Actor.explore_parameter*math.sqrt(
                                                        2*math.log(self.N)/n )
            else:
                ucb = 1.0 # avoiding division by 0
            #       trust - distance  price
            total = ucb - dist_cont - Actor.cost_parameter*actor.price
            choices.append(total)
        self.N += 1

        consider = min(Actor.top_n, len(actor_list))
        top_n = np.argpartition(choices, range(len(choices)-consider,
                                    len(choices)))[len(choices)-consider:]
        #debug(top_n)
        self.watcher.inform_choice(actor_list[top_n[-1]].uid)
        best = None
        for dep in reversed(top_n):
            if actor_list[dep].supply >= self.min_purchase:
                best = actor_list[dep]
                break
            else:
                self.watcher.inform_oos()

        if best == None:
            t = actor_list[0].__class__.__name__
            for dep in top_n:
                debug("{} number {} has supply {}".format(t, dep,
                                                        actor_list[dep].supply))
            raise AttributeError("Best {} were all sold out".format(top_n))


        result, function = self.buy_from(best) # specific to class
        if result != None:
            self.experiences[best.uid][0] += 1
        self.experiences[best.uid][1] += 1

        return function

    def make_vendor_link(self, old, new):
        # Initialises the actor's trust in the new vendor based on their trust
        # in the old one
        self.experiences[new] = np.array(self.experiences[old], copy=True)
        # However, we are `less sure` about this value since it a new vendor
        self.experiences[new][1] = np.int16(np.floor(self.experiences[new][1]/2))


class Patient(Actor):
    """
    This is the class to model each patient
    """

    def __init__(self, uid, system_size, watcher, position=(0,0)):
        super().__init__(position, uid, system_size, watcher)
        return

    def __str__(self):
        return "Patient {0:04d} |\tPosition ({1:6.02f},{2:6.02f})".format(
                    self.uid, self.position[0], self.position[1])

    def __repr__(self):
        return "Patient {0:04d} | Psition: ({1:6.02f},{2:6.02f})".format(
                    self.uid, self.position[0], self.position[1])

    def buy_from(self, seller):
        medicine = seller.make_purchase()
        # Patient uses medicine straight away
        better = self.take(medicine)

        return better, "" # Second argument to keep with inherited class template

    def take(self, medicine):
        """ This can be extended for more medicine types """
        # TODO: Add in placebo effect
        return (medicine - rand()) > 0


class Seller(Actor):
    """
    This is the class to model a seller of medicine
    """

    def __init__(self, uid, system_size, watcher, dynam_price=False, position=(0,0), init_supply=0):
        super().__init__(position, uid, system_size, watcher, dynam_price)

        # Initial stock and cash
        self.supply = init_supply
        self.cash   = 30 + rand()

        self.min_purchase = 10 # Overwrites '1' from parent class
        self.expansion_amount = 20 # When we have 2* this, we can expand
        self.num_out = 0 # Keep track of the number of times we make no sales

        # Initial price and quality are random
        self.price      = rand() + 1
        self.strategy   = rand()  # He uses this as a multiplier for the trust
                                    # metric, not sure if I need it.
        self.quality    = rand()

        return

    def __str__(self):
        return "Seller {0:04d} |\tQuality: {1:04f} |\t Price: {2:04f} |\tPosition ({3:6.02f},{4:6.02f})".format(
                    self.uid, self.quality, self.price, self.position[0], self.position[1])

    def __repr__(self):
        return "Seller {0:04d} | Quality: {1:04f} | Price: {2:04f} | Position ({3:6.02f},{4:6.02f})".format(
                    self.uid, self.quality, self.price, self.position[0], self.position[1])

    def out_of_stock(self):
        if self.dynamic_price:
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
            self.num_out = 0
            supplier.make_purchase(amount)
            self.cash -= amount*supplier.price

            # New quality is average of old and new
            self.quality = (self.quality*self.supply
                            + supplier.quality*amount)/(self.supply + amount)
            self.supply += amount

            function = ""
            if self.supply > 2*self.expansion_amount:
                # Costs us 1 for setup cost and one for new seller supply
                function = "New"

            # Do a quality test
            result = self.test_supply(supplier.quality)
            return result, function
        else: # We ran out of money
            # not sure what to do here?
            #self.generate_new_strategy()
            self.num_out += 1
            if self.num_out > Actor.bust_number:
                # We have gone bust
                return None, "End"
            else:
                return None, ""


    def make_new(self, uid, position):
        """ A method to make a new seller from this one's properties """
        experiences = copy.deepcopy(self.experiences)
        quality = self.quality
        price = self.price
        N = self.N
        supply = self.expansion_amount
        new_seller = Seller(uid, self.system_size, self.watcher,
                                self.dynamic_price, position, supply)
        self.supply -= self.expansion_amount
        new_seller.experiences = experiences
        new_seller.quality = quality
        new_seller.price = price
        new_seller.N = N

        return new_seller

    def generate_new_strategy(self):
        pass


    def test_supply(self, quality): # same as patient for now
        return (quality - rand()) > 0


class Supplier(Actor):
    """ This is the class to model a wholesaler """

    def __init__(self, uid, system_size, watcher, dynam_price=False, position=(0,0), init_supply=500):
        super().__init__(position, uid, system_size, watcher, dynam_price)

        # Initial inventory and cash
        self.supply = init_supply
        self.cash   = rand()
        self.expansion_amount = 500
        self.num_out = 0 # Keep track of how many times we don't make sales

        # Start with random quality
        self.quality = rand()
        self.strat  = self.quality

        # Initial cost random
        self.price = 1.0 + 0.25*rand() # Could be dependent on quality?
        # self.cost = self.quality + rand()  ?

        return

    def __str__(self):
        return "Supplier {0:04d} |\tQuality: {1:04f} |\t Price: {2:04f} |\tPosition ({3:6.02f},{4:6.02f})".format(
                        self.uid, self.quality, self.price, self.position[0], self.position[1])

    def __repr__(self):
        return "Supplier {0:04d} | Quality: {1:04f} | Price: {2:04f} | Position ({3:6.02f},{4:6.02f})".format(
                        self.uid, self.quality, self.price, self.position[0], self.position[1])


    def out_of_stock(self):
        if self.dynamic_price:
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
        #self.cash -= 2 # Running costs
        if self.cash > 1:
            self.num_out = 0
            amount = np.floor(self.cash)
            qual = self.supply*self.quality + amount*self.strat
            self.quality = qual / (self.supply + amount)
            self.supply += amount
            self.cash -= amount

            if self.supply > 2*self.expansion_amount:
                # We can make another supplier actor
                #debug(self.supply)
                return "New"

            return ""

        else:
            #debug("Supplier {} ran out of cash".format(self.uid))
            #self.cash = 0 # Gives suppliers a chance to come back
            self.watcher.inform_no_sup_sales(self.uid)
            self.num_out += 1
            if self.num_out > Actor.bust_number:
                # We have gone bust
                return "End"
            #self.generate_new_strategy()

        # Either way, self.cash is now between 0 and 1

    def generate_new_strategy(self):
        self.strat = abs(min((self.strat + Actor.epsilon*(rand()-0.5)), 1.0))
        self.price = rand() + 1 # depend on quality?
        return


    def make_new(self, uid, position):
        """ A method to make a new supplier from this one's properties """
        quality = self.quality
        price = self.price
        strategy = self.strat
        supply = self.expansion_amount
        new_supplier = Supplier(uid, self.system_size, self.watcher,
                                    self.dynamic_price, position, supply)
        self.supply -= self.expansion_amount
        new_supplier.quality = quality
        new_supplier.price = price
        new_supplier.strat = strategy

        return new_supplier
