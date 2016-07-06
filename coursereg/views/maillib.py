from coursereg import models
import smtplib
import logging

logger = logging.getLogger(__name__)

def send_email(from_address, to_addresses, subject, message):
    msg = 'From: %s\nTo: %s\nSubject: %s\n%s' % (from_address, ", ".join(to_addresses), subject, message)
    try:
        smtp_host = str(models.Config.objects.get(key="smtp_host").value)
        smtp_port = int(models.Config.objects.get(key="smtp_port").value)
        smtp_connection = smtplib.SMTP(smtp_host, smtp_port, timeout=5)
        smtp_connection.sendmail(from_address, to_addresses, msg)
        smtp_connection.quit()
        return True
    except Exception, e:
        logger.error('Unable to send e-mail to %s. Error: %s' % (", ".join(to_addresses), str(e)))
