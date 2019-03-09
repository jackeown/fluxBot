# -*- coding: utf-8 -*-
import random
# import gym
import numpy as np
from collections import deque
from keras.models import Sequential
from keras.layers import Dense
from keras.optimizers import Adam, SGD
from keras import backend as K

# EPISODES = 5000

# total number of actions: 2^5 * (360/45) * 2 + 32
nAngles = 8
actions = []
for r in [0,0.25,0.5]:
    thetas = [0]
    if r > 0:
        thetas = [i/nAngles for i in range(nAngles)]
    for theta in thetas:
        for a,b,l,y,z in [[1 if j==i else 0 for j in range(5)] for i in range(6)]:
            # the 6 above is so that we can have no buttons pressed.
            actions.append([r,theta,a,b,l,y,z])
        # for a in [0,1]:
        #     for b in [0,1]:
        #         for l in [0,1]:
        #             for y in [0,1]:
        #                 for z in [0,1]:
        #                     actions.append([r,theta,a,b,l,y,z])

class DQNAgent:
    def __init__(self, state_size, action_size):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = deque(maxlen = 1000000)
        self.gamma = 0.99  # discount rate
        self.epsilon = 1.0  # exploration rate
        self.epsilon_min = 0.1
        self.epsilon_decay = 0.99995 #99995 decays to 5% in about 24 hours.
        self.learning_rate = 0.0000001
        self.model = self._build_model()
        self.target_model = self._build_model()
        self.update_target_model()

    def _huber_loss(self, target, prediction):
        # sqrt(1+error^2)-1
        error = prediction - target
        return K.mean(K.sqrt(1+K.square(error))-1, axis=-1)

    def _build_model(self):
        # Neural Net for Deep-Q learning Model
        model = Sequential()
        model.add(Dense(100, input_dim=self.state_size + self.action_size, activation='relu'))
        model.add(Dense(100, activation='relu'))
        # model.add(Dense(100, activation='relu'))
        model.add(Dense(1, activation='linear'))
        model.compile(loss="mse",
                      optimizer=Adam(lr=self.learning_rate))
        return model

    def update_target_model(self):
        # copy weights from model to target_model
        self.target_model.set_weights(self.model.get_weights())

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state):
        if np.random.rand() <= self.epsilon:
            return random.choice(actions)
        act_values = self.model.predict(np.array([np.append(state, action) for action in actions]))
        return actions[np.argmax(act_values)]  # returns action

    def replay(self, batch_size):
        minibatch = random.sample(self.memory, batch_size)
        for state, action, reward, next_state, done in minibatch:
            # target = self.model.predict(state)
            if done:
                target = reward
            else:
                inVecs = np.array([np.append(next_state, [action], axis=1) for action in actions]).reshape((len(actions),-1))
                As = self.model.predict(inVecs)
                Ts = self.target_model.predict(inVecs)
                target = reward + self.gamma * Ts[np.argmax(As)]

            inVec = np.append(state, [action], axis=1)
            target = np.array([target])
            self.model.fit(inVec, target, epochs=1, verbose=1)
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def load(self, name):
        self.model.load_weights(name)

    def save(self, name):
        self.model.save_weights(name)

#
# if __name__ == "__main__":
#     env = gym.make('CartPole-v1')
#     state_size = env.observation_space.shape[0]
#     action_size = env.action_space.n
#     agent = DQNAgent(state_size, action_size)
#     # agent.load("./save/cartpole-ddqn.h5")
#     done = False
#     batch_size = 32
#
#     for e in range(EPISODES):
#         state = env.reset()
#         state = np.reshape(state, [1, state_size])
#         for time in range(500):
#             # env.render()
#             action = agent.act(state)
#             next_state, reward, done, _ = env.step(action)
#             reward = reward if not done else -10
#             next_state = np.reshape(next_state, [1, state_size])
#             agent.remember(state, action, reward, next_state, done)
#             state = next_state
#             if done:
#                 agent.update_target_model()
#                 print("episode: {}/{}, score: {}, e: {:.2}"
#                       .format(e, EPISODES, time, agent.epsilon))
#                 break
#         if len(agent.memory) > batch_size:
#             agent.replay(batch_size)
#         # if e % 10 == 0:
#         #     agent.save("./save/cartpole-ddqn.h5")
