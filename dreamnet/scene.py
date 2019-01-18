import random
import os

import requests
import pattern.en as en

from dreamnet.english_cnet import *

current_dir = os.path.dirname(__file__)
dream_ideas = open(os.path.join(current_dir, "nounlist.txt")).read().splitlines()

def locationItems(concept, min_weight=2, min_items=3):
	"""Return nodes strongly associated with being located at concept.
	   If not enough nodes can be found, return None"""
	edges = requests.get("http://api.conceptnet.io/query?end={}&" \
		"rel=/r/AtLocation&limit=1000".format(concept)).json()['edges']
	
	
	items = [x['start']['term'] for x in edges if x['weight'] >= min_weight]
	#only include items that actually let the user do something with them
	items = list(filter(lambda x: len(conceptOptions(x)) > 0, items))

	if len(items) < min_items: return None
	return random.sample(items, min_items)

def generateOptions(concept):
	"""Generate and print a list of ways the user can interact 
	with an item."""
	options = conceptOptions(concept)
	
	if not len(options):
		print("You can't think of anything to do with {}.".format(
			termToReadable(concept)))
		return None

	readable = termToReadable(concept)
	for opt_num, opt in enumerate(options, 1):
		opt['label'] = conjugateVerbs(opt['label'], "INFINITIVE")
		print('{}. Use {} to {}'.format(opt_num, readable, opt['label']))

	return options

def conceptOptions(concept):
	"""Query what the concept is capable of, required for, and used
	for, and return up to three random samples from the results."""
	allOptions = (query(concept, 'CapableOf', all_edges=True) +
			      query(concept, 'HasPrerequisite', all_edges=True, 
			      	reverse=True) +
			      query(concept, 'UsedFor', all_edges=True))

	return random.sample(allOptions, min(3, len(allOptions)))

def describeObject(concept, max_descriptions=4):
	query_messages = {"IsA" : "{} is a type of {}.",
					  "HasProperty" : "{} is {}.",
					  "HasA" : "{} has {}.",
					  "Desires" : "{} wants to {}.",
					  "NotDesires" : "{} doesn't want to {}.",
					  "PartOf" : "{} is part of {}.",
					  "CausesDesire" : "{} makes you want to {}.",
					  "RecievesAction" : "{} can be {}."}

	describeConcept(concept, query_messages)

def describeLocation(concept):
	query_messages = {"LocationOf" : "{} is located at {}.",
				      "HasA" : "{} has a {}.",
				      "IsA" : "{} is a type of {}."}

	describeConcept(concept, query_messages)

def describeConcept(concept, query_messages, max_descriptions=4):
	"""Accept a dict of relation names mapped to message templates.
	Query a few of these relations, printing the templates with 
	information about the concept."""
	readable = termToReadable(concept)
	default_description = "There's not much to say about {}.".format(readable)
	descriptions_given = 0

	for q, m in query_messages.items():
		if descriptions_given >= max_descriptions: break
		result = query(concept, q)
		if result: 
			print(m.format(readable, result['label']).capitalize(), end=" ")
			default_description = ""
			descriptions_given += 1

	print(default_description)

def optionByproducts(opt):
	"""Given a concept node that represents a verb phrase, figure out
	 what new items will be established in the scene after carrying out
	 that phrase. Print each item."""
	dirObj = findDirectObject(opt['label'])
	new_things = [dirObj] if dirObj else []
	
	effects = query(opt['term'], 'Causes')
	created = query(opt['term'], 'CreatedBy', reverse=True)
	if effects and conceptOptions(effects['term']): 
		new_things.append(effects['term'])
	if created and conceptOptions(created['term']): 
		new_things.append(created['term'])

	new_things = [attemptSingularization(t) for t in new_things]
	for t in new_things:
		print("There is now {} in the scene.".format(
			en.referenced(termToReadable(t))))
	return new_things

class Scene:
	def __init__(self, location="", items=set(), inventory=[]):
		self.location = location
		self.items = items
		self.inventory = inventory
		self.options = []

	def handleInput(self, inp):
		if not inp: return
		words = inp.lower().split()
		command = words[0]

		if command[0] == "\'":
			command = command.strip("\'")
			print("Don't actually type the quotation marks, silly.")

		if inp.startswith("the name of an object"): print("Very funny.")

		if self.options and command[0].isnumeric():
			self.selectOption(command)
		elif command == "look":
			self.look(words[1:])
			self.options = None
		elif command == "dream":
			self.dream(' '.join(words[1:]))
			self.options = None
		else:
			self.interact(inp)

	def interact(self, concept):
		"""Handle input that does not start with a special 
		command word like 'look', 'dream' or '2'."""

		asTerm = readableToTerm(concept)
		if asTerm not in self.items:
			if self.options:
				print("If you're trying to select an option," \
					" you just have to type '1' or '2' or '3'.")
				
			print("There is no {} here.".format(concept))
			print("Type 'help' to see the command formats.")
			return

		describeObject(asTerm)
		self.options = generateOptions(asTerm)

	def selectOption(self, opt_num):
		"""Print the consequences of the chosen course of action.
		Add any new items created by it to the scene."""
		try:
			n = int(opt_num)
			if n < 1 or n > 3: raise ValueError("Improper option index")
			opt = self.options[int(opt_num) - 1]
		except:
			print("Not a valid option.")
			return

		print('You {}.'.format(opt['label']))
		
		sub = query(opt['term'], 'HasSubevent')
		if sub: 
			print('As a result of {}, you {}.'.format(
			  conjugateVerbs(opt['label'], "continuous"), 	
			  conjugateVerbs(sub['label'], "infinitive")))

		self.items.update(optionByproducts(opt))

	def dream(self, concept):
		"""Create a new scene based off of the input concept."""
		new_items = []
		concept = attemptSingularization(readableToTerm(concept))
		
		potential_loc = concept
		while True:
			#see if this can be a location (contains enough associated items)
			new_items = locationItems(potential_loc, min_items=3)
			if new_items:
				self.location = potential_loc
				break

			#Conversely, this concept might be an item found within a location
			foundAt = query(potential_loc, "AtLocation")
			if foundAt: potential_loc = foundAt['term']
			#if concept is neither a location nor found at a good location,
			# just pick a random common word and repeat the process
			else: potential_loc = readableToTerm(random.choice(dream_ideas))

		if richness(concept) > 0 and self.location != concept: 
			new_items.append(concept)
		
		self.items = set([attemptSingularization(i) for i in new_items])
		self.lookAround()

	def look(self, words):
		"""Parse the input and call lookAround, or lookItem if the user
		specified an item to look at."""
		if not words: return self.lookAround()

		if words[0] == 'around' or words[0] == self.location:
			print("In the future, you can just say 'look'")
			return self.lookAround()

		if words[0] == 'at':
			print("""You don't need to say 'look at the item';
			 just 'look item' will work.""")
			words = words[2:] if words[1] == 'the' else words[1:]
		
		item = readableToTerm(' '.join(words))
		if item in self.items: 
			describeObject(item)
		else:
			print("There's no {} here.".format(termToReadable(item)))

	def lookAround(self):
		"""Print a description of the scene location, including a list
		of all the items it contains."""
		readable = termToReadable(self.location)
		print("You are in a {}.".format(readable), end=" ")

		describeLocation(self.location)

		item_names = [termToReadable(x) for x in self.items]
		print("There's {} in the {}.".format(en.quantify(item_names), readable))