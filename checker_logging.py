import time

OUTPUT_LOG_FILENAME = "log.txt"

def log(message):

    _textToLog = "[%s] %s" % (time.strftime("%d/%m/%Y-%H:%M:%S"), message)

    with open(OUTPUT_LOG_FILENAME, "a") as myfile:
        myfile.write(_textToLog + "\n")

    print(_textToLog)
