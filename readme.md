# Object Enhancer
* Version 2019.2
* Author: Leonard de Ruijter (Babbage B.V.) <leonard@babbage.com>

Object Enhancer allows you to change properties of NVDAObjects using configuration (INI) files. These files are stored under the "objEnhancer" folder in the NVDA configuration folder (usually "%appdata%\\nvda") and have the ".objdef.ini" file extension. Property mutation takes place when the object is loaded.

## Example: notepad
The following example changes the label of the Notepad text area and menu bar:

```
[randomIdentifier]
	[[input]]
		windowClassName = ['Edit']
	[[output]]
		name = 'Notepad text field'

[anotherRandomIdentifierForMenuBar]
	[[input]]
		windowClassName = ['Notepad']
		role = [10]
		parent.role = [1]
		parent.parent.windowClassName = ['#32769']
	[[output]]
		name = 'Notepad menu bar'
```

To try this example, place the above snippet into a file called 'notepad.objdef.ini' in your 'objEnhancer' directory.

## Writing your own definitions
An Object Enhancer definition has the following syntax

```
[identifier] # Just a string, without quotes
	[input]  # mandatory
		property = [value1, value2, ...]  # for example: location = [(1,2,3,4,)] or role = [4]
	absoluteLocations = True # Whether to parse provided locations as absolute (see below)
	[output] #mandatory
		property = value # for example: name = 'label' or role = 8
```

For every object section, the input and output sections should contain one or more key/value pairs. Input and output definitions are python style, so you are allowed to use strings, lists, tuples, dictionaries, etc. Only the standard python namespace is supported though, so role = controlTypes.ROLE_UNKNOWN will raise a parse error for your definition file. For output definitions, mutations are limited to only one object at once (i.e. "name = 'test'" is valid, "parent.name = 'test'" is not. However, for input, it is perfectly valid to use "parent.parent.next.children[3].location = (1,2,3,4,)".

### The absoluteLocations option
When the "absoluteLocations" option is set to True, location properties in input sections are parsed like all other properties. This means that, if you define "location = (1,2,3,4)" in an input section, every object without this absolute location will fail to match.

However, when this option is False, it wil have a major effect on object definitions with more than one location property in its input section. The provided location properties, usually the location of the object itself and the location of one of its ancestors or siblings, will be compared, and it will be assumed that the distance between the provided top left corners will be the same across screen resizes. Consider the following snippet;

```
[example1]
	[[input]]
		location = (248, 611, 869, 82)
		parent.parent.location = (245, 399, 875, 297)
```

This input definition is based on the unmaximized state of an application. As soon as the application is maximized, the definition should be different, so the definition won't match to the object anymore:

```
[example2]
	[[input]]
		location = (11, 582, 1344, 101)
		parent.parent.location = (8, 370, 1350, 316)
```

When absoluteLocations is False, the first definition above will still match in the case that the object properties are equal to the second definition, allowing the second definition to be omited. The following logic is used:

* When an object gains focus or becomes navigator object, the defined input sections are evaluated
* When location properties are defined, the difference between the defined locations and actual locations are calculated
* When multiple locations are defined, such as "location" and 'parent.parent.location", the logic assumes that the top left coordinate differences for the provided location rectangles are all the same

So, this sounds overwhelmingly complicated. Let's use the examples provided above to make things clearer.

* Example 1:
	+ defined 		location = (248, 611, 869, 82)
	+ actual 		location = (248, 611, 869, 82)
	+ Top left coordinate differences for location: (248-248=0,611-611=0)
	+ defined parent.parent.location = (245, 399, 875, 297)
	+ actual parent.parent.location = (245, 399, 875, 297)
	+ Top left coordinate differences for parent.parent.location: (245-245=0,399-399=0)
	+ Top left coordinate differences for location and parent.parent.location are equal. No wonder, this is an absolute match
* Example 2:
	+ defined 		location = (248, 611, 869, 82)
	+ actual location = (11, 582, 1344, 101)
	+ Top left coordinate differences for location: (248-11=237,611-582=29)
	+ defined parent.parent.location = (245, 399, 875, 297)
	+ actual parent.parent.location = (8, 370, 1350, 316)
	+ Top left coordinate differences for location: (245-8=237,399-370=29)
	+ Top left coordinate differences for location and parent.parent.location are equal

If you still don't get it, please consult the source code of this add-on. Please note that setting absoluteLocations to False can create false positives if not used correctly. You should always give preference to other unique object properties if there are any. This logic is just their for objects for which location based matching is the only way to go.

## Technical details
Object definition files are parsed using the configobj module in unrepr mode.