# Object Enhancer

# Copyright (C) 2017-2019 Babbage B.V.

# This file is covered by the GNU General Public License.
# See the file COPYING for more details.

import wx
import gui
import configobj
import addonHandler
from .definitionEvaluator import ObjEnhancerOverlay, getObjectVars
from .definitionFileHandler import validateDefinitionObj
from . import constants
import NVDAObjects
from copy import copy
from logHandler import log
from ast import literal_eval
from . import utils
addonHandler.initTranslation()

# Used to ensure that event handlers call Skip(). Not calling skip can cause focus problems for controls. More
# generally the advice on the wx documentation is:
# "In general, it is recommended to skip all non-command events
# to allow the default handling to take place. The command events are, however,
# normally not skipped as usually
# a single command such as a button click or menu item selection must only be processed by one handler."


def skipEventAndCall(handler):
	def wrapWithEventSkip(event):
		if event:
			event.Skip()
		return handler()
	return wrapWithEventSkip


class AddInputEntryDialog(wx.Dialog):

	def __init__(self, parent, title, obj, objectVars=None):
		super(AddInputEntryDialog, self).__init__(parent, title=title)
		self.obj = obj
		if objectVars:
			self.objectVars = objectVars
		else:
			self.objectVars = list(getObjectVars(obj, constants.INPUT_ATTRIBUTES)) if obj else []

		mainSizer = wx.BoxSizer(wx.VERTICAL)
		sHelper = gui.guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)

		varsText = _("&Relevant object attributes:")
		self.varsList = sHelper.addLabeledControl(
			varsText, gui.nvdaControls.AutoWidthColumnListCtrl,
			autoSizeColumn=2,
			itemTextCallable=self.getItemTextForVarsList,
			style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_VIRTUAL
		)
		self.varsList.ItemCount = len(self.objectVars)
		# Translators: The label for a column in input list used to identify an entry.
		self.varsList.InsertColumn(0, _("Attribute"))
		# Translators: The label for a column in input list used to identify an item's value.
		self.varsList.InsertColumn(1, _("Value"))
		self.varsList.Bind(wx.EVT_LIST_ITEM_FOCUSED, self.onVarsListItemFocused)
		if not obj:
			self.varsList.Disable()

		attributeText = _("A&ttribute:")
		self.attributeEdit = sHelper.addLabeledControl(attributeText, wx.TextCtrl)

		valueText = _("&Value:")
		self.valueEdit = sHelper.addLabeledControl(valueText, wx.TextCtrl)

		sHelper.addDialogDismissButtons(self.CreateButtonSizer(wx.OK | wx.CANCEL))

		mainSizer.Add(sHelper.sizer, border=gui.guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL)
		mainSizer.Fit(self)
		self.SetSizer(mainSizer)
		if obj:
			self.varsList.SetFocus()
		else:
			self.attributeEdit.SetFocus()
		self.CentreOnScreen()

	def getItemTextForVarsList(self, item, column):
		return str(self.objectVars[item][column])

	def onVarsListItemFocused(self, evt):
		index = evt.Index
		self.attributeEdit.Value = self.objectVars[index][0]
		value = self.objectVars[index][1]
		if isinstance(value, tuple):
			value = tuple.__repr__(value)
		else:
			value = str(value)
		self.valueEdit.Value = value


