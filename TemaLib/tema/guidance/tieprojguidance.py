# Tieproj guidance written for OHJ-2900 by Timo Pitkänen
# Copyright (c) 2006-2010 Tampere University of Technology
# 
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# tema libraries:
from tema.guidance.guidance import Guidance as GuidanceBase
# python libraries:
import random
import time 
import threading
import copy
from sets import Set

version='0.1'

# The search algorithm constructs a tree using this Node class
class Node:
	def __init__(self, parent):
	
		#maximum points found from this node or its children 
		self.maxPoints = 0.0
		
		# parent node
		self.parent = parent
		
		#children nodes
		self.children = []
		
		# contains indices to all node's children with the max score
		self.nextStep = []

class Guidance(GuidanceBase):

	def __init__(self):
		GuidanceBase.__init__(self)

		self.began = 0

		# initializes the random number generator
		random.seed()
		
		# a list of suggestions
		# seach method appends a suggestion every time it makes a decision
		# about next chosen transition, and suggestAction pops suggestions
		# from the beginning of it. 
		self.suggestions = []
		
		# tells how many keywords there are in the suggestions list
		self.keywordsInSuggestions = 0
				
		# the lock is acquired before accessing the variables shared by
		# suggestAction and searcher threads
		self.lock = threading.Lock()
		
		# the suggestion event signals for a new suggestion added to the suggestions list
		self.suggestionEvent = threading.Event()
		
		# the state event signals for a new root state for search thread to start searching
		# next suggestions (search waits for this after a verification action)
		self.stateEvent = threading.Event()
		
		# is suggestAction waiting for suggestion?
		self.waitingForSuggestion = 0
		
		# is searcher thread waiting for verification?
		self.waitingForVerification = 0
		
		# The estimated delay after a keyword execution, is updated by suggestAction.
		self.keywordDelay = 0.1


	# searchs for optimal suggestions and appends them to the suggestions list
	def search(self):	
	
		# deep copies requirements
		requirements = copy.deepcopy(self._requirements)
		
		# a set of executed transitions - non executed transitions will be favored
		# by the decision maker
		executedTransitions = Set()
		
		# a set of transitions which the searcher won't take into account when 
		# searching paths. Maybe a bad idea for real testing situations, but I added 
		# this so the search wouldn't get stuck in verification transitions which never 
		# get executed anyway. 
		bannedTransitions = Set()
						
		# root state and node where the search begin 
		rootState = self.newRootState
		rootNode = Node(0)
		
		# maximum depth of a search
		maxDepth = 25
		
		# an array for storing number of transitions of each level during the search	
		curSequences = [0] * maxDepth		
		numOfTransitions = [0] * maxDepth
						
		# an array for storing the index of where search is at the moment
		curSequenceInds = [0] * maxDepth
		
		# an array for storing current states of each level during the search
		curStates = [0] * ( maxDepth + 1 )
		
		# an array for storing transition arrays during the search
		curTransitions = [0] * ( maxDepth + 1 )

		suggestion = 0
		
		# these estimations are updated during searches

		# an estimated time to search before the suggestions list is empty and 
		# a new suggestion is needed				
		timeToSearch = 0.0
		
		# an estimated time for going through one level of transitions
		level1SearchTime = 0.1
		
		# an estimated branching factor for the model graph, 
		branchingFactor = 3.5
			
		# search for new suggestions forever
		while 1:
			
			# search a path?
			searchPath = 1
			
			# continue searching from a (possibly) preexisting path?
			continuePathSearch = 0
			
			# transitions from the root state
			rootTransitions = rootState.getOutTransitions()
			
			# updates the branching factor slowly							
			branchingFactor = 0.997 * branchingFactor + 0.003 * len(rootTransitions)
			
			# are the root transitions keywords?
			isKeyword = rootTransitions[0].getAction().isKeyword()
			
			# no selected suggestion so far
			suggestion = -1
						
			if len(rootTransitions) == 1:
				# only one transition, no search needed
				searchPath = 0
				suggestion = 0
			
			# a keyword?
			elif isKeyword:
				
				# the suggestion doesn't matter so the first one is selected, and
				# the searcher has to wait for verification								
				suggestion = 0
				self.waitingForVerification = 1
			
				# acquires the lock and appends the suggestion to the list
				self.lock.acquire()				 			
				self.suggestions.append(suggestion)
				self.keywordsInSuggestions += 1
				
				# estimates is there enough time to search at least two levels deep
				
				# time to search is the number of keywords in the suggestion list multiplied by the keyword delay 
				# minus time since last suggestAction call		
				timeToSearch = self.keywordsInSuggestions * self.keywordDelay - time.time() + self.lastSuggestActionCallTime
							
				# signals that there's a new suggestion and releases the lock  
				self.suggestionEvent.set()
				self.lock.release()
				
				# time to search is divided by the number of first level transitions so the 
				# estimation would be more accurate				
				timeToSearch /= len(rootTransitions)
				
				# is there less time than it would take to search through two levels?
				if timeToSearch < level1SearchTime * branchingFactor:
					# doesn't search
					searchPath = 0		
				else:
					# continues searching from a (possibly) preexisting path
					continuePathSearch = 1		
					
			# root node has next steps?
			elif len(rootNode.nextStep) > 0:
				# continues previously searched path
				searchPath = 0	
												
			if searchPath:
				# a new path will be searched
				
				# at first, the deepness of the search is decided by estimating the available time 
				# and the time it would take to search through different amounts of levels		
					
				self.lock.acquire()
								
				# time to search is the number of keywords in the suggestion list multiplied by the keyword delay 
				# minus time since last suggestAction call
				timeSinceLastCall = time.time() - self.lastSuggestActionCallTime
				timeToSearch = self.keywordsInSuggestions * self.keywordDelay - timeSinceLastCall
				
				self.lock.release()
				
				# time to search is divided by the number of first level transitions so the 
				# estimation would be more accurate
				timeToSearch /= len(rootTransitions)
						
				# search depth				
				searchDepth = 1
				searchTime = level1SearchTime
				
				# raises the depth for as long as there seems to be enough time for more levels
				while timeToSearch > searchTime * branchingFactor and searchDepth < maxDepth:
					searchTime *= branchingFactor
					searchDepth += 1
					
				self.log("Keywordeja jonossa: %s" %self.keywordsInSuggestions)
				self.log("Aikaa käytettävissä: %s" %timeToSearch)
				self.log("Keyword delay: %s" %self.keywordDelay)
				self.log("Branching factor: %s" %branchingFactor)
				self.log("Aikaa edellisestä suggestActionista %s" %timeSinceLastCall)
				self.log("Valittu syvyys: %s" %searchDepth)
					
				# time before the search
				timeBefore = time.time()		
										
				numOfTransitions[0] = len(rootTransitions)
				curSequenceInds[0] = 0
				
				randomSequence = range(len(rootTransitions))
				random.shuffle(randomSequence)
				curSequences[0] = randomSequence
				
				curStates[0] = rootState
				curTransitions[0] = rootTransitions
				
				# if root node has no children, create them
				if len(rootNode.children) == 0:
					for i in range(len(rootTransitions)):
						rootNode.children.append(Node(rootNode))
											
				# current node and depth
				curNode = rootNode
				depth = 0
				
				while 1:
					# if suggestAction is already waiting for a suggestion,
					# search depth becomes 1
					if self.waitingForSuggestion:
						self.log("Lopetetaan etsintä kesken")
						self.waitingForSuggestion = 0
						searchDepth = 1
											
					# goes a step deeper if possible
					if depth < searchDepth and curSequenceInds[depth] < numOfTransitions[depth]:
					
						# transitions from the current state
						transitions = curStates[depth].getOutTransitions()
						
						# current transition index 
						transInd = curSequences[depth][curSequenceInds[depth]]
						
						# the selected transition
						trans = transitions[transInd]
						
						# ignores banned transitions
						if id(trans) in bannedTransitions:
							curSequenceInds[depth] += 1
						else:
			
							# the node where the transition leads
							curNode = curNode.children[transInd]
												
							# raises the depth	
							depth += 1
							
							# sets the current state of the depth the search went to
							curStates[depth] = trans.getDestState()
							
							# number of transitions from the state the search went to
							numOfTrans = len(curStates[depth].getOutTransitions())	
							
							# updates the branching factor slowly							
							branchingFactor = 0.997 * branchingFactor + 0.003 * numOfTrans
							
							# marks the transition executed
							for covObj in requirements:
								covObj.push()
								covObj.markExecuted(trans)
							
							# the deepest level of the search?		
							if depth == searchDepth:
								
								# calculates the points of the path and stores
								# them to node's maxPoints
								curNode.maxPoints = 0.0													
								for covObj in requirements:
									curNode.maxPoints += covObj.getPercentage()
									
							# more levels left
							else:

								# updates the number of transitions in this level and 
								# current transition index of this level
								numOfTransitions[depth] = numOfTrans
								curSequenceInds[depth] = 0
								
								randomSequence = range(numOfTrans)
								random.shuffle(randomSequence)
								curSequences[depth] = randomSequence
								
								# creates children nodes if this node doesn't have them yet
								if len(curNode.children) == 0:
									for i in range(numOfTrans):
										curNode.children.append(Node(curNode))								
					
					# goes back one step	
					else:
						# the end of search when the search retuns back to root level					
						if depth == 0:
							break
							
						depth -= 1
						parent = curNode.parent
						
						curTransitionInd = curSequences[depth][curSequenceInds[depth]]

					    # the child has higher score than its parent?												
						if curNode.maxPoints > parent.maxPoints:
							# the child becomes the only possible choice in nextStep
							parent.nextStep = [curTransitionInd]
							
							# updates max points of the parent 
							parent.maxPoints = curNode.maxPoints
							
						# the child has equal score as its parent?
						elif curNode.maxPoints == parent.maxPoints:
							# the child is appended to the nextStep list
							
							# makes sure that no child is appended many times
							# (would be possible when the search continues from preexisting path)
							if continuePathSearch == 0 or len(parent.nextStep) == 0 or parent.nextStep[-1] < curTransitionInd:
								parent.nextStep.append(curTransitionInd)
														
						curNode = parent
						
						# goes to the next transition
						curSequenceInds[depth] += 1
						
						# pops marked executions
						for covObj in requirements:
							covObj.pop()
							
				# search is over
				
				# measures the time it took to search the path
				timeAfter = time.time()
				searchTime = timeAfter - timeBefore
				
				# the search time is divided by the number of first level transitions so the 
				# estimation would be more accurate
				searchTime /= len(rootTransitions)
				
				# updates search time of level 1 according to this search time
				
				for i in range(searchDepth - 1):
					searchTime /= branchingFactor
	
				level1SearchTime = level1SearchTime * 0.9 + searchTime * 0.1
													
			# no suggestion selected yet?
			if suggestion == -1:
				
				# randomly choses one of the equal choices for the next step
							
				maxPoints = 0.0
												
				random.shuffle(rootNode.nextStep)
				
				suggestionSelected = 0
									
				# randomly selects any transition that has not been executed before
				for i in rootNode.nextStep:
					if id(rootTransitions[i]) not in executedTransitions:
						suggestion = i
						suggestionSelected = 1
						break

				# if all transitions were executed before, just randomly selects 
				# one of them
				if suggestionSelected == 0:
					suggestion = random.choice(rootNode.nextStep)		
						
			# wait for verification?					
			if self.waitingForVerification == 1:
								
				# waits for the state event
				self.stateEvent.wait()
				self.stateEvent.clear()
				self.waitingForVerification = 0
				
				# the new root state has been put to self.newRootState				
				rootState = self.newRootState
							
				# finds out which transition is the right one
				for i in range(len(rootTransitions)):
				
					# the right transition leads to the new root state
					if rootTransitions[i].getDestState() == rootState:
						
						# marks the transition executed				
						for covObj in requirements:
							covObj.markExecuted(rootTransitions[i])
						
						suggestion = i
					else:
						# bans all other transitions, these can't be reached
						bannedTransitions.add(id(rootTransitions[i]))	
		
			else:	
				# acquires the lock
				self.lock.acquire()	
			 			
			 	# appends the suggestion to the list
				self.suggestions.append(suggestion)
				
				if isKeyword:
					self.keywordsInSuggestions += 1
				
				self.log("Uusi suggestio annettu")
				
				# signals that there's a new suggestion and releases the lock 
				self.suggestionEvent.set()
				self.lock.release()
				
				time.sleep(0.01)
						
				# transition that will be executed
				trans = rootTransitions[suggestion]
				
				# adds the transition to the executed transitions set
				executedTransitions.add(id(rootTransitions[suggestion]))
				
				# marks the transition executed
				for covObj in requirements:
					covObj.markExecuted(trans)
						
				# a new root state for the next search						
				rootState = trans.getDestState()
			
			#moves to the next node				
					
			if len(rootNode.children) == 0:
				# no children, nulls rootNode
				rootNode.maxPoints = 0.0
				rootNode.nextStep = []
			else:
				# rootNode becomes one of its children
				rootNode = rootNode.children[suggestion]

			rootNode.parent = 0
						

	def suggestAction(self, state):
	
		# first call?
		if self.began == 0:
			self.began = 1
			
			# time
			self.oldTime = time.time()
			self.updateKeywordDelay = 0
			self.lastSuggestActionCallTime = self.oldTime
						
			# starts the searcher thread which finds optimal actions
			# for this function to suggest
			
			# the state where the searcher begins		
			self.newRootState = state
			
			# starts the searcher thread
			searcher = threading.Thread(target = self.search)
			searcher.start()
	
		if self.waitingForVerification == 1 and len(self.suggestions) == 0:
			# if searcher is waiting for verification, 
			# tell the new state to it and wake it up
			self.newRootState = state
			self.stateEvent.set()
		
		# time
		newTime = time.time()
		
		if self.updateKeywordDelay: 	
			# calculates the time between this and the last suggestAction call, 
			# and updates keywordDelay 
			
			timeDif = newTime - self.oldTime 
								
			self.keywordDelay = self.keywordDelay * 0.9 + timeDif * 0.1
					
		# acquires the lock 		
		self.lock.acquire()
				
		self.lastSuggestActionCallTime = newTime
	
		# if there's no more suggestions left, wait until there is
		if len(self.suggestions) == 0:	
		
			self.waitingForSuggestion = 1
		
			self.log("SuggestAction odottaa")

			# clears the event		
			self.suggestionEvent.clear()		
					
			# releases the lock
			self.lock.release()
			
			# waits for the event which tells that there's a new suggestion
			self.suggestionEvent.wait()
			
			self.log("SuggestAction lopetti odotuksen")
						
			# after waking up, the lock is acquired again
			self.lock.acquire()
	
		# pops the first suggestion
		transInd = self.suggestions.pop(0)
		
		# the action that will be suggested
		action = state.getOutTransitions()[transInd].getAction()
		
		# is action a keyword?
		if action.isKeyword():
			# now there's one less key word in the suggestions list
			self.keywordsInSuggestions -= 1
			
			# the keyword delay will be updated next time suggestAction is called
			self.updateKeywordDelay = 1
			self.oldTime = time.time()
		else:
			self.updateKeywordDelay = 0
				
		# releases the lock
		self.lock.release()
		
		# returns the action related to the suggestion
		return action
