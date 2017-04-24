# Object Enhancer
* Version 2017.1
* Author: Leonard de Ruijter (Babbage B.V.) <leonard@babbage.com>

Object Enhancer allows you to change properties of NVDAObjects using configuration (INI) files. These files are stored under the "objEnhancer" folder in the NVDA configuration folder (usually "%appdata%\\nvda") and have the ".objdef.ini" file extension.

## Example: notepad
The following example changes the label of the Notepad text area and menu bar:

```
[randomIdentifier]
	[[input]]
		windowClassName = u'Edit'
	[options]]
		absoluteLocations = False
		raiseOutputErrors = True
		ignoreNonexistentAttributes = True
	[[output]]
		name = 'Notepad text field'

[anotherRandomIdentifierForMenuBar]
	[[input]]
		windowClassName = u'Notepad'
		role = 10
		parent.role = 1
		parent.parent.windowClassName = u'#32769'
	[[options]]
		absoluteLocations = False
		raiseOutputErrors = True
		ignoreNonexistentAttributes = True
	[[output]]
		name = 'Notepad menu bar'
```

To try this example, place the above snippet into a file called 'notepad.objdef.ini' in your 'objEnhancer' directory.

## Writing your own definitions
An Object Enhancer definition has the following syntax

```
[identifier] # Just a string, without quotes
	[input] # mandatory
		attribute = value # for example: location = (1,2,3,4,) or role = 4
	[options]] #optional
		absoluteLocations = False # Whether to parse provided locations as absolute (see below)
		raiseOutputErrors = True # Raise an error whenever it is not possible to set an object's attribute
		ignoreNonexistentAttributes = True # allow setting foo = bar on an object, even though the object does not have the foo attribute. If set to False, behavior depends on the value of raiseOutputErrors. If raiseOutputErrors is False, the attribute will be ignored. If True, an error is raised. Please note that the latter can result in many errors
	[output] #mandatory
		attribute = value # for example: name = 'label' or role = 8
```

For every object section, the input and output sections are mandatory and should contain one or more key/value pairs. Input and output definitions are python style, so you are allowed to use strings, lists, tuples, dictionaries, etc. Only the standard python namespace is supported though, so role = controlTypes.ROLE_UNKNOWN will raise a parse error for your definition file. Setting the options section is optional.