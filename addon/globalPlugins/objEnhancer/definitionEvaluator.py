# Object Enhancer

# Copyright (C) 2021 Babbage B.V.

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
import api

def evaluateObjectAttributes(obj, definition, cache):
	if not isinstance(obj, NVDAObject):
		raise ValueError("Invalid NVDAObject specified: {obj!r}".format(obj=obj))
	input = definition.get('input', {})
	if not (( isinstance(definition, Section) or isinstance(definition, dict)) and input):
		raise ValueError("Invalid definition spesification provided: {definition}".format(definition=definition))
	functions = definition.get('functions', {})

	for attr, possibleVals in input.items():
		if attr == 'fg':
			#this is a dummy attribute that is added to give an overview when looking at the definition.
			continue
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
				handleErrors = definition['handleDefinitionErrors']
				if handleErrors == "raise":
					raise
				else:
					log.exception("Error while handling objEnhancer definition {definition}".format(definition=definition))
					if handleErrors == "break":
						break
					elif handleErrors == "continue":
						continue
			cache[(attr, tupleParams)] = val

		if val in possibleVals:
			continue

		elif attr == 'location' and definition.get("fgDependendLocation", False):
			# in this case we check for the relative location compared to the foreground object
			fgLocation = api.getForegroundObject().location
			objLocation = obj.location
			relativeLocation = (objLocation.left - fgLocation.left, objLocation.top - fgLocation.top, objLocation.height, objLocation.width)
			if relativeLocation in possibleVals:
				log.info("good enough!")
				continue
			else:
				break

		elif not definition.get('absoluteLocations', True) and attr == 'location':
			for expectedVal in possibleVals:
				relativeLocation = RectLTWH(*map(sub, expectedVal, val))
				if relativeLocation.topLeft == relativeLocation.bottomRight:
					break
			else:
				break
		else:
			break
	else:
		# if we did not encounter a break statement in the previous for loop we get here
		return True
	return False


class ObjEnhancerOverlay(NVDAObject):
	pass


def getOverlayClassForDefinition(definition):
	name = definition.name[0].upper() + definition.name[1:]
	output = definition.get('output', {})
	if not output:
		# this appears to be a empty definition helper (like fg dependencies) so we ignore this
		return None
	if not ( (isinstance(definition, Section) or isinstance(definition, dict)) and output):
		raise ValueError("Invalid definition specification provided: {definition}".format(definition=definition))
	output = output.dict()
	output['_objEnhancerDefinition'] = definition
	return type(
		"{}ObjEnhancerOverlay".format(name),
		(ObjEnhancerOverlay,),
		output
		)


def findMatchingDefinitionsForObj(obj, definitions, objCache):
	if not isinstance(definitions, configobj.ConfigObj):
		raise ValueError("Invalid spesification provided: {definitions}".format(definitions=definitions))
	for name, definition in definitions.items():
		if definition['isAbstract']:
			continue

		# parent in this context means the parent of the definition (from which the definition inherits filter criteria
		# so this is not related to the parent of the object
		parent = definition["parent"]
		if parent:
			try:
				parentDef = definitions[parent]
			except KeyError:
				log.error("Definition {name} refered to unknown parent: {parent}".format(name = name, parent=parent))
				continue
			if not evaluateObjectAttributes(obj, parentDef, objCache):
				return None

		# this part checks whether there is a filter that depends on the current foreground object and applies that filter
		fg = definition["fg"]
		if fg:
			fgObj = api.getForegroundObject()
			if not fgObj:
				return None
			try:
				fgDef = definitions[fg]
			except KeyError:
				log.error("Definition {name} refered to unknown foreground: {fg}".format(name=name, fg=fg))
				continue

			if not evaluateObjectAttributes(fgObj, fgDef, {}):
				# if the foreground object does not match with the demanded fg object, we deny this definition
				return None

		# if the optional parent definition and fg definition checks out, we check the object definition
		if evaluateObjectAttributes(obj, definition, {}):
			return definition
	return None

def getObjectVars(obj, inputAttributes):
	for attr in inputAttributes:
		try:
			val = getattr(obj, attr)
		except Exception:
			func = vars(utils).get(attr)
			if not callable(func):
				log.exception("Couldn't get {attr} from {obj!r}".format(attr=attr, obj=obj))
				continue
			try:
				val = MethodType(func, obj)()
			except Exception:
				log.exception("Couldn't get value for utility function {attr} from {obj!r}".format(attr=attr, obj=obj))
				continue
		yield (attr, val)
