# Object Enhancer

#Copyright (C) 2017 Babbage B.V.

#This file is covered by the GNU General Public License.
#See the file COPYING for more details.

import wx
import gui
import configobj
import controlTypes
import addonHandler
import NVDAObjects
addonHandler.initTranslation()

# Used to ensure that event handlers call Skip(). Not calling skip can cause focus problems for controls. More
# generally the advice on the wx documentation is: "In general, it is recommended to skip all non-command events
# to allow the default handling to take place. The command events are, however, normally not skipped as usually
# a single command such as a button click or menu item selection must only be processed by one handler."
def skipEventAndCall(handler):
	def wrapWithEventSkip(event):
		if event:
			event.Skip()
		return handler()
	return wrapWithEventSkip

outputProperties = [
	"description",
	"name",
	"placeholder",
	"presentationType",
	"role",
	"roleText"
]

inputProperties = [
	"location",
	"role",
	"windowClassName",
	"windowControlID"
]

class AddEntryDialog(wx.Dialog):

	def __init__(self, parent, title, properties):
		super().__init__(parent, title=title)
		mainSizer=wx.BoxSizer(wx.VERTICAL)
		sHelper = gui.guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)

		propertySizer = wx.BoxSizer(wx.HORIZONTAL)
		# Translators: This is the label for the edit field.
		propertyText = _("Property:")
		propertyLabel = wx.StaticText(self, label=propertyText)
		propertySizer.Add(propertyLabel, flag=wx.ALIGN_CENTER_VERTICAL)
		propertySizer.AddSpacer(gui.guiHelper.SPACE_BETWEEN_ASSOCIATED_CONTROL_HORIZONTAL)
		self.propertyCombo = wx.ComboBox(
			self,
			choices=properties,
			style=wx.CB_DROPDOWN
		)
		propertySizer.Add(self.propertyCombo)
		sHelper.addItem(propertySizer)

		sHelper.addDialogDismissButtons(self.CreateButtonSizer(wx.OK | wx.CANCEL))

		mainSizer.Add(sHelper.sizer, border=gui.guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL)
		mainSizer.Fit(self)
		self.SetSizer(mainSizer)
		self.propertyCombo.SetFocus()
		self.CentreOnScreen()

class InputPanel(wx.Panel):

	def __init__(self, parent, definition, obj=None):
		if not isinstance(definition,dict):
			raise ValueError("Invalid definition provided: %s"%definition)
		self.definition = definition
		self.input = list(definition['input'].items())
		self.functions = list(definition['functions'].items())
		super().__init__(parent, id=wx.ID_ANY)
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
		self.inputList.InsertColumn(0, _("Property"))
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

		self.addButton.Bind(wx.EVT_BUTTON, skipEventAndCall(self.OnAddClick))
		self.editButton.Bind(wx.EVT_BUTTON, skipEventAndCall(self.OnEditClick))
		self.removeButton.Bind(wx.EVT_BUTTON, skipEventAndCall(self.OnRemoveClick))

		self.SetSizerAndFit(sizer.sizer)

	def getItemTextForList(self, item, column):
		entry = self.input[item]
		if column == 0:
			return entry[column]
		if column == 1:
			return ", ".join(entry[column])
		else:
			raise ValueError("Unknown column: %d" % column)

	def onListItemFocused(self, evt):
		# Update the editing controls to reflect the newly selected criterium.
		index = evt.Index
		self.editingItem = index
		self.editButton.Enable()
		self.removeButton.Enable()
		evt.Skip()

	def OnAddClick(self):
		with AddEntryDialog(
			self,
			title=_("Add filter property"),
			properties=inputProperties
		) as entryDialog:
			if entryDialog.ShowModal() != wx.ID_OK:
				return
			newAttr = entryDialog.propertyCombo.Value
			if not newAttr:
				return
		for index, (attr, val) in enumerate(self.input):
			if newAttr == attr:
				# Translators: An error reported when adding an property that is already present.
				gui.messageBox(_(f'Property {newAttr!r} is already present.'),
					_("Error"), wx.OK | wx.ICON_ERROR)
				self.inputList.Select(index)
				self.inputList.Focus(index)
				self.inputList.SetFocus()
				return
		self.input.append((newAttr, []))
		self.inputList.ItemCount = len(self.input)
		index = self.inputList.ItemCount - 1
		self.inputList.Select(index)
		self.inputList.Focus(index)
		# We don't get a new focus event with the new index.
		self.inputList.sendListItemFocusedEvent(index)
		self.inputList.SetFocus()

	def OnEditClick(self):
		return

	def OnRemoveClick(self):
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