class EditInputEntryDialog(wx.Dialog):

	def __init__(self, parent, title, values):
		super(EditInputEntryDialog, self).__init__(parent, title=title)
		self.values = copy(values)

		mainSizer = wx.BoxSizer(wx.VERTICAL)
		sHelper = gui.guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)

		valuesText = "&{title}".format(title=title)
		self.valuesList = sHelper.addLabeledControl(
			valuesText, gui.nvdaControls.AutoWidthColumnListCtrl,
			itemTextCallable=self.getItemTextForValuesList,
			style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_VIRTUAL
		)
		self.valuesList.ItemCount = len(self.values)
		# Translators: The label for a column in input list used to identify an entry.
		self.valuesList.InsertColumn(0, _("Value"))
		self.valuesList.Bind(wx.EVT_LIST_ITEM_FOCUSED, self.onValuesListItemFocused)

		valueText = _("&Value:")
		self.valueEdit = sHelper.addLabeledControl(valueText, wx.TextCtrl)
		self.valueEdit.Bind(wx.EVT_TEXT, skipEventAndCall(self.onItemEdited))

		bHelper = sHelper.addItem(gui.guiHelper.ButtonHelper(orientation=wx.HORIZONTAL))

		# Translators: The label for a button to add a new entry.
		self.addButton = bHelper.addButton(self, label=_("&Add"))
		# Translators: The label for a button to remove an entry.
		self.removeButton = bHelper.addButton(self, label=_("Re&move"))
		self.removeButton.Disable()

		self.addButton.Bind(wx.EVT_BUTTON, skipEventAndCall(self.onAddClick))
		self.removeButton.Bind(wx.EVT_BUTTON, skipEventAndCall(self.onRemoveClick))

		sHelper.addDialogDismissButtons(self.CreateButtonSizer(wx.OK | wx.CANCEL))

		mainSizer.Add(sHelper.sizer, border=gui.guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL)
		mainSizer.Fit(self)
		self.SetSizer(mainSizer)
		self.valuesList.SetFocus()
		self.CentreOnScreen()

	def getItemTextForValuesList(self, item, column):
		return str(self.values[item])

	def onItemEdited(self):
		index = self.valuesList.GetFirstSelected()
		# Update the entry the user was just editing.
		entry = self.values
		try:
			val = literal_eval(self.valueEdit.Value)
		except Exception:
			val = self.valueEdit.Value
		entry[index] = val

	def onAddClick(self):
		self.values.append("")
		self.valuesList.ItemCount = len(self.values)
		index = self.valuesList.ItemCount - 1
		self.valuesList.Select(index)
		self.valuesList.Focus(index)
		# We don't get a new focus event with the new index.
		self.valuesList.sendListItemFocusedEvent(index)
		self.valueEdit.SetFocus()

	def onRemoveClick(self):
		index = self.valuesList.GetFirstSelected()
		del self.values[index]
		self.valuesList.ItemCount = len(self.values)
		# sometimes removing may result in an empty list.
		if not self.valuesList.ItemCount:
			# disable the controls, since there are no items in the list.
			self.removeButton.Disable()
		else:
			index = min(index, self.valuesList.ItemCount - 1)
			self.valuesList.Select(index)
			self.valuesList.Focus(index)
			# We don't get a new focus event with the new index.
			self.valuesList.sendListItemFocusedEvent(index)
		self.valuesList.SetFocus()

	def onValuesListItemFocused(self, evt):
		index = evt.Index
		self.valueEdit.Value = str(self.values[index])
		self.removeButton.Enable()


