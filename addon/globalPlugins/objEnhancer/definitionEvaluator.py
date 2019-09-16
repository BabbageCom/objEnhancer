# Object Enhancer

# Copyright (C) 2017 Babbage B.V.

# This file is covered by the GNU General Public License.
# See the file COPYING for more details.

import configobj
from NVDAObjects import NVDAObject
from logHandler import log
from operator import sub, attrgetter
from locationHelper import RectLTWH
from . import utils
from types import MethodType
from configobj import Section


def evaluateObjectAttributes(obj, definition, cache):
	if not isinstance(obj, NVDAObject):
		raise ValueError(f"Invalid NVDAObject specified: {obj!r}")
	input = definition.get('input', {})
	if not (isinstance(definition, Section) and input):
		raise ValueError(f"Invalid definition spesification provided: {definition}")
	options = definition.get('options', {})
	functions = definition.get('functions', {})
	for attr, possibleVals in input.items():
		params = functions.get(attr, {})
		tupleParams = tuple(params.items())
		val = cache.get((attr, tupleParams))
		if not val:
			try:
				# Use attrgetter to support fetching attributes on children
				try:
					val = attrgetter(attr)(obj)
				except AttributeError:
					func = vars(utils).get(attr)
					if not callable(func):
						raise
					val = MethodType(func, obj)
				if not callable(val) and params:
					raise TypeError("Function definition missmatch")
				elif callable(val):
					val = val(**params)
			except Exception:
				handleErrors = options['handleDefinitionErrors']
				if handleErrors == "raise":
					raise
				else:
					log.exception(f"Error while handling objEnhancer definition {definition}")
					if handleErrors == "break":
						break
					elif handleErrors == "ignore":
						continue
			cache[(attr, tupleParams)] = val
		if val in possibleVals:
			continue
		elif not options.get('absoluteLocations', True) and attr == 'location':
			for expectedVal in possibleVals:
				relativeLocation = RectLTWH(*map(sub, expectedVal, val))
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
	name = definition.name[0].upper() + definition.name[1:]
	output = definition.get('output', {})
	if not (isinstance(definition, Section) and output):
		raise ValueError(f"Invalid definition specification provided: {definition}")
	output = output.dict()
	output['_objEnhancerDefinition'] = definition
	return type(
		"{}ObjEnhancerOverlay".format(name),
		(ObjEnhancerOverlay,),
		output
		)


def findMatchingDefinitionsForObj(obj, definitions, objCache):
	if not isinstance(definitions, configobj.ConfigObj):
		raise ValueError(f"Invalid spesification provided: {definitions}")
	for name, definition in definitions.items():
		if definition['isAbstract']:
			continue
		parent = definition["parent"]
		if parent:
			try:
				parentDef = definitions[parent]
			except KeyError:
				log.error(f"Definition {name} refered to unknown parent {parent}")
				continue
			if not evaluateObjectAttributes(obj, parentDef, objCache):
				return None
		if evaluateObjectAttributes(obj, definition, objCache):
			return definition
	return None

def getObjectVars(obj, inputAttributes):
	for attr in inputAttributes:
		try:
			val = getattr(obj, attr)
		except Exception:
			func = vars(utils).get(attr)
			if not callable(func):
				log.exception(f"Couldn't get {attr} from {obj!r}")
				continue
			try:
				val = MethodType(func, obj)()
			except Exception:
				log.exception(f"Couldn't get value for utility function {attr} from {obj!r}")
				continue
		yield (attr, val)
