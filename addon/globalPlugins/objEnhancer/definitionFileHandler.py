# Object Enhancer

#Copyright (C) 2017 Babbage B.V.

#This file is covered by the GNU General Public License.
#See the file COPYING for more details.

import globalVars
import os
from logHandler import log
from configobj import ConfigObj
from io import BytesIO
from validate import Validator

defFileSpec=ConfigObj(BytesIO("""[__many__]
	[[input]]
		[[options]]
			raiseOutputErrors = bool(default=True)
			ignoreNonexistentAttributes = bool(default=True)
			absoluteLocations = bool(default=False)
			ignoreGainFocusEvent = bool(default=False)
			ignoreBecomeNavigatorObjectEvent = bool(default=False)
		[[output]]"""),
	indent_type="\t",
	encoding="UTF-8",
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
		yield (appName,os.path.join(definitionFilePath,fileName))

def getDefinitionFileFromAppName(appName,errorNotFound=False):
	filePath=os.path.join(getDefinitionFileDir(),"{name}.objdef.ini".format(name=appName.replace(".","_")))
	if errorNotFound and not os.path.isfile(filePath):
		raise IOError("{path} does not exist".format(path=filePath))
	return filePath

def getDefinitionOBjFromDefinitionFile(definitionFile,create=True):
	# configObj objects are created even when the file doesn't exist
	if not os.path.isabs(definitionFile):
		raise ValueError("Absolute path required")
	try:
		obj=ConfigObj(
			infile=definitionFile,
			raise_errors=True,
			create_empty=create,
			file_error=not create,
			indent_type="\t",
			encoding="UTF-8",
			unrepr=True,
			configspec=defFileSpec
		)
		obj.newlines = "\r\n"
		val = Validator()
		obj.validate(val, copy=True)
	except Exception as e:
		raise e
	return obj

def getDefinitionOBjFromAppName(appName,create=True):
	return getDefinitionOBjFromDefinitionFile(getDefinitionFileFromAppName(appName,errorNotFound=not create),create)