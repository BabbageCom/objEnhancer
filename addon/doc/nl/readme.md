# Object Enhancer
* Author: Babbage B.V. <info@babbage.com>

Object Enhancer stelt je in staat om aan te passen hoe NVDA objecten op het scherm uitspreekt.
Dit kan gedaan worden met een intuïtieve interface.
Je kunt de add-on gebruiken om labels van objecten te veranderen, maar afhankelijk van hoe je de add-on gebruikt, kun je veel meer zaken aan objecten wijzigen.

Wijzigingen in een object worden opgeslagen in een definitie.
Een definitie bevat:

* Criteria die moeten gelden om de definitie te laten gelden
* Attribuutwijzigingen die worden toegepast op elk object dat overeenkomt met de definitie
* Optionele relaties met andere definities. Een definitie kan criteria van andere definities overnemen

## Je eigen definities aanmaken
Object Enhancer has a graphical interface to create new and edit existing defintions.

To create a new definition for the current navigator object, press NVDA+control+tab. This will open the new definition dialog when no definition was found for the current object, and edits the existing definition if there is a definition to edit.

NVDA+control+shift+tab opens the main dialog of the add-on that allows you to look up existing definitions and edit existing ones.

Note that if you want to create a definition quickly, you are strongly advised to create a new definition using NVDA+control+tab, as that allows you to use some of the attributes of the object automatically.
For example, when you press this shortcut when the current navigator object is a list item, you can automatically add the current name, role or location to the definition.

### Creating or editing a definition
The new/edit definition dialog consists of the following items:

#### Definition name
An unique name for your definition that is used for you to recognize it later on, as well as to link it to other definition when necessary.

#### Filter criteria:
These are the criteria to use for the definition to apply. You can filter on attributes/properties of an object.

To add a new criterion, press add. You can choose from the list of Relevant object attributes, or prrovide one yourself. For example, you could choose the windowControlID from the list of relevant attributes, which will prepopulate the attribute and value edit controls. Alternatively, if you want to match on an object with IAccessibleRole = 10 (ROLE_SYSTEM_CLIENT), you can do so manually.

You can also edit current filter criteria or add an extra value to filter on, if you want to match on an object with a windowControlID of either 15 or 16, for example.

#### Attribute changes
In the list with attribute changes, you can specify what attributes of the object have to be changed. In most cases, you probably want to change the name or description attributes.

#### Inherrit settings from definition / Definition is abstract
This combo box and check box allow you to set a relationship between several definitions.

Imagine the case where you need to label several buttons in one application. All buttons have a windowClassName of magicButton. You can create a definition that has windowClass=magicButton, and check the check box Definition is abstract, don't use it directly. In subsequent definitions, you can Inherrit settings from the magicButton definition, which will let the new definition behave as were windowClassName=magicButton specified as filter criterion.

#### Treat object location criteria as absolute screen coordinat
When this option is enabled, location criteria from the criteria section are parsed like all other properties. This means that, if you define location = (1, 2, 3, 4), every object without this absolute location will fail to match.

However, when this option is disabled, it wil have a major effect on object definitions with more than one location property match. The provided location properties, usually the location of the object itself and the location of one of its ancestors or siblings, will be compared, and it will be assumed that the distance between the provided top left corners will be the same across screen resizes. Consider the following definition snippet:

```
[example1]
	[[input]]
		location = [(248, 611, 869, 82)]
		parent.parent.location = [(245, 399, 875, 297)]
```

This input definition is based on the unmaximized state of an application. As soon as the application is maximized, the definition should be different, so the definition won't match to the object anymore:

```
[example2]
	[[input]]
		location = [(11, 582, 1344, 101)]
		parent.parent.location = [(8, 370, 1350, 316)]
```

When the absolute locations option is disabled, the first definition above will still match in the case that the object properties are equal to the second definition, allowing the second definition to be omited. The following logic is used:

* When an object gains focus or becomes navigator object, the definitions are evaluated.
* When location properties are defined, the difference between the defined locations and actual locations are calculated
* When multiple locations are defined, such as "location" and 'parent.parent.location", the logic assumes that the top left coordinate differences for the provided location rectangles are all the same

So, this sounds overwhelmingly complicated. Let's use the examples provided above to make things clearer.

* Example 1:
	+ defined location = (248, 611, 869, 82)
	+ actual location = (248, 611, 869, 82)
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

If you still don't get it, please consult the source code of this add-on. Please note that disabling this option can create false positives if not used correctly. You should always give preference to other unique object properties if there are any. This logic is just their for objects for which location based matching is the only way to go.

#### Definition error handling
This combo box allows you to decide what to do if there is an error while evaluating this definition:

* If set to continue, the error is ignored and evaluation continues
* If set to break, evaluation is aborted
* If set to raise, an error, a failing evaluation causes a traceback.

Please don't touch this option unless you're a developer.

## Technical details
Object definition files are parsed using the configobj module in unrepr mode.