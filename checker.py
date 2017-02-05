"""
    Entry point of the program.

    Joe.
"""

# -------- Imports --------

try:
    import requests
    import Levenshtein
    import dill
    import time
    import signal
    import sys
    import re
    import hashlib
    import math
    import checker_classes
    import checker_data_management
    import checker_emailing
    import checker_logging
except ImportError as ex:
    print("\nSome modules can not be imported.\nError message: '%s'.\nTry to install missing modules with:\n\t$> pip install module-name\n" % ex)
    quit()

# -------- Global variables --------

RECORDS_FILENAME = "saved_records.data"
SCHEDULED_TIME_INTERVAL_SECONDS = 10 * 60

# -------- Functions --------

def cleanContent(content):

    _contentCleaned = content
    _replacingStrings = [[" ", ""],
                         ["\t", ""],
                         ["\n", ""],
                         ["\r", ""]]

    for _newReplacementePair in _replacingStrings:
        _contentCleaned = _contentCleaned.replace(_newReplacementePair[0], _newReplacementePair[1])

    return _contentCleaned


def generateChecksum(text):

    _cleanText = cleanContent(text)
    _newChecksum = (hashlib.md5(_cleanText.encode('utf-8'))).hexdigest()

    return _newChecksum


def checkContentHasChanged(elementToCheck, url_content):

    _elementPreviousContent = elementToCheck.getContent()
    if _elementPreviousContent == None:
        checker_logging.log("  There is no previous record of this element. Storing it now.")
        elementToCheck.setContent(url_content)
        elementToCheck.setLastChecksum(generateChecksum(url_content))
        return False
    else:
        checker_logging.log("  Comparing new content to previous version stored ...")

        # Compute the new checksum
        _newChecksum = generateChecksum(url_content)

        # If checksums do not match, proceed with analysis
        if not elementToCheck.getLastChecksum() == _newChecksum:
            checker_logging.log("  The hash of the new content does not match that of the saved. Analysing ...")
            # Save the new checksum
            elementToCheck.setLastChecksum(_newChecksum)

            # Compute the change ratio
            _previousContentCleaned = cleanContent(_elementPreviousContent)
            _newContentCleaned = cleanContent(url_content)
            _changeRatio = 100 * (1.0 - Levenshtein.ratio(_newContentCleaned, _previousContentCleaned))

            # Store the change ratio
            elementToCheck.setLastChangeAmount(_changeRatio)
            if _changeRatio > elementToCheck.getMinimumChangeThreshold():
                checker_logging.log("  Content has changed enough: %.1f [%%]. Threshold: %.1f [%%]." % (_changeRatio, elementToCheck.getMinimumChangeThreshold()))
                return True
            elif _changeRatio > 0:
                checker_logging.log("  Content has not changed enough. Change: %.1f [%%]. Threshold: %.1f [%%]." % (_changeRatio, elementToCheck.getMinimumChangeThreshold()))
        else:
            checker_logging.log("  Content has not changed at all.")

    return False


def checkElement(elementToCheck):

    _current_url = elementToCheck.getURL()
    checker_logging.log("  Trying to download content at '%s'." % (_current_url))
    try:
        _req = requests.get(_current_url)
    except Exception as ex:
        checker_logging.log("  ERROR: exception occured when retrieving URL '%s'. Exception message: '%s'" % (_current_url, ex))
        return None

    if not _req.status_code == 200:
        checker_logging.log("  ERROR: server status code was %d!" % (_req.status_code))
        return None

    if checkContentHasChanged(elementToCheck, _req.text):
        return True
    else:
        return False


def checkAll(elementsToCheck, elementsIndexes=None):

    _errorIDs = []
    _elementIDsThatChanged = []

    # If no list of indexes is specified, just check them all
    if elementsIndexes is None:
        elementsIndexes = checker_data_management.getAllIDs(elementsToCheck)

    checker_logging.log("*** Started check of %d elements ***" % (len(elementsIndexes)))
    errorsCount = 0
    _itemIndex = 0
    for _url_index in elementsIndexes:
        _itemIndex += 1

        # Do not try to use an index if it is invalid
        if _url_index < 0 or _url_index >= len(elementsToCheck):
            pass

        _currentElementToCheck = checker_data_management.getElementByID(elementsToCheck, _url_index)
        checker_logging.log("--Checking element %d of %d:" % (_itemIndex, len(elementsIndexes)))
        _checkResult = checkElement(_currentElementToCheck)
        # If it could not be checked
        if _checkResult is None:
            errorsCount += 1
            _errorIDs.append(_url_index)
        # If it was checked and it had changed
        elif _checkResult:
            # Mark this element to be notified as "changed"
            _elementIDsThatChanged.append(_url_index)

    if errorsCount == 0:
        checker_logging.log("*** Completed checking of %d elements successfully. ***" % (len(elementsIndexes)))
    else:
        checker_logging.log("*** Completed checking of %d elements WITH %d errors! ***" % (len(elementsIndexes), errorsCount))

    return [_errorIDs, _elementIDsThatChanged]