class OutputPanel(wx.Panel):

	def __init__(self, parent, definition, obj=None):
		if not isinstance(definition,dict):
			raise ValueError("Invalid definition provided: %s"%definition)
		self.output = list(definition['output'].items())
		super().__init__(parent, id=wx.ID_ANY)
		sizer = gui.guiHelper.BoxSizerHelper(self, orientation=wx.HORIZONTAL)
		# Translators: The label for output list.
		outputText = _("&Property changes:")
		self.outputList = sizer.addLabeledControl(
			outputText,
			gui.nvdaControls.AutoWidthColumnListCtrl,
			autoSizeColumn=1,
			itemTextCallable=self.getItemTextForList,
			style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_VIRTUAL
		)
		self.outputList.ItemCount = len(self.output)
		# Translators: The label for a column in output list used to identify an entry.
		self.outputList.InsertColumn(0, _("Property"))
		# Translators: The label for a column in output list used to identify an item's value.
		self.outputList.InsertColumn(1, _("Value"))
		self.outputList.Bind(wx.EVT_LIST_ITEM_FOCUSED, self.onListItemFocused)

		# Translators: The label for the group of controls to change an item.
		changeItemText = _("Change output value")
		changeItemHelper = sizer.addItem(gui.guiHelper.BoxSizerHelper(self, sizer=wx.StaticBoxSizer(wx.StaticBox(self, label=changeItemText), wx.VERTICAL)))
		propertySizer = wx.BoxSizer(wx.HORIZONTAL)
		# Translators: The label for the edit field to change the property of an item.
		propertyText = _("Output &property")
		propertyLabel = wx.StaticText(self, label=propertyText)
		propertySizer.Add(propertyLabel, flag=wx.ALIGN_CENTER_VERTICAL)
		propertySizer.AddSpacer(gui.guiHelper.SPACE_BETWEEN_ASSOCIATED_CONTROL_HORIZONTAL)
		self.propertyCombo = wx.ComboBox(
			self,
			choices=outputProperties,
			style=wx.CB_DROPDOWN
		)
		propertySizer.Add(self.propertyCombo)
		changeItemHelper.addItem(propertySizer)

		self.propertyCombo.Bind(wx.EVT_TEXT, skipEventAndCall(self.onItemEdited))

		# Translators: The label for the edit field to change the value of a criterium.
		valueText = _("Output &value")
		self.valueEdit = changeItemHelper.addLabeledControl(valueText, wx.TextCtrl)
		self.valueEdit.Bind(wx.EVT_TEXT, skipEventAndCall(self.onItemEdited))

		# disable controls until an item is selected
		self.propertyCombo.Disable()
		self.valueEdit.Disable()

		self.editingItem = None

		bHelper = sizer.addItem(gui.guiHelper.ButtonHelper(orientation=wx.HORIZONTAL))
		# Translators: The label for a button to add a new entry.
		self.addButton = bHelper.addButton(self, label=_("&Add"))
		# Translators: The label for a button to remove an entry.
		self.removeButton = bHelper.addButton(self, label=_("Re&move"))
		self.removeButton.Disable()

		self.addButton.Bind(wx.EVT_BUTTON, skipEventAndCall(self.OnAddClick))
		self.removeButton.Bind(wx.EVT_BUTTON, skipEventAndCall(self.OnRemoveClick))


		self.SetSizerAndFit(sizer.sizer)

	def getItemTextForList(self, item, column):
		entry = self.output[item]
		return entry[column]

	def onItemEdited(self):
		if self.editingItem is not None:
			# Update the entry the user was just editing.
			entry = self.output[self.editingItem]
			property = self.propertyCombo.Value
			val = self.valueEdit.Value
			self.output[self.editingItem] = (property, val)

	def onListItemFocused(self, evt):
		# Update the editing controls to reflect the newly selected criterium.
		index = evt.Index
		self.editingItem = index
		entry = self.output[index]
		attr, val = entry
		self.propertyCombo.ChangeValue(attr)
		self.valueEdit.ChangeValue(val)
		self.removeButton.Enable()
		self.propertyCombo.Enable()
		self.valueEdit.Enable()
		evt.Skip()

	def OnAddClick(self):
		with AddEntryDialog(
			self,
			title=_("Add output property"),
			properties=outputProperties
		) as entryDialog:
			if entryDialog.ShowModal() != wx.ID_OK:
				return
			newAttr = entryDialog.propertyCombo.Value
			if not newAttr:
				return
		for index, (attr, val) in enumerate(self.output):
			if newAttr == attr:
				# Translators: An error reported when adding an property that is already present.
				gui.messageBox(_(f'Property {newAttr!r} is already present.'),
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

	def OnRemoveClick(self):
		index = self.outputList.GetFirstSelected()
		del self.output[index]
		self.outputList.ItemCount = len(self.output)
		# sometimes removing may result in an empty list.
		if not self.outputList.ItemCount:
			self.editingItem = None
			# disable the controls, since there are no items in the list.
			self.propertyCombo.Disable()
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

	def __init__(self, options={}, parent=None):
		if not isinstance(options,dict):
			raise ValueError("Invalid definition provided: %s"%definition)

class SingleDefinitionDialog(gui.SettingsDialog):

	def __init__(self,parent, obj=None):
		if not obj:
			raise ValueError("obj must be supplied")
		elif obj and not isinstance(obj,NVDAObjects.NVDAObject):
			raise ValueError("Invalid object provided")
		definition = getattr(obj, "_objEnhancerDefinition", {})
		if isinstance(definition, configobj.Section):
			self.title=_("Editing definition (%s)") % definition.name
		else:
			self.title=_("New definition")
		self.definition=definition
		self.obj=obj
		super(SingleDefinitionDialog,self).__init__(parent)

	def makeSettings(self, settingsSizer):
		settingsSizerHelper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		nameText=_("Identifying name")
		self.nameEdit = settingsSizerHelper.addLabeledControl(nameText, wx.TextCtrl)
		if isinstance(self.definition, configobj.Section):
			self.nameEdit.Value = self.definition.name
		if self.definition.get('input') is None:
			self.definition['input'] = {}
		if self.definition.get('functions') is None:
			self.definition['functions'] = {}
		self.inputPanel = InputPanel(parent=self,definition=self.definition,obj=self.obj)
		settingsSizerHelper.addItem(self.inputPanel)
		if self.definition.get('output') is None:
			self.definition['output']={}
		self.outputPanel=OutputPanel(parent=self,definition=self.definition,obj=self.obj)
		settingsSizerHelper.addItem(self.outputPanel)

	def postInit(self):
		self.nameEdit.SetFocus()
