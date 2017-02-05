import time
import dill
import checker_logging
import checker_classes

DEFAULT_MINIMUM_THRESHOLD = 5.0


def _printAllData(elementsList):

    for _element in elementsList:
        checker_logging.log("-----")
        checker_logging.log("DEBUG:            ID: %d" % _element.getID())
        checker_logging.log("DEBUG:           URL: %s" % _element.getURL())
        checker_logging.log("DEBUG:     Threshold: %f" % _element.getMinimumChangeThreshold())
        checker_logging.log("DEBUG:   Last change: %s" % _element.getLastChangeAmount())
        checker_logging.log("DEBUG: Last checksum: %s" % _element.getLastChecksum())
        checker_logging.log("DEBUG:   Periodicity: %s" % _element.getPeriodicity())
    checker_logging.log("-----")


def loadElementsFromTextFile(filename):

    checker_logging.log("Loading elements from text file '%s' ..." % filename)
    _lines = []
    _thresholds = []
    try:
        # Read each line on the file
        with open(filename) as _file:
            _content = _file.readlines()
            for _newLine in _content:
                _newLine = _newLine.strip()
                if not _newLine == "":
                    if not _newLine[0] == "#":
                        _newLineParts = _newLine.split()
                        try:
                            _thresholds.append(float(_newLineParts[0]))
                            _lines.append(_newLineParts[1])
                        except:
                            pass
    except Exception as ex:
        checker_logging.log("ERROR: exception occured when trying to read file. Exception message: %s" % (ex))
        return None

    if len(_lines) == 0:
        checker_logging.log("No valid elements were found!")
        return None

    # LOG all loaded elements
    checker_logging.log("Loaded %d elements:" % len(_lines))
    for _index in range(len(_lines)):
        checker_logging.log("  %5.d: %s" % (_index + 1, _lines[_index]))

    # Create array of objects with the loaded elements
    _loadedElementsList = []
    for _index in range(len(_lines)):
        addNewElementByURL(_loadedElementsList,
                           url=_lines[_index],
                           minimumThreshold=_thresholds[_index])

    return _loadedElementsList


def saveRecordsToFile(dataToSave, filename):

    _objectToSave = {"saved-data" : dataToSave,
                     "saving-datetime" : time.strftime("%d/%m/%Y-%H:%M:%S")}
    try:
        checker_logging.log("Saving records to file '%s' ..." % filename)
        with open(filename, "wb") as _file:
            dill.dump(_objectToSave, _file)
        checker_logging.log("Records saved successfully.")
        return True
    except Exception as ex:
        checker_logging.log("ERROR: could not save records to file '%s'. Exception message: '%s'." % (filename, ex))
        return False


def addNewElementByURL(elementsList, url, minimumThreshold=None):

    if minimumThreshold is None:
        minimumThreshold = DEFAULT_MINIMUM_THRESHOLD

    _newObject = checker_classes.TrackedElement(minimumChangeThreshold=minimumThreshold)
    _newObject.setURL(url)
    _newObject.setID(len(elementsList))
    elementsList.append(_newObject)


def removeElement(elementsList, element):

    if checkIfElementExists(elementsList, element.getURL()):
        elementsList.remove(element)
        return True
    else:
        return False


def addNewElement(elementsList, newElement):

    newElement.setID(len(elementsList))
    elementsList.append(newElement)


def removeNonExistingElements(previousList, newList):
    """
        Removes from previousList the elements that do not appear in newList.
    """
    _removedElementsCounter = 0
    for _previousListElement in previousList:
        if not checkIfElementExists(newList, _previousListElement.getURL()):
            removeElement(previousList, _previousListElement)
            _removedElementsCounter += 1

    if _removedElementsCounter > 0:
        checker_logging.log("Removed %d elements from the complete list." % _removedElementsCounter)


def loadRecordsFromFile(filename):

    try:
        checker_logging.log("Loading records from file '%s' ..." % filename)
        with open(filename, "rb") as _file:
            _loadedData = dill.load(_file)
            checker_logging.log("Records loaded successfully. Date-time found: %s." % _loadedData
                .get("saving-datetime"))
            return _loadedData.get("saved-data")
    except Exception as ex:
        checker_logging.log("ERROR: could not load records from file '%s'. Exception message: '%s'." % (filename, ex))
        return None


def checkIfElementExists(elementsList, elementURL):

    _elementFound = False
    for _element in elementsList:
        if _element.getURL() == elementURL:
            _elementFound = True
            break

    return _elementFound


def getAllIDs(elementsList):

    _indexes = []
    for _element in elementsList:
        _indexes.append(_element.getID())
    return _indexes


def getElementByID(elementsList, ID):

    _foundElement = None
    for _element in elementsList:
        if _element.getID() == ID:
            _foundElement = _element
            break
    return _foundElement


def addMissingElements(completeList, newList):

    _newElementsCounter = 0
    for _newListElement in newList:
        _elementFound = False
        for _completeListElement in completeList:
            if _newListElement.getURL() == _completeListElement.getURL():
                _elementFound = True
                break
        if not _elementFound:
            _newElementsCounter += 1
            addNewElement(completeList, _newListElement)

    if _newElementsCounter > 0:
        checker_logging.log("Added %d new elements to the complete list." % _newElementsCounter)
    else:
        checker_logging.log("No new elements added to the complete list.")

