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
Object Enhancer heeft een grafische interface om nieuwe definities te maken en bestaande definities te bewerken.

Om een ​​nieuwe definitie voor het huidige navigatorobject te maken, druk je op NVDA + control + tab. Hiermee wordt het nieuwe definitie dialoogvenster geopend als er geen definitie is gevonden voor het huidige object, en wordt de bestaande definitie bewerkt als er een definitie is om te bewerken.

NVDA+control+shift+tab opent het hoofddialoogvenster van de add-on waarmee je bestaande definities kunt opzoeken en bestaande definities kunt bewerken.

Houd er rekening mee dat wanner je snel een definitie wilt maken, je dat het beste kunt doen met NVDA+control+tab, omdat je daarmee bepaalde eigenschappen van het object automatisch kunt laten overnemen.
Wanneer je bijvoorbeeld op deze sneltoets drukt wanneer het huidige navigatorobject een lijstitem is, kun je automatisch de huidige naam, rol of locatie aan de definitie toevoegen.

### Een definitie maken of bewerken
Het dialoogvenster Nieuwe definitie / definitie bewerken bestaat uit de volgende items:

#### Definitienaam
Een unieke naam voor je definitie die je gebruikt om deze later te herkennen, en om deze indien nodig aan een andere definitie te koppelen.

#### Filtercriteria:
Dit zijn de criteria die moeten worden gebruikt om de definitie toe te passen. Je kunt filteren op attributen / eigenschappen van een object.

Druk op toevoegen om een ​​nieuw criterium toe te voegen.
Je kunt kiezen uit de lijst met relevante objectattributen of zelf een attribuut opgeven.
Je kunt bijvoorbeeld de optie windowControlID kiezen uit de lijst met attributen, waarna de invoervelden voor attribuut en waarde automatisch worden ingevuld.
Wanneer je bijvoorbeeld wilt matchen op een object met IAccessibleRole = 10 (ROLE_SYSTEM_CLIENT), kun je dit ook handmatig doen.

Je kunt ook de huidige filtercriteria bewerken of een extra waarde toevoegen om op te filteren, wanneer je op een object wilt matchen dat bijv. de waarde 15 of 16 heeft voor windowControlID.

#### Attribuutwijzigingen
In de lijst met attribuutwijzigingen kun je opgeven welke kenmerken van het object moeten worden gewijzigd. In de meeste gevallen wil je waarschijnlijk de naam (name) of beschrijving (description) wijzigen.

#### Instellingen overerven van definitie / Definitie is abstract
Met deze vervolgkeuezelijst en dit selectievakje kun je een relatie tussen verschillende definities instellen.

Stel je voor dat je meerdere knoppen in één applicatie moet labelen.
Alle knoppen hebben een windowClassName van magicButton.
Je kunt een definitie maken met windowClass = magicButton en het selectievakje Definitie is abstract, gebruik deze niet rechtstreeks aanvinken.
In volgende definities kun je instellingen overerven uit de definitie van magicButton, waardoor de nieuwe definitie zich zal gedragen alsof windowClassName = magicButton is opgegeven als filtercriterium.

#### Behandel criteria voor objectlocatie als absolute schermcoördinaten
Wanneer deze optie is ingeschakeld, worden locatiecriteria uit de criteriasectie behandeld zoals alle andere attributen. Dit betekent dat als je locaton = (1, 2, 3, 4) definieert, elk object zonder deze absolute locatie niet overeenkomt.

Als deze optie echter is uitgeschakeld, heeft dit een groot effect op objectdefinities met meer dan één locatie.
Voor meer details verwijzen we je naar de engelse documentatie.

#### Definitiefoutafhandeling
Met deze vervolgkeuzelijst kun je beslissen wat er moet gebeuren als er een fout optreedt bij het evalueren van deze definitie:

* Indien ingesteld op continue, wordt de fout genegeerd en gaat de evaluatie verder
* Indien ingesteld op break, wordt de evaluatie afgebroken
* Indien ingesteld op raise, veroorzaakt een falende evaluatie een traceback.

Pas deze optie niet aan tenzij je weet wat je doet, bijv. omdat je een NVDA- of Python-ontwikkelaar bent.
