from . import ddqn as dqn
import melee
from melee import enums
import random, os
import numpy as np
import pandas as pd
import itertools
import math

def makeSureFolderExists(folder):
	try:
	    os.makedirs(folder)
	except FileExistsError:
	    # directory already exists
	    pass


class AI:
	def __init__(self, stateDim = 34, actionDim = 7, loadAndSave = False, nExpFiles = 100, train=False):
		self.train = train
		self.nExpFiles = nExpFiles
		self.loadAndSave = loadAndSave
		self.movesMade = 0
		self.stateDim = stateDim
		self.actionDim = actionDim
		self.dqn = dqn.DQNAgent(stateDim, actionDim)
		self.dqn.epsilon = 1.0
		self.prevState = None

		if self.loadAndSave:
			try:
				self.dqn.load("dqn.model")
				print("Loaded model!")
			except:
				print("Failed to load model!")
		else:
			print("opted not to load or save")


	def ctrlToAction(self,ctrl):
		action = []
		action.extend(ctrl.main_stick)
		action.append(ctrl.button[enums.Button.BUTTON_A])
		action.append(ctrl.button[enums.Button.BUTTON_B])
		action.append(ctrl.button[enums.Button.BUTTON_L])
		action.append(ctrl.button[enums.Button.BUTTON_Y])
		action.append(ctrl.button[enums.Button.BUTTON_Z])
		return np.array(action)

	def ctrlFromAction(self,action):
		ctrl = melee.controller.ControllerState()
		ctrl.main_stick = (action[0], action[1])
		ctrl.button[enums.Button.BUTTON_A] = action[2]
		ctrl.button[enums.Button.BUTTON_B] = action[3]
		ctrl.button[enums.Button.BUTTON_L] = action[4]
		ctrl.button[enums.Button.BUTTON_Y] = action[5]
		ctrl.button[enums.Button.BUTTON_Z] = action[6]
		ctrl.l_shoulder = int(ctrl.button[enums.Button.BUTTON_L])
		return ctrl

	def performAction(self,action,controller):
		ctrl = self.ctrlFromAction(action)
		controller.empty_input()

		controller.tilt_analog(enums.Button.BUTTON_MAIN,ctrl.main_stick[0],ctrl.main_stick[1])

		if ctrl.button[enums.Button.BUTTON_B]:
			controller.press_button(enums.Button.BUTTON_B)
		if ctrl.button[enums.Button.BUTTON_A]:
			controller.press_button(enums.Button.BUTTON_A)
		if ctrl.button[enums.Button.BUTTON_Y]:
			controller.press_button(enums.Button.BUTTON_Y)

		if ctrl.button[enums.Button.BUTTON_L]:
			controller.press_button(enums.Button.BUTTON_L)
			# controller.press_shoulder(enums.Button.BUTTON_L,0.0)
		else:
			controller.release_button(enums.Button.BUTTON_L)
			# controller.press_shoulder(enums.Button.BUTTON_L,0.0)

		if ctrl.button[enums.Button.BUTTON_Z]:
			controller.press_button(enums.Button.BUTTON_Z)

		#controller.release_button(enums.Button.BUTTON_R)
		#controller.press_shoulder(enums.Button.BUTTON_R,-1.0)


	def calculateReward(self,prevState,curState):
		reward = 0

		# Change in Stock number
		reward += ((curState[5] - prevState[5]) - (curState[21] - prevState[21]))

		# Change in Percentage
		reward += (max(curState[20] - prevState[20],0) - max(curState[4] - prevState[4],0))/200
		return reward

	def done(self,curState):
		# if either player has 0 stocks, then Game Over, else the game is on!
		done = ((curState[5] == 0) or (curState[21] == 0))
		return done

	def transformState(self,inState,ai_number):
		state = list(tuple(inState))
		if ai_number == 1:
			for i in range(2,18):
				tmp = state[i]
				state[i] = state[i+16]
				state[i+16] = tmp

		state = np.array(state).round(decimals=8) # is this bad?

		# scale down certain aspects of state
		# for "normalization" purposes of learning.
		state[2] *= 0.05
		state[3] *= 0.05
		state[2+16] *= 0.05
		state[3+16] *= 0.05

		return state


	def makeMove(self, gamestate, controller, ai_number=1):
		gamestate = gamestate.tolist()
		curState = self.transformState(gamestate, ai_number)
		done = self.done(curState)

		if self.prevState != None:
			prevState = self.transformState(self.prevState,ai_number)

		# Poll Network for Action
		action = self.dqn.act(curState.reshape(1,-1))
		if not done:
			self.performAction(action,controller)
			self.movesMade += 1



		# Update Network
		# movesMade > 100 check is to give stock counts time to be initialized
		if (self.prevState != None) and (self.movesMade > 100):
			reward = self.calculateReward(prevState,curState)
			if reward != 0:
				print("Reward for ai_number {}: {}".format(ai_number,reward))
				print("DQN epsilon: {}".format(self.dqn.epsilon))
				print([layer.input_shape for layer in self.dqn.model.layers])

			if done and ai_number == 2:
				print("Done!")
				# salty runback
				controller.press_button(enums.Button.BUTTON_A)
				controller.press_button(enums.Button.BUTTON_B)
				self.prevState = None
				self.movesMade = 0
				return

			prevAction = self.ctrlToAction(controller.prev)
			self.dqn.remember(prevState.reshape(1,-1),prevAction,reward,curState.reshape(1,-1),int(done))
			if self.movesMade % 100 == 0:
				print("saving experience and loading newest model")
				data = [self.dqn.memory[i] for i in range(0,-100,-1)]
				df = pd.DataFrame(data)

				csvFile = "experiences/exp{}.csv".format(random.randint(1,self.nExpFiles))
				makeSureFolderExists("experiences")
				df.to_csv(csvFile,mode='a',header=False,index=False)
				try:
					self.dqn.load("dqn.model")
				except:
					print("failed to load model!")
			if self.train:
				batch_size = 100
				frequency = 60
				if len(self.dqn.memory) > batch_size and self.movesMade % frequency == 0:
					print("replay!")
					self.dqn.replay(batch_size = batch_size)
					if self.loadAndSave:
						self.dqn.save("dqn.model")

		# prevState Update
		if (ai_number == 2) and (done == False):
			self.prevState = gamestate




	def sendExperienceToLearner(ip,port,exp):
		"""Sends a vector of (state,action,reward) 
		3-tuples to the "learner server
		"""
		pass

	def retrieveParametersFromLearner(ip, port):
		"""Makes a request to a 'learner server' to get the latest parameters
		for the policy."""
		pass