# Object Enhancer

#Copyright (C) 2017 Babbage B.V.

#This file is covered by the GNU General Public License.
#See the file COPYING for more details.

import configobj
from baseObject import AutoPropertyObject
from NVDAObjects import NVDAObject
from operator import attrgetter
from logHandler import log

def evaluateObjAttrs(obj,spec, event):
	if not isinstance(obj,NVDAObject):
		raise ValueError("Invalid NVDAObject specified: %s"%obj)
	matches=0
	input=spec.get('input',{})
	if not (isinstance(spec,configobj.Section) and input):
		raise ValueError("Invalid spesification provided: %s"%spec)
	options=spec.get('options',{})
	if options.get('ignore%sEvent'%event[0].upper()+event[1:],False):
		return
	# We intentionally do not use iterators here
	attrs=input.keys()
	getter=attrgetter(*attrs)
	try:
		actualValues=list(getter(obj)) if len(attrs)>1 else [getter(obj)]
	except:
		return 0
	expectedValues=input.values()
	if len(actualValues)!=len(expectedValues):
		raise RuntimeError("Lengths don't match")
	for i in xrange(len(attrs)):
		if actualValues[i]!=expectedValues[i]:
			return 0
		matches+=1
	return matches

def manipulateObject(obj,spec):
	output=spec.get('output',{})
	if not (isinstance(spec,configobj.Section) and output):
		raise ValueError("Invalid specification provided: %s"%spec)
	options=spec.get('options',{})
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
