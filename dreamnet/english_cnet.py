"""Tools for interacting with ConceptNet in English and interpreting
the results. Translate between plain words and the ConceptNet format"""

import random

import requests
import pattern.en as en

def query(concept, rel, reverse=False, all_edges=False):
	"""Return the node(s) that are related to concept by rel"""
	direction = ('start', 'end') if not reverse else ('end', 'start')
	edges = requests.get("http://api.conceptnet.io/query?{}={}&rel=/r/{}" \
		"&limit=1000".format(direction[0], concept, rel)).json()['edges']

	if not len(edges): return []
	if not all_edges: return random.choice(edges)[direction[1]]
	return [x[direction[1]] for x in edges]

def isRich(concept, threshold=20):
	obj = requests.get('http://api.conceptnet.io{}'.format(concept)).json()
	return concept != "/c/en/" and len(obj.get('edges', [])) >= threshold

def attemptSingularization(term):
	"""Return the singular form of this term, unless the plural form
	has more edges connecting it to other nodes."""
	term_node = requests.get('http://api.conceptnet.io{}'.format(term)).json()
	richness = len(term_node.get('edges', []))

	singular = readableToTerm(en.singularize(termToReadable(term)))
	return singular if isRich(singular, threshold=richness) else term

def richness(concept):
	#print("Determining richness of: {}".format(concept))
	if concept == "/c/en/": return 0
	obj = requests.get('http://api.conceptnet.io{}'.format(concept)).json()
	return len(obj.get('edges', []))

def termToReadable(t):
	return t[6:].replace('_', ' ')

def readableToTerm(s):
	return "/c/en/" + s.replace(' ', '_')

def conjugateVerbs(sentence, tense):
	"""Use parse trees to identify the verbs in a phrase. Assume the
	first word in the phrase is guaranteed to be a verb. Return the
	phrase with each verb converted to the desired tense."""
	if not sentence: return None

	"""pattern-en's conjugation() often does not work, 
	but lexeme() generates conjugations in a predictable order"""
	lexeme_indicies = {"infinitive" : 0, "continuous" : 2}
	t = lexeme_indicies[tense.lower()]

	words = en.parsetree(sentence)[0]
	words[0].string = en.lexeme(words[0].string)[t]

	for word in words:
		if word.type[0] == "V":	
			word.string = en.lexeme(word.string)[t]

	return words.string

def findDirectObject(sentence):
	"""Return the direct object of the input verb phrase."""
	try:
		remainder = sentence[sentence.index(' ')+1:]
	except:
		return None

	"""Doesn't work for certain verbs, typically those that have another, 
	non-verb sense (e.g. 'ready' the weapon, 'storm' the hill). So we simply
	replace this difficult verb with a more easily understood one: 'see' """
	tree = en.parsetree('You see {}'.format(remainder), 
		tags=True, chunks=True, relations=True)
	rel = tree.sentences[0].relations
	obj_dict = rel["OBJ"]
	if len(obj_dict): 
		obj = next(iter(obj_dict.values())).head.string
		return readableToTerm(obj)

	for word in tree.sentences[0].words:
		if word.type[0] == 'N': return readableToTerm(word.string)
	return None

def correctSpelling(s):
	words = [en.suggest(w) for w in s.split()]
	return ' '.join(words)