def performCompleteProcedure():

    checker_logging.log("++++ Complete procedure started ++++")

    # Try to load previous records of the elements
    _trackedElementsList = checker_data_management.loadRecordsFromFile(RECORDS_FILENAME)

    # Read the text file
    _elementsFromTextFile = checker_data_management.loadElementsFromTextFile("items_to_check.txt")

    # No way of continuing
    if _elementsFromTextFile is None:
        checker_logging.log("ERROR: no valid elements in the input file. Can not continue.")
        return

    checker_logging.log("Updating the complete list of elements ...")
    if _trackedElementsList is None:
        checker_logging.log("No previous elements exist. Using all %d new loaded elements." % len(_elementsFromTextFile))
        _trackedElementsList = _elementsFromTextFile
    else:
        checker_data_management.removeNonExistingElements(_trackedElementsList, _elementsFromTextFile)
        checker_data_management.addMissingElements(_trackedElementsList, _elementsFromTextFile)

    [_errorIndexes, _elementsChanged] = checkAll(_trackedElementsList)
    checker_data_management.saveRecordsToFile(_trackedElementsList, RECORDS_FILENAME)

    # The elements with errors should be tried again and if they still produce
    # errors, a notification should be issued. They should not be automatically
    # deleted in case the server is temporary down.
    _retryNeeded = False
    if len(_errorIndexes) > 0:
        _retryNeeded = True
        checker_logging.log("++Retry of elements that produced errors:")
        [_errorIndexes, _elementsChangedRetry] = checkAll(_trackedElementsList, _errorIndexes)
        # Add the additional elements that changed to the complete list
        for _newChanged in _elementsChangedRetry:
            _elementsChanged.append(_newChanged)

    # Notify of errors and changes if needed
    _emailNeeded = False
    _emailBodyText = ""
    if len(_errorIndexes) > 0:
        _emailNeeded = True
        checker_logging.log("--The following %d elements still produced an error after retry." % len(_errorIndexes))
        for _errorIndex in _errorIndexes:
            checker_logging.log("     ID-#%.4d, URL: '%s'." % (_errorIndex,
                                            checker_data_management.getElementByID(_trackedElementsList, _errorIndex).getURL()))
        checker_logging.log("--Notifying that %d elements were not accessible." % len(_errorIndexes))
        _errorElements = []
        for _errorIndex in _errorIndexes:
            _errorElements.append(checker_data_management.getElementByID(_trackedElementsList, _errorIndex))
        _emailErrorsText = checker_emailing.formatTextContentNotAccessible(_errorElements)
        _emailBodyText += _emailErrorsText + "\n"

    # Notify for all elements that changed
    if len(_elementsChanged) > 0:
        _emailNeeded = True
        checker_logging.log("--Notifying that %d elements have changed." % len(_elementsChanged))
        _changedElements = []
        for _elementIndex in _elementsChanged:
            _changedElements.append(checker_data_management.getElementByID(_trackedElementsList, _elementIndex))
        _emailChangesText = checker_emailing.formatTextContentChanged(_changedElements)
        _emailBodyText += _emailChangesText


#    checker_data_management._printAllData(_trackedElementsList)

    # Send joint email with all data
    if _emailNeeded:
        _emailBodyText += ("\nAutomatic message generated on: %s.\n" % time.strftime("%d/%m/%Y-%H:%M:%S"))
        checker_emailing.sendEmail(checker_emailing.EMAIL_SUBJECT_TEXT, _emailBodyText)

    checker_logging.log("++++ Complete procedure finished ++++")

    return _errorIndexes


# -------- Main to test --------

continueInLoop = True


def signal_handler(signal, frame):
    checker_logging.log("Control-C received. Stopping scheduled task.")
    global continueInLoop
    continueInLoop = False


def secondsToTimeStr(time):

    _hours = math.floor(time/(60.0*60.0))
    _minutes = math.floor((time - _hours*60*60)/60.0)
    _seconds = (time - _hours*60*60 - _minutes*60)

    _returnString = ""
    if not _hours == 0:
        _returnString += "%.2dh:%.2dm:%.2ds" % (_hours, _minutes, _seconds)
    elif not _minutes == 0:
        _returnString += "%.2dm:%.2ds" % (_minutes, _seconds)
    else:
        _returnString += "%.2ds" % _seconds

    return "%.2dh %.2dm %.2ds" % (_hours, _minutes, _seconds)


if __name__ == "__main__":

    checker_logging.log("*# -- Main script started -- #*")

    checker_logging.log("Wiring Control-C signal.")
    signal.signal(signal.SIGINT, signal_handler)

    while continueInLoop:
        _elementIndexesWithError = performCompleteProcedure()
        checker_logging.log("[...] Waiting %s until next execution ..." % secondsToTimeStr(SCHEDULED_TIME_INTERVAL_SECONDS))
        time.sleep(SCHEDULED_TIME_INTERVAL_SECONDS)

    checker_logging.log("*# -- Main script finished -- #*")
