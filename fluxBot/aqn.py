import torch
import torch.nn as nn

from collections import Iterable, deque

class AQN:
    def __init__(self, stateSize, actionSize):
        self.stateSize = stateSize
        self.actionSize = actionSize
        self.memory = deque(maxlen = 1000000)

        self.learningRate = 0.001

        self.gamma = 0.1 # discount factor
        self.gammaIncreaseRate = 0.02
        self.gammaMax = 0.99

        self.epsilon = 0.5 # exploration rate
        self.epsilonDecayRate = 0.99
        self.epsilonMin = 0.05

        self.model = self._build_model()

    def _buildModel(self):
        """ Builds the pytorch model so the 'act' and 'replay' functions can use it. """

        # TODO




    def remember(self, experience):
        """ Stores a 5-tuple of (state,action,reward,nextState,doneBool) in memory"""
        # sanity check on input:
        if not isinstance(experience, Iterable) or len(experience) != 5:
            raise Exception("AQN remember function should take a 5-tuple as input!")
        else:
            self.memory.append(experience)






    def act(self, state):
        """ Selects an action for the agent to perform.
            (Computes the max over forward passes of our Q function estimator.)"""
        pass
        # TODO


    def replay(self, batchSize):
        """ Learns from memory by adjusting our Q function estimator
            to accurately reflect past experience."""
        pass
        # TODO
