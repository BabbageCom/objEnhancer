# Object Enhancer

#Copyright (C) 2017 Babbage B.V.

#This file is covered by the GNU General Public License.
#See the file COPYING for more details.

import globalVars
import os
from logHandler import log
from configobj import ConfigObj, flatten_errors
from io import StringIO
from configobj.validate import Validator, ValidateError
import controlTypes

defFileSpec=ConfigObj(StringIO(u"""[__many__]
	parent = string(default="")
	isAbstract = boolean(default=False)
	[[input]]
		___many___ = list(default=list())
	[[functions]]
	[[options]]
		absoluteLocations = boolean(default=True)
		handleDefinitionErrors = option("ignore", "break", "raise", default="break")
	[[output]]"""),
	indent_type="\t",
	encoding="UTF-8",
	interpolation=False,
	list_values=False,
	_inspec=True
)
defFileSpec.newlines = "\r\n"

def getDefinitionFileDir():
	configPath = globalVars.appArgs.configPath
	definitionFilePath=os.path.join(configPath,'objEnhancer')
	if not os.path.isdir(definitionFilePath):
		try:
			os.makedirs(definitionFilePath)
		except Exception as e:
			log.exception("Error creating definition file folder")
			return None
	return definitionFilePath

def availableDefinitionFiles():
	definitionFilePath=getDefinitionFileDir()
	for fileName in os.listdir(getDefinitionFileDir()):
		if not fileName.endswith(u'.objdef.ini'):
			continue	
		appName=fileName.rsplit('.',2)[0].encode('mbcs')
		yield (appName,os.path.abspath(os.path.join(definitionFilePath,fileName)))

def getDefinitionFileFromAppName(appName,errorNotFound=False):
	filePath=os.path.abspath(os.path.join(getDefinitionFileDir(),"{name}.objdef.ini".format(name=appName.replace(".","_"))))
	if errorNotFound and not os.path.isfile(filePath):
		raise IOError("{path} does not exist".format(path=filePath))
	return filePath

def getDefinitionOBjFromDefinitionFile(definitionFile,create=True):
	# configObj objects are created even when the file doesn't exist
	if not os.path.isabs(definitionFile):
		raise ValueError("Absolute path required")
	obj=ConfigObj(
		infile=definitionFile,
		raise_errors=True,
		create_empty=create,
		file_error=not create,
		indent_type="\t",
		encoding="UTF-8",
		interpolation=False,
		unrepr=True,
		configspec=defFileSpec
	)
	obj.newlines = "\r\n"
	val = Validator()
	res = obj.validate(val, preserve_errors=True)
	errors = []
	for section_list, key, error in flatten_errors(obj, res):
		if key is not None:
			section_list.append(key)
		else:
			section_list.append('[missing section]')
		section_string = ', '.join(section_list)
		if error == False:
			error = 'Missing value or section.'
		errors.append(section_string + ' = ' + error.message)
	if errors:
		raise ValidateError("Errors in %s: %s" % (definitionFile, "; ".join(errors)))
	for name, definition in obj.items():
		parent = definition[parent]
		try:
			parentDef = obj[parent]
		except KeyError:
			log.error("Definition %s refered to unknown parent %s" % (name, parent))
			continue
		temp = definition.dict()
		definition.merge(parentDef, decoupled=True)
		definition.merge(temp)
	return obj

def getDefinitionOBjFromAppName(appName,create=True):
	return getDefinitionOBjFromDefinitionFile(getDefinitionFileFromAppName(appName,errorNotFound=not create),create)
