# Object Enhancer

#Copyright (C) 2017 Babbage B.V.

#This file is covered by the GNU General Public License.
#See the file COPYING for more details.

import addonHandler
import globalPluginHandler
import definitionFileHandler
from configobj import ConfigObj
import os
from logHandler import log
from validate import Validator
import api
import definitionEvaluator
from copy import deepcopy
import appModuleHandler
from tones import beep
import dialogs
from NVDAObjects import NVDAObject
import gui
import wx
#We need to initialize translation and localization support:
addonHandler.initTranslation()

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	scriptCategory = _("Obj Enhancer")

	def __init__(self):
		super(GlobalPlugin, self).__init__()
		# Create a definitions dictionary
		self.definitions={}
		# populate the definitions dictionary
		self.loadDefinitions()

	def loadDefinition(self,appName, fileName=None, create=False):
		if appName in self.definitions:
			self.definitions[appName].reload()
			log.debug("Obj Enhancer definition file for {app} reloaded".format(app=appName))
		elif fileName:
			self.definitions[appName]=definitionFileHandler.getDefinitionOBjFromDefinitionFile(fileName,create)
			log.debug("Obj Enhancer definition file for {app} loaded from specified path {path}".format(app=appName,path=fileName))
		else:
			self.definitions[appName]=definitionFileHandler.getDefinitionOBjFromAppName(appName,create)
			log.debug("Obj Enhancer definition file for {app} loaded".format(app=appName))

	def unloadDefinition(self,appName, obj=None, delete=False):
		defObj=obj or self.definitions.get(appName,None)
		if not isinstance(defObj,ConfigObj):
			raise ValueError("{app} not registered".format(app=appName))
		del self.definitions[appName]
		defFile=defObj.filename
		if delete:
			os.remove(defFile)
			log.debug("Obj Enhancer definition file for {app} unloaded and deleted".format(app=appName))

	def loadDefinitions(self):
		for a,f in definitionFileHandler.availableDefinitionFiles():
			self.loadDefinition(a,f)
		# The global file should always be there
		if not 'global' in self.definitions:
			self.loadDefinition('global',create=True)

	def unloadDefinitions(self):
		# We do not use iteritems here as the dictionary changes in the for loop
		for app,obj in self.definitions.items():
			self.unloadDefinition(app,obj)

	def terminate(self):
		self.unloadDefinitions()
		super(GlobalPlugin,self).terminate()

	def getDefinitionsForAppModule(self,appModule):
		if not isinstance(appModule,appModuleHandler.AppModule):
			raise ValueError("Invalid appModule specified")
		name=appModule.appModuleName
		if name=="appModuleHandler":
			name=appModule.appName.encode('mbcs')
		# This will return None if no definitions available. Note that an empty dictionary will evaluate to False as well
		return self.definitions.get(name)

	def event_focusEntered(self,obj,nextHandler):
		try:
			appDefs=self.getDefinitionsForAppModule(obj.appModule)
			globalDefs=self.definitions['global']
			if appDefs:
				relevantDefs=deepcopy(appDefs)
				relevantDefs.merge(globalDefs)
			else:
				relevantDefs=globalDefs
			if not relevantDefs:
				return
			matches={matchCount:definition for (matchCount,definition) in definitionEvaluator.findMatchingDefinitionsForObj(obj,relevantDefs)}
			if not matches:
				return
			objDefinition=matches[max(m for m in matches)]
			definitionEvaluator.manipulateObject(obj,objDefinition)
		finally:
			nextHandler()

	event_becomeNavigatorObject=event_gainFocus=event_focusEntered

	def script_navigatorObject_enhance(self,gesture):
		obj=api.getNavigatorObject()
		if not isinstance(obj,NVDAObject):
			# Translators: Reported when the user tries to perform a command related to the navigator object
			# but there is no current navigator object.
			ui.message(_("No navigator object"))
			return
		wx.CallAfter(gui.mainFrame._popupSettingsDialog,dialogs.SingleDefinitionDialog,obj=obj,spec=getattr(obj,'objEnhancerSpec',{}))
	script_navigatorObject_enhance.__doc__=_("Customize the properties of the navigator object")

	__gestures = {
		"kb:NVDA+control+tab":"navigatorObject_enhance"
	}
