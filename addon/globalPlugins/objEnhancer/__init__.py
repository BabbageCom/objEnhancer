# Object Enhancer

#Copyright (C) 2017 Babbage B.V.

#This file is covered by the GNU General Public License.
#See the file COPYING for more details.

import addonHandler
import globalPluginHandler
from . import definitionFileHandler
from configobj import ConfigObj
import os
from logHandler import log
import api
from . import definitionEvaluator
from copy import deepcopy
import appModuleHandler
from tones import beep
from . import dialogs
from NVDAObjects import NVDAObject
import gui
import wx
from scriptHandler import script
from .utils import bitmapHash
import ui
import weakref
#We need to initialize translation and localization support:
addonHandler.initTranslation()

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	scriptCategory = _("Obj Enhancer")

	def __init__(self):
		super(GlobalPlugin, self).__init__()
		# Create a definitions dictionary
		self.definitions = {}
		# populate the definitions dictionary
		self.loadDefinitions()

	def loadDefinition(self,appName, fileName=None, reload=False, create=False):
		if appName in self.definitions:
			if reload:
				self.definitions[appName].reload()
				definitionFileHandler.validateDefinitionObj(self.definitions[appName])
				log.debug(f"Obj Enhancer definition file for {appName} reloaded")
			else:
				log.debug(f"Obj Enhancer definition file for {appName} already loaded")
		elif fileName:
			self.definitions[appName]=definitionFileHandler.getDefinitionObjFromDefinitionFile(fileName,create)
			log.debug(f"Obj Enhancer definition file for {appName} loaded from specified path {fileName}")
		else:
			self.definitions[appName]=definitionFileHandler.getDefinitionObjFromAppName(appName,create)
			log.debug(f"Obj Enhancer definition file for {appName} loaded")

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
			self.loadDefinition(a,f, reload=True)
		# The global file should always be there
		if not 'global' in self.definitions:
			self.loadDefinition('global', create=True)

	def unloadDefinitions(self):
		# We do not use items here as the dictionary changes in the for loop
		for app,obj in list(self.definitions.items()):
			self.unloadDefinition(app,obj)

	def terminate(self):
		self.unloadDefinitions()
		super(GlobalPlugin,self).terminate()

	def getDefinitionsForAppModule(self,appModule, create=False):
		if not isinstance(appModule,appModuleHandler.AppModule):
			raise ValueError("Invalid appModule specified")
		name=appModule.appModuleName
		if name=="appModuleHandler":
			name=appModule.appName
		definitions = self.definitions.get(name)
		if definitions is None and create:
			self.loadDefinition(name, create=create)
			definitions = self.definitions.get(name)
		return definitions

	def chooseNVDAObjectOverlayClasses(self,obj,clsList):
		defs = []
		appDefs=self.getDefinitionsForAppModule(obj.appModule)
		globalDefs=self.definitions['global']
		if appDefs:
			defs.append(appDefs)
		if globalDefs:
			defs.append(globalDefs)
		objCache = {}
		for relevantDefs in defs:
			definition = definitionEvaluator.findMatchingDefinitionsForObj(obj,relevantDefs, objCache)
			if definition:
				clsList.insert(0, definitionEvaluator.getOverlayClassForDefinition(definition))
				break

	@script(
		description=_("Customize the properties of the navigator object"),
		gesture="kb:NVDA+control+tab"
	)
	def script_navigatorObject_enhance(self,gesture):
		obj=api.getNavigatorObject()
		if not isinstance(obj,NVDAObject):
			# Translators: Reported when the user tries to perform a command related to the navigator object
			# but there is no current navigator object.
			ui.message(_("No navigator object"))
			return
		wx.CallAfter(
			gui.mainFrame._popupSettingsDialog,
			dialogs.SingleDefinitionDialog,
			obj=obj,
			moduleDefinitions=self.getDefinitionsForAppModule(obj.appModule, create=True)
		)

	@script(
		description=_("Copies the base64 encoded SHA1 hash of the bitmap of the navigator object to the clipboard"),
		gesture="kb:NVDA+control+alt+h"
	)
	def script_copyHashToClipboard(self, gesture):
		if api.copyToClip(bitmapHash(api.getNavigatorObject()).decode("ascii")):
			ui.message("Hash copied to clipboard")
		else:
			ui.message("Couldn't copy hash to clipboard")
