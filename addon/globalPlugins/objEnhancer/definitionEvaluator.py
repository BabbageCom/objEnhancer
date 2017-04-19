# Object Enhancer

#Copyright (C) 2017 Babbage B.V.

#This file is covered by the GNU General Public License.
#See the file COPYING for more details.

import configobj
from baseObject import AutoPropertyObject
from NVDAObjects import NVDAObject
from operator import attrgetter

def manipulateObject(obj,spec):
	if not isinstance(spec,configobj.Section):
		raise ValueError("Invalid specification")

def evaluateObjAttrs(obj,spec,optionals=None):
	if not isinstance(obj,NVDAObject):
		raise ValueError("Invalid AutoPropertyObject specified")
	if not isinstance(spec,dict):
		raise ValueError("Specification should be a dictionary")
	# We intentionally do not use iterators here
	attrs=spec.keys()
	getter=attrgetter(*attrs)
	try:
		actualValues=list(getter(obj)) if len(attrs)>1 else [getter(obj)]
	except:
		return False
	expectedValues=spec.values()
	if len(actualValues)!=len(expectedValues):
		raise RuntimeError("Lengths don't match")
	for i in xrange(len(attrs)):
		if actualValues[i]!=expectedValues[i]:
			return False
	return True

def setattrObj(obj,attribute, value):
	"""setattr wrapper to deal with AutoPropertyObjects"""
	if not isinstance(obj,AutoPropertyObject):
		raise ValueError("Invalid AutoPropertyObject specified")
