# Object Enhancer

#Copyright (C) 2017 Babbage B.V.

#This file is covered by the GNU General Public License.
#See the file COPYING for more details.

import wx
import gui
import configobj
import controlTypes
import addonHandler
addonHandler.initTranslation()

class CriteriaPanel(wx.Panel):

	def __init__(self, type, spec, parent=None, id=wx.ID_ANY):
		if type not in ("input","output"):
			raise ValueError("Invalid type provided: %s"%type)
		if not isinstance(spec,dict):
			raise ValueError("Invalid specification provided: %s"%spec)
		data=spec.get(type,{})
		super(CriteriaPanel, self).__init__(parent, id)
		self.data=data
		self.itemToDataMapping=[]
		sizer = gui.guiHelper.BoxSizerHelper(self, orientation=wx.HORIZONTAL)
		# Translators: The label for criteria list.
		typeText=_("input") if type=="input" else _("output")
		criteriaText = _("&%s criteria")%typeText.title()
		self.criteriaList = sizer.addLabeledControl(criteriaText, gui.nvdaControls.AutoWidthColumnListCtrl, autoSizeColumnIndex=0, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
		# Translators: The label for a column in criteria list used to identify a criterium.
		self.criteriaList.InsertColumn(0, _("Property"))
		# Translators: The label for a column in criteria list used to identify a criterium's value.
		self.criteriaList.InsertColumn(1, _("Value"))
		for attr,val in data.iteritems():
			item = self.criteriaList.Append((attr,val))
			self.itemToDataMapping.insert(item,attr)
		self.criteriaList.Bind(wx.EVT_LIST_ITEM_FOCUSED, self.onListItemFocused)

		# Translators: The label for the group of controls to change a criterium.
		changeCriteriumText = _("Change %s criterium")%typeText
		changeCriteriumHelper = sizer.addItem(gui.guiHelper.BoxSizerHelper(self, sizer=wx.StaticBoxSizer(wx.StaticBox(self, label=changeCriteriumText), wx.VERTICAL)))
		# Borrowed from gui.settingsDialogs.SpeechCriteriumsDialog.makeSettings
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

		# Translators: The label for the edit field to change the property of a criterium.
		propertyText = _("%s &property")%typeText
		self.propertyEdit = changeCriteriumHelper.addLabeledControl(propertyText, wx.TextCtrl)
		self.propertyEdit.Bind(wx.EVT_TEXT, skipEventAndCall(self.onCriteriumEdited))

		# Translators: The label for the edit field to change the value of a criterium.
		valueText = _("%s &value")%typeText
		self.valueEdit = changeCriteriumHelper.addLabeledControl(valueText, wx.TextCtrl)
		self.valueEdit.Bind(wx.EVT_TEXT, skipEventAndCall(self.onCriteriumEdited))

		# disable controls until an item is selected
		self.propertyEdit.Disable()
		self.valueEdit.Disable()
		
		bHelper = sizer.addItem(gui.guiHelper.ButtonHelper(orientation=wx.HORIZONTAL))
		# Translators: The label for a button to add a new criterium.
		addButton = bHelper.addButton(self, label=_("&Add"))
		# Translators: The label for a button to remove a criterium.
		self.removeButton = bHelper.addButton(self, label=_("Re&move"))
		self.removeButton.Disable()

		#self.addButton.Bind(wx.EVT_BUTTON, self.OnAddClick)
		self.removeButton.Bind(wx.EVT_BUTTON, self.OnRemoveClick)

		self.editIndex = -1

		self.SetSizerAndFit(sizer.sizer)

	def onCriteriumEdited(self):
		if self.editIndex is not -1:
			# Delete the criterium the user was just editing.
			del self.data[self.itemToDataMapping[self.editIndex]]
			attr = self.itemToDataMapping[self.editIndex]=self.propertyEdit.Value
			val = self.valueEdit.Value
			self.data[attr]=val
			self.criteriaList.SetStringItem(self.editIndex,0,attr)
			self.criteriaList.SetStringItem(self.editIndex,1,val)

	def onListItemFocused(self, evt):
		# Update the editing controls to reflect the newly selected criterium.
		index = evt.GetIndex()
		attr=self.itemToDataMapping[index]
		val = self.data[attr]
		self.editIndex = index
		self.propertyEdit.ChangeValue(attr)
		self.valueEdit.ChangeValue(val)
		self.removeButton.Enable()
		self.propertyEdit.Enable()
		self.valueEdit.Enable()
		evt.Skip()

	def OnAddClick(self, evt):
		with AddCriteriumDialog(self) as entryDialog:
			if entryDialog.ShowModal() != wx.ID_OK:
				return
			identifier = entryDialog.identifierTextCtrl.GetValue()
			if not identifier:
				return
		for index, criterium in enumerate(self.criteriums):
			if identifier == criterium.identifier:
				# Translators: An error reported in the Criterium Pronunciation dialog when adding a criterium that is already present.
				gui.messageBox(_('Criterium "%s" is already present.') % identifier,
					_("Error"), wx.OK | wx.ICON_ERROR)
				self.criteriumsList.Select(index)
				self.criteriumsList.Focus(index)
				self.criteriumsList.SetFocus()
				return
		addedCriterium = characterProcessing.SpeechCriterium(identifier)
		try:
			del self.pendingRemovals[identifier]
		except KeyError:
			pass
		addedCriterium.displayName = identifier
		addedCriterium.replacement = ""
		addedCriterium.level = characterProcessing.SYMLVL_ALL
		addedCriterium.preserve = characterProcessing.SYMPRES_NEVER
		self.criteriums.append(addedCriterium)
		item = self.criteriumsList.Append((addedCriterium.displayName,))
		self.updateListItem(item, addedCriterium)
		self.criteriumsList.Select(item)
		self.criteriumsList.Focus(item)
		self.criteriumsList.SetFocus()

	def OnRemoveClick(self, evt):
		index = self.criteriaList.GetFirstSelected()
		attr=self.itemToDataMapping.pop(index)
		del self.data[attr]
		self.criteriaList.DeleteItem(index)
		index = min(index, self.criteriaList.ItemCount - 1)
		self.criteriaList.Select(index)
		self.criteriaList.Focus(index)
		# We don't get a new focus event with the new index
		self.editIndex = index
		self.criteriaList.SetFocus()

