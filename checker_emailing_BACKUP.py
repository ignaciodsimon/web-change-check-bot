import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import checker_logging

FROM_EMAIL_ADDRESS = "webpage.checker.bot@gmail.com"
FROM_EMAIL_PASSWORD = "skfjn290"
EMAIL_SERVER = "smtp.gmail.com"
EMAIL_PORT = 587
TO_EMAIL_ADDRESS = "ignaciodsimon@gmail.com"
EMAIL_SUBJECT_TEXT = "Status update from webpage-checker-bot"


def formatTextContentNotAccessible(elements):
    
    _bodyText = "The following URLs cannot be accessed:\n\n"
    for _element in elements:
        _bodyText += "    [ID: %d] %s\n" % (_element.getID(), _element.getURL())
    return _bodyText


def formatTextContentChanged(elements):
    
    _bodyText = "The content on the following URLs have changed:\n\n"
    for _element in elements:
        _bodyText += "    [ID: %d - Diff: %.1f%% - Th: %.1f%%] %s\n" % (_element.getID(),
                                                                        _element.getLastChangeAmount(),
                                                                        _element.getMinimumChangeThreshold(),
                                                                        _element.getURL())
    return _bodyText


def sendEmail(title, bodyText):

    try:
        checker_logging.log("Sending email with subject '%s' ..." % title)
        # Form message
        fromaddr = FROM_EMAIL_ADDRESS
        toaddr = TO_EMAIL_ADDRESS
        msg = MIMEMultipart()
        msg['From'] = fromaddr
        msg['To'] = toaddr
        msg['Subject'] = title
        body = bodyText
        msg.attach(MIMEText(body, 'plain'))

        # Send message
        server = smtplib.SMTP(EMAIL_SERVER, EMAIL_PORT)
        server.starttls()
        server.login(fromaddr, FROM_EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(fromaddr, toaddr, text)
        server.quit()
    
        checker_logging.log("Email (apparently) sent successfully.")
    except Exception as ex:
        checker_logging.log("ERROR: could not send an email. Exception message: '%s'." % ex)