class InputPanel(wx.Panel):

	def __init__(self, parent, definition, obj=None, objectVars=None):
		if not isinstance(definition, dict):
			raise ValueError("Invalid definition provided: {definition}".format(definition=definition))
		self.definition = definition
		self.input = list(definition['input'].items())
		self.functions = list(definition['functions'].items())
		self.obj = obj
		self.objectVars = objectVars
		super(InputPanel, self).__init__(parent, id=wx.ID_ANY)
		sizer = gui.guiHelper.BoxSizerHelper(self, orientation=wx.HORIZONTAL)
		# Translators: The label for input list.
		inputText = _("&Filter criteria:")
		self.inputList = sizer.addLabeledControl(
			inputText, gui.nvdaControls.AutoWidthColumnListCtrl,
			autoSizeColumn=1,
			itemTextCallable=self.getItemTextForList,
			style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_VIRTUAL
		)
		self.inputList.ItemCount = len(self.input)
		# Translators: The label for a column in input list used to identify an entry.
		self.inputList.InsertColumn(0, _("Attribute"))
		# Translators: The label for a column in input list used to identify an item's value.
		self.inputList.InsertColumn(1, _("Value"))
		self.inputList.Bind(wx.EVT_LIST_ITEM_FOCUSED, self.onListItemFocused)

		self.editingItem = None

		bHelper = sizer.addItem(gui.guiHelper.ButtonHelper(orientation=wx.HORIZONTAL))
		# Translators: The label for a button to add a new entry.
		self.addButton = bHelper.addButton(self, label=_("&Add"))
		# Translators: The label for a button to edit a new entry.
		self.editButton = bHelper.addButton(self, label=_("&Edit"))
		self.editButton.Disable()
		# Translators: The label for a button to remove an entry.
		self.removeButton = bHelper.addButton(self, label=_("Re&move"))
		self.removeButton.Disable()

		self.addButton.Bind(wx.EVT_BUTTON, skipEventAndCall(self.onAddClick))
		self.editButton.Bind(wx.EVT_BUTTON, skipEventAndCall(self.onEditClick))
		self.removeButton.Bind(wx.EVT_BUTTON, skipEventAndCall(self.onRemoveClick))

		self.SetSizerAndFit(sizer.sizer)

	def getItemTextForList(self, item, column):
		entry = self.input[item]
		if column == 0:
			return entry[column]
		elif column == 1:
			return ", ".join(str(x) for x in entry[column])
		else:
			raise ValueError("Unknown column: %d" % column)

	def onListItemFocused(self, evt):
		# Update the editing controls to reflect the newly selected criterium.
		index = evt.Index
		self.editingItem = index
		self.editButton.Enable()
		self.removeButton.Enable()
		evt.Skip()

	def onAddClick(self):
		with AddInputEntryDialog(
			self,
			title=_("Add filter attribute"),
			obj=self.obj,
			objectVars=self.objectVars
		) as entryDialog:
			if entryDialog.ShowModal() != wx.ID_OK:
				return
			newAttr = entryDialog.attributeEdit.Value
			if not newAttr:
				return
			try:
				newValue = literal_eval(entryDialog.valueEdit.Value)
			except Exception:
				newValue = entryDialog.valueEdit.Value
		for index, (attr, val) in enumerate(self.input):
			if newAttr == attr:
				# Translators: An error reported when adding an attribute that is already present.
				gui.messageBox(
					_("Attribute {newAttr!r} is already added.").format(newAttr=newAttr),
					_("Error"), wx.OK | wx.ICON_ERROR)
				self.inputList.Select(index)
				self.inputList.Focus(index)
				self.inputList.SetFocus()
				return
		self.input.append((newAttr, [newValue]))
		self.inputList.ItemCount = len(self.input)
		index = self.inputList.ItemCount - 1
		self.inputList.Select(index)
		self.inputList.Focus(index)
		# We don't get a new focus event with the new index.
		self.inputList.sendListItemFocusedEvent(index)
		self.inputList.SetFocus()

	def onEditClick(self):
		index = self.inputList.GetFirstSelected()
		attr, values = self.input[index]
		with EditInputEntryDialog(
			self,
			title=_("Filter values for {attr}").format(attr=attr),
			values=values,
		) as entryDialog:
			if entryDialog.ShowModal() != wx.ID_OK:
				return
			newValues = entryDialog.values
			if not newValues:
				# Translators: An error reported when adding an attribute that is already present.
				gui.messageBox(
					_("NO values specified."),
					_("Error"), wx.OK | wx.ICON_ERROR)
			values[:] = newValues

	def onRemoveClick(self):
		index = self.inputList.GetFirstSelected()
		del self.input[index]
		self.inputList.ItemCount = len(self.input)
		# sometimes removing may result in an empty list.
		if not self.inputList.ItemCount:
			self.editingItem = None
			# disable the controls, since there are no items in the list.
			self.editButton.Disable()
			self.removeButton.Disable()
		else:
			index = min(index, self.inputList.ItemCount - 1)
			self.inputList.Select(index)
			self.inputList.Focus(index)
			# We don't get a new focus event with the new index.
			self.inputList.sendListItemFocusedEvent(index)
		self.inputList.SetFocus()


class AddOutputEntryDialog(wx.Dialog):

	def __init__(self, parent, title, attributes):
		super(AddOutputEntryDialog, self).__init__(parent, title=title)
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		sHelper = gui.guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)

		attributeSizer = wx.BoxSizer(wx.HORIZONTAL)
		# Translators: This is the label for the edit field.
		attributeText = _("Attribute:")
		attributeLabel = wx.StaticText(self, label=attributeText)
		attributeSizer.Add(attributeLabel, flag=wx.ALIGN_CENTER_VERTICAL)
		attributeSizer.AddSpacer(gui.guiHelper.SPACE_BETWEEN_ASSOCIATED_CONTROL_HORIZONTAL)
		self.attributeCombo = wx.ComboBox(
			self,
			choices=attributes,
			style=wx.CB_DROPDOWN
		)
		attributeSizer.Add(self.attributeCombo)
		sHelper.addItem(attributeSizer)

		sHelper.addDialogDismissButtons(self.CreateButtonSizer(wx.OK | wx.CANCEL))

		mainSizer.Add(sHelper.sizer, border=gui.guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL)
		mainSizer.Fit(self)
		self.SetSizer(mainSizer)
		self.attributeCombo.SetFocus()
		self.CentreOnScreen()


