# Object Enhancer

#Copyright (C) 2017 Babbage B.V.

#This file is covered by the GNU General Public License.
#See the file COPYING for more details.

import globalVars
import os
from logHandler import log
import configobj

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
	if not create and not os.path.isfile(definitionFile):
		raise IOError("{path} does not exist".format(path=definitionFile))
	try:
		obj=configobj.ConfigObj(
			infile=definitionFile,
			raise_errors=True
		)
	except error as e:
		raise e
	return obj

def getDefinitionOBjFromAppName(appName,create=True):
	return getDefinitionOBjFromDefinitionFile(getDefinitionFileFromAppName(appName,errorNotFound=not create),create)