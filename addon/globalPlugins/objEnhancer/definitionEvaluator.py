# Object Enhancer

#Copyright (C) 2017 Babbage B.V.

#This file is covered by the GNU General Public License.
#See the file COPYING for more details.

import configobj
from baseObject import AutoPropertyObject
from NVDAObjects import NVDAObject
from operator import attrgetter

def manipulateObject(obj,spec):
	options=spec.get('options')
	output=spec.get('output')
	if not (isinstance(spec,configobj.Section) and options and output):
		raise ValueError("Invalid specification")
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

def evaluateObjAttrs(obj,spec):
	if not isinstance(obj,NVDAObject):
		raise ValueError("Invalid NVDAObject specified")
	input=spec.get('input')
	options=spec.get('options')
	if not (isinstance(spec,configobj.Section) and input and options):
		raise ValueError("Invalid spesification provided")
	# We intentionally do not use iterators here
	attrs=input.keys()
	getter=attrgetter(*attrs)
	try:
		actualValues=list(getter(obj)) if len(attrs)>1 else [getter(obj)]
	except:
		return False
	expectedValues=input.values()
	if len(actualValues)!=len(expectedValues):
		raise RuntimeError("Lengths don't match")
	for i in xrange(len(attrs)):
		if actualValues[i]!=expectedValues[i]:
			return False
	return True

