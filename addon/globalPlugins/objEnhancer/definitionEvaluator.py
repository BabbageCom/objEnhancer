# Object Enhancer

#Copyright (C) 2017 Babbage B.V.

#This file is covered by the GNU General Public License.
#See the file COPYING for more details.

import configobj
from baseObject import AutoPropertyObject
from NVDAObjects import NVDAObject
from logHandler import log
from operator import sub, attrgetter
import itertools
from locationHelper import RectLTWH
from configobj import Section
from . import utils
from types import MethodType

def evaluateObjAttrs(obj,definition, cache):
	if not isinstance(obj,NVDAObject):
		raise ValueError("Invalid NVDAObject definitionified: %s"%obj)
	input=definition.get('input',{})
	if not (isinstance(definition, Section) and input):
		raise ValueError("Invalid definition spesification provided: %s"%definition)
	options=definition.get('options',{})
	functions=definition.get('functions',{})
	for attr, possibleVals in input.items():
		params = functions.get(attr)
		val = cache.get((attr, params))
		if not val:
			try:
				# Use attrgetter to support fetching attributes on children
				try:
					val = attrgetter(attr)(obj)
				except AtributeError:
					func = vars(utils).get(attr)
					if not callable(func):
						raise
					val = MethodType(func, obj)
				if (callable(val) and not params) or (not callable(val) and params):
					raise TypeError("Function definition missmatch")
				if callable(val):
					val = val(**params)
			except:
				handleErrors = options['handleDefinitionErrors']
				if handleErrors == "raise":
					raise
				elif handleErrors == "break":
					break
				elif handleErrors == "ignore":
					continue
		if val in possibleVals:
			continue
		elif not options.get('absoluteLocations',True) and attr=='location':
			for val in possibleVals:
				relativeLocation = RectLTWH(*map(sub,expectedVal,val))
				if relativeLocation.topLeft == relativeLocation.bottomRight:
					break
			else:
				break
		else:
			break
	else:
		return True
	return False

class ObjEnhancerOverlay(NVDAObject):
	pass

def getOverlayClassForDefinition(definition):
	output=definition.get('output',{})
	if not (isinstance(definition, Section) and output):
		raise ValueError("Invalid definition specification provided: %s"%definition)
	output = output.dict()
	output['_objEnhancerDefinition'] = definition
	return type(
		"{}{}ObjEnhancerOverlay".format(definition.name[0].upper(), definition.name[1:]),
		(ObjEnhancerOverlay,),
		output
	)

def findMatchingDefinitionsForObj(obj,definitions):
	if not isinstance(definitions,configobj.ConfigObj):
		raise ValueError("Invalid spesification provided: %s"%definitions)
	objCache = {}
	for definition in definitions.values():
		if evaluateObjAttrs(obj,definition, objCache):
			return definition
	return None
