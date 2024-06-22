"""This module contains the RidePoolController class, which represents a dispatching procedure in the simulation."""
import os
import sys
from typing import Callable, List, Union


if "SUMO_HOME" in os.environ:
    tools = os.path.join(os.environ["SUMO_HOME"], "tools")
    sys.path.append(tools)
else:
    raise ImportError("Please declare the environment variable 'SUMO_HOME'")
import numpy as np
from gymnasium import spaces

class RidePoolController:
    '''
    # Observation Space
    The default observation for ride pooling controller agent is a vector:

    obs = [non_served]

    - ```non_served``` is a number of active passenger requests which are not dispatched
    
    You can change the observation space by implementing a custom observation class. See :py:class:`sumo_rl.environment.observations.ObservationFunction`.

    # Action Space
    Action space is discrete, corresponding to the maximum occupancy of cars

    # Reward Function
    The default reward function is 'emissions-nonserved'. You can change the reward function by implementing a custom reward function and passing to the constructor of :py:class:`sumo_rl.environment.env.SumoEnvironment`.
    '''

    def __init__(
        self,
        env,
        max_capacity,
        reward_fn: Union[str, Callable],
        sumo,
        verbose: bool = False,
    ):
        """Initializes a RidePoolController object.

        Args:
            env (SumoEnvironment): The environment this traffic signal belongs to.
            reward_fn (Union[str, Callable]): The reward function. Can be a string with the name of the reward function or a callable function.
            sumo (Sumo): The Sumo instance.
        """
        self.env = env
        self.max_capacity = max_capacity
        self.last_measure = 0.0
        self.last_reward = None
        self.reward_fn = reward_fn
        self.sumo = sumo
        self.verbose = verbose
        self.observations_dim = 1 

        if type(self.reward_fn) is str:
            if self.reward_fn in RidePoolController.reward_fns.keys():
                self.reward_fn = RidePoolController.reward_fns[self.reward_fn]
            else:
                raise NotImplementedError(f"Reward function {self.reward_fn} not implemented")

        self.observation_fn = self.env.observation_class(self)

        self.observation_space = self.observation_fn.observation_space()
        self.action_space = spaces.Discrete(self.max_capacity)
              

    def getTaxi(self, person, taxis, action):
        ''' Assigns the taxi to the customer
            
            Returns taxi if it was assigned, and -1 if we cannot find the taxi for this person at the moment
        '''
        selectedTaxi = -1
        fromEdge = person.fromEdge
        toEdge = person.toEdge
        personId = person.persons[0]
        currentDistance = np.inf
        for taxi in taxis:
            # get number of current customers
            currentCustomers = self.sumo.vehicle.getParameter(taxi, "device.taxi.currentCustomers")
            currList = list(map(lambda x: x[1:], currentCustomers.split(" ")))
            
            '''
            If the taxi already has maximum amount of passengers or bigger amount,
            then we will not select it for the reservation.
            A taxi may have current amount of passengers bigger than the current maximum capacity,
            for the case when the maximum capacity may change between the iterations (e.g. tuned by RL algorithm).

            Length of current list will be 1 in the case when we do not have any current customers,
            in the case we also check for the second condition, preventing the case of neglecting the taxi
            which has no passengers (len(currList)==1) and maximum occupancy 1 (action==1). In this case
            currentCustomers string should be empty. 
            '''
            if len(currList) >= action and currentCustomers != '':
                continue

            # here we calculate pickup distance for the current taxi
            route = self.sumo.vehicle.getRoute(taxi) 
            taxiDepartEdge = route[0] 
            distance = self.sumo.simulation.getDistanceRoad(taxiDepartEdge, 0, fromEdge, 0, isDriving=True)   
            # and select taxi with a minimum pickup distance
            if distance < currentDistance:
                selectedTaxi = taxi
                currentDistance = distance
        return selectedTaxi

    def getCandPoi(self, poi, pdList):
        ''' Gets the list of candidate POIs (by candidate POI, we mean POI that may be visited next)
            For example, we cannot perform drop-off until we performed pick-up for this reservation.

            Return the list of candidate POI, from which we will select one with the minimum distance
            from the previous POI.
        '''
        candPoi = []
        # add to candidates all pois that 
        # have not been scheduled before
        for p in poi:
            found = False
            for pd in pdList:
                # ???
                if p == pd:
                    found = True
            if not found:
                # but if the poi is drop off
                # we add it only if pickup was
                # already performed or already scheduled
                if p[2] == "dropoff":
                    foundPickUp = False
                    for pd in poi:
                        if p[0] == pd[0] and pd[2] == "pickup":
                            foundPickUp = True
                    # if passenger was already picked up
                    if not foundPickUp:
                        candPoi.append(p) 
                    else:
                        # if pick up was already scheduled
                        foundPickUpScheduled = False
                        for pd in pdList:
                            if p[0] == pd[0] and pd[2] == "pickup":
                                foundPickUpScheduled = True
                        if foundPickUpScheduled:
                            candPoi.append(p)
                # pick up is always added
                else:
                    candPoi.append(p)
        return candPoi

    def getNextPoi(self, currentEdge, candPoi):
        ''' Find next POI from the set of candidate POI to be added to the route.
            The choice is performed based on the minimum distance from the previous POI already scheduled for the route.

            Returns next POI and its location (edge).
        '''
        nextPoi = candPoi[0]
        newCurrentEdge = candPoi[0][1]
        currentDistance = np.inf

        for cand in candPoi:
            distance = self.sumo.simulation.getDistanceRoad(currentEdge, 0, cand[1], 0, isDriving=True)   
            if distance < currentDistance:
                nextPoi = cand
                newCurrentEdge = cand[1]
                currentDistance = distance
        return nextPoi, newCurrentEdge

    def getPickUpDropOffList(self, taxi, currentCustomers, newCustomerRes, all_reservations):
        pickupDropoffList = []

        # resList contains indices of all the passengers assigned
        resList = [int(newCustomerRes)]
        currList = list(map(lambda x: x[1:], currentCustomers.split(" ")))
        resList.extend(currList)

        # print("reslist: ", resList)

        poi = []
        for res in resList:
            # find passenger reservation
            person = tuple(filter(lambda x: x.id == str(res), all_reservations))[0]
            fromEdge = person.fromEdge
            toEdge = person.toEdge
            wasPickup = True if int(person.state) == 8 else False
            # extend the sequence of pick-up and drop-off points
            poi.append((res, toEdge, "dropoff"))
            # for some reasons, there is an exception
            # when you try to skip pickup for already picked up person
            # in contrast to documentation
            poi.append((res, fromEdge, "pickup"))
        
        currentEdge = self.sumo.vehicle.getRoute(taxi)[0]

        scheduled = 0
        pdList = []

        # creating the route
        while scheduled < len(poi):
            candPoi = self.getCandPoi(poi, pdList)
            nextPoi, currentEdge = self.getNextPoi(currentEdge, candPoi)
            pdList.append(nextPoi)
            scheduled += 1

        for p in pdList:
            pickupDropoffList.append(str(p[0]))

        return pickupDropoffList

    def dispatch(
            self, 
            action: int = 1,
            ):
        ''' Assign the taxis to current pending requests
        '''

        all_reservations = self.sumo.person.getTaxiReservations(0)
        # returns the reservations that have not been assigned yet
        reservations = tuple(filter(lambda x: x.state!=4 and x.state!=8, all_reservations))
        # get all taxis
        taxis = self.sumo.vehicle.getTaxiFleet(-1)

        for person in reservations:
            # assign the taxi
            taxi = self.getTaxi(person, taxis, action)
            # if we cannot find a taxi, then we skip this passenger
            if (taxi == -1):
                # print("Cannot assign taxi for person")
                continue
            taxiState = int(self.sumo.vehicle.getParameter(taxi, "device.taxi.state"))
            currentCustomers = self.sumo.vehicle.getParameter(taxi, "device.taxi.currentCustomers")

            # for empty taxi
            if taxiState == 0:
                self.sumo.vehicle.dispatchTaxi(taxi, [person.id])
            # for non-empty taxi, we calculate sequence of pick-ups and drop-offs 
            # searching for the one giving the shortest path
            else:
                # print("taxiState: ", taxiState)
                pickupDropoffList = self.getPickUpDropOffList(taxi, currentCustomers, person.id, all_reservations)
                self.sumo.vehicle.dispatchTaxi(taxi, pickupDropoffList)
           

    # returns maximum values for observations, for setting parameter of gym space box
    def get_max_observations(self):
        # for test with a single state variable (non-served requests)
        return np.asarray([np.inf], dtype=np.float32)


    def get_observation(self):
        # get all reservations (including dispatched ones)
        reservations = self.sumo.person.getTaxiReservations(0)
         # get all reservations that have not been assigned to taxi
        non_served_reservations = tuple(filter(lambda x: x.state!=4 and x.state!=8, reservations))
        # non-served, thus, is a number of pending requests
        non_served = len(non_served_reservations)
        obs1 = np.array(non_served, dtype=np.float32)

        # return np.asarray([obs1, obs2])
        return np.asarray([obs1])

    def compute_reward(self):
        """Computes the reward of the ridepooling controller."""
        self.last_reward = self.reward_fn(self)
        return self.last_reward   

    def _emissions_nonserved_reward(self):
        step = self.sumo.simulation.getCurrentTime() / 1000
        
        # get all reservations (including dispatched ones)
        all_reservations = self.sumo.person.getTaxiReservations(0)
        # get all reservations that have not been assigned to taxi
        reservations = tuple(filter(lambda x: x.state!=4 and x.state!=8 and x.reservationTime != self.sumo.simulation.getTime(), all_reservations))
        empty_taxis = self.sumo.vehicle.getTaxiFleet(0)
        taxi_count = self.sumo.vehicle.getTaxiFleet(-1)
        occupied_taxis = len(taxi_count) - len(empty_taxis)
        non_served = len(reservations)
        # these coefficients are:
        # for non-served - the maximum number of unserved requests for simulation with fixed capacity = 1
        # for occupied taxis - the total number of taxis in the system (that is, the maximum number of occupied taxis)
        # in this way, we mix two targets with the same weights
        reward = round((non_served/11.0 - occupied_taxis/15.0) * (-10),2)

        return reward

    @classmethod
    def register_reward_fn(cls, fn: Callable):
        """Registers a reward function.

        Args:
            fn (Callable): The reward function to register.
        """
        if fn.__name__ in cls.reward_fns.keys():
            raise KeyError(f"Reward function {fn.__name__} already exists")

        cls.reward_fns[fn.__name__] = fn

    reward_fns = {
        "emissions-nonserved": _emissions_nonserved_reward,
    }