class OutputPanel(wx.Panel):

	def __init__(self, parent, definition, obj=None):
		if not isinstance(definition, dict):
			raise ValueError("Invalid definition provided: {definition}").format(definition=definition)
		self.output = list(definition['output'].items())
		super(OutputPanel, self).__init__(parent, id=wx.ID_ANY)
		sizer = gui.guiHelper.BoxSizerHelper(self, orientation=wx.HORIZONTAL)
		# Translators: The label for output list.
		outputText = _("&Attribute changes:")
		self.outputList = sizer.addLabeledControl(
			outputText,
			gui.nvdaControls.AutoWidthColumnListCtrl,
			autoSizeColumn=1,
			itemTextCallable=self.getItemTextForList,
			style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_VIRTUAL
		)
		self.outputList.ItemCount = len(self.output)
		# Translators: The label for a column in output list used to identify an entry.
		self.outputList.InsertColumn(0, _("Attribute"))
		# Translators: The label for a column in output list used to identify an item's value.
		self.outputList.InsertColumn(1, _("Value"))
		self.outputList.Bind(wx.EVT_LIST_ITEM_FOCUSED, self.onListItemFocused)

		# Translators: The label for the group of controls to change an item.
		changeItemText = _("Change output value")
		changeItemHelper = sizer.addItem(
			gui.guiHelper.BoxSizerHelper(
				self,
				sizer=wx.StaticBoxSizer(wx.StaticBox(self, label=changeItemText), wx.VERTICAL)
				))
		attributeSizer = wx.BoxSizer(wx.HORIZONTAL)
		# Translators: The label for the edit field to change the attribute of an item.
		attributeText = _("Output &attribute:")
		attributeLabel = wx.StaticText(self, label=attributeText)
		attributeSizer.Add(attributeLabel, flag=wx.ALIGN_CENTER_VERTICAL)
		attributeSizer.AddSpacer(gui.guiHelper.SPACE_BETWEEN_ASSOCIATED_CONTROL_HORIZONTAL)
		self.attributeCombo = wx.ComboBox(
			self,
			choices=constants.OUTPUT_ATTRIBUTES,
			style=wx.CB_DROPDOWN
		)
		attributeSizer.Add(self.attributeCombo)
		changeItemHelper.addItem(attributeSizer)

		self.attributeCombo.Bind(wx.EVT_TEXT, skipEventAndCall(self.onItemEdited))

		# Translators: The label for the edit field to change the value of a criterium.
		valueText = _("Output &value:")
		self.valueEdit = changeItemHelper.addLabeledControl(valueText, wx.TextCtrl)
		self.valueEdit.Bind(wx.EVT_TEXT, skipEventAndCall(self.onItemEdited))

		# disable controls until an item is selected
		self.attributeCombo.Disable()
		self.valueEdit.Disable()

		self.editingItem = None

		bHelper = sizer.addItem(gui.guiHelper.ButtonHelper(orientation=wx.HORIZONTAL))
		# Translators: The label for a button to add a new entry.
		self.addButton = bHelper.addButton(self, label=_("&Add"))
		# Translators: The label for a button to remove an entry.
		self.removeButton = bHelper.addButton(self, label=_("Re&move"))
		self.removeButton.Disable()

		self.addButton.Bind(wx.EVT_BUTTON, skipEventAndCall(self.onAddClick))
		self.removeButton.Bind(wx.EVT_BUTTON, skipEventAndCall(self.onRemoveClick))

		self.SetSizerAndFit(sizer.sizer)

	def getItemTextForList(self, item, column):
		entry = self.output[item]
		return entry[column]

	def onItemEdited(self):
		if self.editingItem is not None:
			# Update the entry the user was just editing.
			attribute = self.attributeCombo.Value
			val = self.valueEdit.Value
			self.output[self.editingItem] = (attribute, val)

	def onListItemFocused(self, evt):
		# Update the editing controls to reflect the newly selected criterium.
		index = evt.Index
		self.editingItem = index
		entry = self.output[index]
		attr, val = entry
		self.attributeCombo.ChangeValue(attr)
		self.valueEdit.ChangeValue(val)
		self.removeButton.Enable()
		self.attributeCombo.Enable()
		self.valueEdit.Enable()
		evt.Skip()

	def onAddClick(self):
		with AddOutputEntryDialog(
			self,
			title=_("Add output attribute"),
			attributes=constants.OUTPUT_ATTRIBUTES
		) as entryDialog:
			if entryDialog.ShowModal() != wx.ID_OK:
				return
			newAttr = entryDialog.attributeCombo.Value
			if not newAttr:
				return
		for index, (attr, val) in enumerate(self.output):
			if newAttr == attr:
				# Translators: An error reported when adding an attribute that is already present.
				gui.messageBox(
					_('Attribute {newAttr!r} is already present.').format(newAttr=newAttr),
					_("Error"), wx.OK | wx.ICON_ERROR)
				self.outputList.Select(index)
				self.outputList.Focus(index)
				self.outputList.SetFocus()
				return
		self.output.append((newAttr, ""))
		self.outputList.ItemCount = len(self.output)
		index = self.outputList.ItemCount - 1
		self.outputList.Select(index)
		self.outputList.Focus(index)
		# We don't get a new focus event with the new index.
		self.outputList.sendListItemFocusedEvent(index)
		self.valueEdit.SetFocus()

	def onRemoveClick(self):
		index = self.outputList.GetFirstSelected()
		del self.output[index]
		self.outputList.ItemCount = len(self.output)
		# sometimes removing may result in an empty list.
		if not self.outputList.ItemCount:
			self.editingItem = None
			# disable the controls, since there are no items in the list.
			self.attributeCombo.Disable()
			self.valueEdit.Disable()
			self.removeButton.Disable()
		else:
			index = min(index, self.outputList.ItemCount - 1)
			self.outputList.Select(index)
			self.outputList.Focus(index)
			# We don't get a new focus event with the new index.
			self.outputList.sendListItemFocusedEvent(index)
		self.outputList.SetFocus()


