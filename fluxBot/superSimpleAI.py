
from fluxBot import ddqn as dqn
import melee
from melee import enums
import random
import numpy as np
import pandas as pd
import itertools


class AI:
	def __init__(self, state_size = 1, action_size = 2, loadAndSave = False, nExpFiles = 100, train = False):
		self.train = train
		self.nExpFiles = nExpFiles
		self.loadAndSave = loadAndSave
		self.movesMade = 0
		self.state_size = state_size
		self.action_size = action_size
		self.dqn = dqn.DQNAgent(state_size, action_size)
		self.dqn.gamma = 0.99
		self.dqn.epsilon = 0.01
		self.prevState = None

		self.stickLocations = []
		# self.stickLocations.extend([(x,1.0) for x in [0.5,]])
		# self.stickLocations.extend([(x,0.75) for x in [0.25,0.5,0.75]])
		self.stickLocations.extend([(x,0.5) for x in [0,1.0]])
		# self.stickLocations.extend([(x,0.25) for x in [0.25,0.5,0.75]])
		# self.stickLocations.extend([(x,0.0) for x in [0.5]])

		if self.loadAndSave:
			try:
				self.dqn.load("dqn.model")
				print("Loaded model!")
			except:
				print("Failed to load model!")
		else:
			print("opted not to load or save")



	def ctrlToAction(self,ctrl):
		n = 0
		n += self.stickLocations.index(ctrl.main_stick)
		# n += ctrl.button[enums.Button.BUTTON_B]*16
		# n += ctrl.button[enums.Button.BUTTON_A]*1
		# n += ctrl.button[enums.Button.BUTTON_Y]*2
		# n += ctrl.button[enums.Button.BUTTON_L]*3
		# n += ctrl.button[enums.Button.BUTTON_Z]*4
		return n


	def ctrlFromAction(self,n):
		ctrl = melee.controller.ControllerState()
		ctrl.main_stick = self.stickLocations[n]
		# buttons = [enums.Button.BUTTON_B, enums.Button.BUTTON_A, enums.Button.BUTTON_Y, enums.Button.BUTTON_L, enums.Button.BUTTON_Z]
		# ctrl.button[buttons[n % 5]] = True
		# ctrl.l_shoulder = int(ctrl.button[enums.Button.BUTTON_L])

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
			controller.press_shoulder(enums.Button.BUTTON_L,1.0)
		else:
			controller.release_button(enums.Button.BUTTON_L)
			controller.press_shoulder(enums.Button.BUTTON_L,-1.0)

		if ctrl.button[enums.Button.BUTTON_Z]:
			controller.press_button(enums.Button.BUTTON_Z)


	def calculateReward(self,prevState,curState):
		reward = 0

		# Change in Stock number
		reward += ((curState[5] - prevState[5]) - (curState[21] - prevState[21]))*100

		# Change in Percentage
		#reward += (max(curState[20] - prevState[20],0) - max(curState[4] - prevState[4],0))

		return reward

	def done(self,curState):
		# if either player has 0 stocks, then Game Over, else the game is on!
		done = ((curState[5] == 0) or (curState[21] == 0))
		return done

	def transformState(self,inState,ai_number):
		state = list(tuple(inState))
		if ai_number == 2:
			state = list(np.array(state).round(decimals=4))
		else:
			for i in range(2,18):
				tmp = state[i]
				state[i] = state[i+16]
				state[i+16] = tmp

			state = list(np.array(state).round(decimals=4))
		return state

	def makeMove(self,gamestate,controller,ai_number=1):
		gamestate = gamestate.tolist()
		curState = self.transformState(gamestate,ai_number)
		done = self.done(curState)

		if self.prevState != None:
			prevState = self.transformState(self.prevState,ai_number)

		# Poll Network for Action
		action = self.dqn.act(np.array([[curState[2]*0.05]]))
		self.performAction(action,controller)
		self.movesMade += 1


		# update target network for ddqn
		if self.movesMade % 500 == 0:
			self.dqn.update_target_model()



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
				self.prevState = None
				self.movesMade = 0

			prevAction = self.ctrlToAction(controller.prev)
			self.dqn.remember(np.array([prevState[2]*0.05]),prevAction,reward,np.array([curState[2]*0.05]),int(done))
			if self.movesMade % 100 == 0:
				print("saving experience and loading newest model")
				data = [self.dqn.memory[i] for i in range(0,-100,-1)]
				df = pd.DataFrame(data)

				csvFile = "experiences_superSimple/exp{}.csv".format(random.randint(1,self.nExpFiles))
				df.to_csv(csvFile,mode='a',header=False,index=False)
				try:
					self.dqn.load("dqn.model")
				except:
					print("failed to load model!")
			if self.train:
				batch_size = 100
				frequency = 60
				if len(self.dqn.memory) > batch_size and self.movesMade % frequency == 0:
					self.dqn.replay(batch_size = batch_size)
					if self.loadAndSave:
						self.dqn.save("dqn.model")

		# prevState Update
		if (ai_number == 2) and (done == False):
			self.prevState = gamestate
