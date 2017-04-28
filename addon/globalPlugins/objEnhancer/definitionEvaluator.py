# Object Enhancer

#Copyright (C) 2017 Babbage B.V.

#This file is covered by the GNU General Public License.
#See the file COPYING for more details.

import configobj
from baseObject import AutoPropertyObject
from NVDAObjects import NVDAObject
from operator import attrgetter
from logHandler import log
from operator import sub
import itertools

def evaluateObjAttrs(obj,spec):
	if not isinstance(obj,NVDAObject):
		raise ValueError("Invalid NVDAObject specified: %s"%obj)
	matches=0
	input=spec.get('input',{})
	if not (isinstance(spec,dict) and input):
		raise ValueError("Invalid spesification provided: %s"%spec)
	options=spec.get('options',{})
	# We intentionally do not use iterators here
	attrs=input.keys()
	getter=attrgetter(*attrs)
	relativeLocations={}
	try:
		actualValues=list(getter(obj)) if len(attrs)>1 else [getter(obj)]
	except:
		return 0
	expectedValues=input.values()
	if len(actualValues)!=len(expectedValues):
		raise RuntimeError("Lengths don't match")
	for i in xrange(len(attrs)):
		attr=attrs[i]
		exVal=expectedValues[i]
		actVal=actualValues[i]
		if not options.get('absoluteLocations',True) and 'location' in attr:
			relativeLocations[attr]=tuple(map(sub,exVal,actVal))
		elif actVal==exVal:
			matches+=1
		else:
			return 0
	if len(relativeLocations)==1 and relativeLocations.values()[0]==(0,0,0,0):
		matches=+1
	for x,y in itertools.combinations(relativeLocations.itervalues(),2):
		if x[:2]!=y[:2]:
			return 0
		matches+=1
	return matches

def manipulateObject(obj,spec):
	output=spec.get('output',{})
	if not (isinstance(spec,dict) and output):
		raise ValueError("Invalid specification provided: %s"%spec)
	options=spec.get('options',{})
	setattr(obj,'objEnhancerSpec',spec)
	for attr,val in output.iteritems():
		if not options.get('ignoreNonexistentAttributes',True):
			try:
				getattr(obj,atr)
			except Exception as e:
				if options.get('raiseOutputErrors',True):
					raise e
				else:
					continue
		try:
			setattr(obj,attr,val)
		except Exception as e:
			if options.get('raiseOutputErrors',True):
				raise e
			else:
				continue

def findMatchingDefinitionsForObj(obj,definitions):
	if not isinstance(definitions,configobj.ConfigObj):
		raise ValueError("Invalid spesification provided: %s"%definitions)
	for objId,definition in definitions.iteritems():
		matches=evaluateObjAttrs(obj,definition)
		if matches:
			yield (matches,definition)