class OptionsPanel(wx.Panel):

	def __init__(self, parent, definition):
		if not isinstance(definition, dict):
			raise ValueError("Invalid definition provided: {definition}".format(definition=definition))
		self.definition = definition
		self.options = definition['options']
		super(OptionsPanel, self).__init__(parent, id=wx.ID_ANY)
		optionsText = _("options")
		sHelper = gui.guiHelper.BoxSizerHelper(
			self,
			sizer=wx.StaticBoxSizer(wx.StaticBox(self, label=optionsText), wx.VERTICAL)
			)

		absoluteLocationsText = _("&Treat object location criteria as absolute screen coordinates")
		self.absoluteLocationsCheckBox = sHelper.addItem(wx.CheckBox(self, label=absoluteLocationsText))
		self.absoluteLocationsCheckBox.Value = self.options.get('absoluteLocations', True)
		self.absoluteLocationsCheckBox.Bind(
			wx.EVT_CHECKBOX,
			self.onAbsoluteLocationsCheckbox
		)

		handleDefinitionErrorsText = _("&Definition error handling:")
		self.handleDefinitionErrorsChoices = ("ignore", "break", "raise")
		self.handleDefinitionErrorsList = sHelper.addLabeledControl(
			handleDefinitionErrorsText,
			wx.Choice,
			choices=self.handleDefinitionErrorsChoices)
		curChoice = self.options.get('handleDefinitionErrors', "break")
		self.handleDefinitionErrorsList.Selection = self.handleDefinitionErrorsChoices.index(curChoice)
		self.handleDefinitionErrorsList.Bind(
			wx.EVT_CHOICE,
			skipEventAndCall(self.onHandleDefinitionErrorsListChange)
			)

		self.SetSizerAndFit(sHelper.sizer)
	def onAbsoluteLocationsCheckbox(self, evt):
		self.options['absoluteLocations'] = evt.IsChecked()

	def onHandleDefinitionErrorsListChange(self):
		self.options['handleDefinitionErrors'] = self.handleDefinitionErrorsChoices[
			self.handleDefinitionErrorsList.Selection]


