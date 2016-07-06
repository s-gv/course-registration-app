import smtplib


def send_email(from_address, to_address, subject, message):
    msg = 'From: %s\nTo: %s\nSubject: %s\n%s' % (from_address, to_address, subject, message)
    try:
        smtp_connection = smtplib.SMTP('www.ece.iisc.ernet.in', 25, timeout=5)
        smtp_connection.sendmail(from_address, [to_address], msg)
        smtp_connection.quit()
        return True
    except:
        pass