class SingleDefinitionDialog(gui.SettingsDialog):

	def __init__(
			self,
			parent,
			moduleDefinitions,
			definition=None,
			obj=None,
			objectVars=None,
			multiInstanceAllowed=False):
		if definition is None and obj is None:
			raise ValueError("Either obj or definition is required")
		elif obj and not isinstance(obj, NVDAObjects.NVDAObject):
			raise ValueError("Invalid object provided")
		if not definition:
			definition = getattr(obj, "_objEnhancerDefinition", {})
		if isinstance(definition, configobj.Section):
			self.title = _("Editing definition (%s)") % definition.name
			if obj:
				assert isinstance(obj, ObjEnhancerOverlay)
		else:
			self.title = _("New definition")
		self.definition = definition
		self.obj = obj
		self.objectVars = objectVars
		self.moduleDefinitions = moduleDefinitions
		super(SingleDefinitionDialog, self).__init__(parent, multiInstanceAllowed=multiInstanceAllowed)

	def makeSettings(self, settingsSizer):
		settingsSizerHelper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		nameText = _("Identifying name:")
		self.nameEdit = settingsSizerHelper.addLabeledControl(nameText, wx.TextCtrl)
		if isinstance(self.definition, configobj.Section):
			self.nameEdit.Value = self.definition.name
		if self.definition.get('input') is None:
			self.definition['input'] = {}
		if self.definition.get('functions') is None:
			self.definition['functions'] = {}
		self.inputPanel = InputPanel(
			parent=self,
			definition=self.definition,
			obj=self.obj,
			objectVars=self.objectVars
		)
		settingsSizerHelper.addItem(self.inputPanel)

		if self.definition.get('options') is None:
			self.definition['options'] = {}
		self.optionsPanel = OptionsPanel(parent=self, definition=self.definition)
		settingsSizerHelper.addItem(self.optionsPanel)

		if self.definition.get('output') is None:
			self.definition['output'] = {}
		self.outputPanel = OutputPanel(parent=self, definition=self.definition, obj=self.obj)
		settingsSizerHelper.addItem(self.outputPanel)

	def postInit(self):
		self.nameEdit.SetFocus()

	def onOk(self, evt):
		try:
			name = self.nameEdit.Value
			parent = self.moduleDefinitions
			self.definition["input"] = dict(self.inputPanel.input)
			self.definition["functions"] = dict(self.inputPanel.functions)
			self.definition["output"] = dict(self.outputPanel.output)
			# self.definition[options] = dict(self.options)
			if isinstance(self.definition, configobj.Section):
				assert parent is self.definition.parent
				# This is an existing definition
				if self.definition.name != name:
					parent.rename(self.definition.name, name)
					# A bug in configobj doesn't update self.definition.name
					self.definition.name = name
			else:  # New definition
				parent[name] = self.definition
			validateDefinitionObj(parent)
			if not isinstance(self.Parent, DefinitionsPanel):
				parent.write()
		finally:
			super(SingleDefinitionDialog, self).onOk(evt)

	def onCancel(self, evt):
		try:
			parent = self.moduleDefinitions
			if not isinstance(self.Parent, DefinitionsPanel):
				parent.reload()
				validateDefinitionObj(parent)
		finally:
			super(SingleDefinitionDialog, self).onCancel(evt)


class DefinitionsPanel(gui.settingsDialogs.SettingsPanel):

	def makeSettings(self, sizer):
		settingsSizerHelper = gui.guiHelper.BoxSizerHelper(self, sizer=sizer)
		definitionsText = _("&Available definitions:")
		self.definitionsList = settingsSizerHelper.addLabeledControl(
			definitionsText,
			gui.nvdaControls.AutoWidthColumnListCtrl,
			autoSizeColumn=3,
			itemTextCallable=self.getItemTextForList,
			style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_VIRTUAL
		)
		self.definitionsList.ItemCount = len(self.definitions)
		self.definitionsList.InsertColumn(0, _("Identifier"))
		self.definitionsList.InsertColumn(1, _("Input"))
		self.definitionsList.InsertColumn(2, _("Output"))
		self.definitionsList.Bind(wx.EVT_LIST_ITEM_FOCUSED, self.onListItemFocused)

		bHelper = settingsSizerHelper.addItem(gui.guiHelper.ButtonHelper(orientation=wx.HORIZONTAL))
		# Translators: The label for a button to add a new entry.
		self.addButton = bHelper.addButton(self, label=_("&Add"))
		# Translators: The label for a button to edit a new entry.
		self.editButton = bHelper.addButton(self, label=_("&Edit"))
		self.editButton.Disable()
		# Translators: The label for a button to remove an entry.
		self.removeButton = bHelper.addButton(self, label=_("Re&move"))
		self.removeButton.Disable()

		self.addButton.Bind(wx.EVT_BUTTON, skipEventAndCall(self.onAddClick))
		self.editButton.Bind(wx.EVT_BUTTON, skipEventAndCall(self.onEditClick))
		self.removeButton.Bind(wx.EVT_BUTTON, skipEventAndCall(self.onRemoveClick))

	def onSave(self):
		validateDefinitionObj(self.definitions)
		self.definitions.write()

	def onDiscard(self):
		self.definitions.reload()
		validateDefinitionObj(self.definitions)

	def getItemTextForList(self, item, column):
		entry = list(self.definitions.values())[item]
		if column == 0:
			return entry.name
		elif column == 1:
			return "test"
		elif column == 2:
			return "test2"
		else:
			raise ValueError("Unknown column: %d" % column)

	def onListItemFocused(self, evt):
		# Update the editing controls to reflect the newly selected criterium.
		self.editButton.Enable()
		self.removeButton.Enable()
		evt.Skip()

	def onAddClick(self):
		newEntry = SingleDefinitionDialog(self, self.definitions, definition={}, multiInstanceAllowed=True)
		ret = newEntry.ShowModal()
		if ret == wx.ID_OK:
			self.Freeze()
			# trigger a refresh of the settings
			self._sendLayoutUpdatedEvent()
			self.Thaw()

	def onEditClick(self):
		index = self.definitionsList.GetFirstSelected()
		editedEntry = SingleDefinitionDialog(
			self,
			self.definitions,
			definition=list(self.definitions.values())[index],
			multiInstanceAllowed=True
		)
		ret = editedEntry.ShowModal()
		if ret == wx.ID_OK:
			self.Freeze()
			# trigger a refresh of the settings
			self._sendLayoutUpdatedEvent()
			self.Thaw()

	def onRemoveClick(self):
		index = self.definitionsList.GetFirstSelected()
		name = list(self.definitions)[index]
		del self.definitions[name]
		self.definitionsList.ItemCount = len(self.definitions)
		# sometimes removing may result in an empty list.
		if not self.definitionsList.ItemCount:
			# disable the controls, since there are no items in the list.
			self.editButton.Disable()
			self.removeButton.Disable()
		else:
			index = min(index, self.definitionsList.ItemCount - 1)
			self.definitionsList.Select(index)
			self.definitionsList.Focus(index)
			# We don't get a new focus event with the new index.
			self.definitionsList.sendListItemFocusedEvent(index)
		self.definitionsList.SetFocus()


class DefinitionsDialog(gui.settingsDialogs.MultiCategorySettingsDialog):
	title = _("Object Enhancer Definitions")

	def __init__(self, parent, multipleDefinitionsDict, initialCategory=None):
		self.multipleDefinitionsDict = multipleDefinitionsDict
		self._categoryClasses = []
		super(DefinitionsDialog, self).__init__(parent, initialCategory=initialCategory)

	def makeSettings(self, settingsSizer):
		super(DefinitionsDialog, self).makeSettings(settingsSizer)
		# Hack, override the label for categories.
		# This really should be an option on MultiCategorySettingsDialog.
		try:
			staticText = settingsSizer.Children[0].Sizer.Children[0].Window
			staticText.Label = _("&Applications:")
		except Exception:
			pass

	@property
	def categoryClasses(self):
		if self._categoryClasses:
			return self._categoryClasses
		self._categoryClasses = []
		for name, definitions in self.multipleDefinitionsDict.items():
			self._categoryClasses.append(
				type(
					"{name}DefinitionsPanel".format(name=name.capitalize()),
					(DefinitionsPanel,),
					dict(
						title=name.capitalize(),
						definitions=definitions
					)
				)
			)
		return self._categoryClasses
