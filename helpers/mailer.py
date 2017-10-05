import smtplib
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email import encoders

"""
NOTE: from github.research.chop.edu/dbhi/eig_reports/...., to be spawned as a stand-alone library.
TODO: add bcc support
"""


class ChopMailer(object):
    def __init__(self):
        self._sub = ''
        self._sender = 'felmeistera@email.chop.edu'
        self.recipients = ''
        self.ccers = ''
        self._smtp = 'mailrouter.chop.edu'
        self._attachment = None
        self._filelocation = None
        self._header = ""
        self._msg = MIMEMultipart('alternative')
        self._body = MIMEText(
            """
    Hello:<br>
    YOU ARE RECEIVING A TEST EMAIL, THIS IS A TEST, and ONLY A TEST!<br/>
    Your requested integrated data report is ready and has been attached.<br>
    If you have any questions please contact Alex Felmeister at felmeistera@email.chop.edu.<br><br>

    Thank you,
    <br>
    The Enterprise Informatics Group<br>
    <a href ="http://dbhi.chop.edu/"><i>The Department of Biomedical and Health Informatics </i></a><br>
    """, 'html')

    def set_header(self, header):
        self._header = header

    def set_recipient(self, recipients):
        """Takes email address as string or list of email addresses. MUST BE IN CHOP DOMAIN"""
        if type(recipients) == str:
            # leave as string for _msg header:
            self._msg['To'] = recipients
            # but put into list form for sendmail():
            self.recipients = recipients.split(",")
            if "@email.chop.edu" not in self.recipients:
                print("All recipients must be on the CHOP domain")
                exit()
        elif type(recipients) == list:
            # put as string for _msg header:
            self._msg['To'] = ", ".join(recipients)
            # and leave in list form for sendmail():
            self.recipients = recipients
            for r in self.recipients:
                if "@email.chop.edu" not in r:
                    print("All recipients must be on the CHOP domain")
                    exit(1)
       # TODO: add catchall else to throw exception for other unexpected types

    def set_subject(self, subject):
        """Use to set Subject. Default subject not set"""
        self._sub = '[SEND SECURE] ' + subject

    def set_body(self, body):
        """Use to overwrite body text with an html block"""
        self._body = MIMEText(body, 'html')

    def set_sender(self, sender):
        """Use to overwrite felmeistera@email.chop.edu"""
        self._sender = sender

    def set_cc(self, ccers):
        if type(ccers) == str:
            # leave as string for _msg header:
            self._msg['Cc'] = ccers
            # but put into list form for sendmail():
            self.ccers = ccers.split(",")
            if "@email.chop.edu" not in self.ccers:
                print("All cc: recipients must be on the CHOP domain")
                exit()
        elif type(ccers) == list:
            # put as string for _msg header:
            self._msg['Cc'] = ", ".join(ccers)
            # and leave in list form for sendmail():
            self.ccers = ccers
            for r in self.ccers:
                if "@email.chop.edu" not in r:
                    print("All cc: recipients must be on the CHOP domain")
                    exit(1)
       # TODO: add catchall else to throw exception for other unexpected types

    def set_attachment(self, filelocation):
        """Attach CSV file"""
        self._filelocation = filelocation
        with open(self._filelocation) as f:
            self._attachment = MIMEBase('application', 'csv')
            self._attachment.set_payload(f.read())
            self._attachment.add_header('Content-Disposition', 'attachment', filename=f.name)
            encoders.encode_base64(self._attachment)

    def send(self):
        """Send mail"""
        self._msg['Subject'] = self._sub
        self._msg['From'] = self._sender
        # Now in set_recipient(): self._msg['To'] = self.recipients
        if self._msg['Cc'] is None:
            self._msg['Cc'] = 'eigsupport@email.chop.edu'
        # Now in set_cc(): self._msg['Cc'] = self.ccers
        self._msg.attach(self._body)
        if self._attachment:
            self._msg.attach(self._attachment)
        main_engine = smtplib.SMTP(self._smtp)
        try:
            # combine recipients with ccers for all sendmail addresses:
            main_engine.sendmail(self._sender, self.recipients+self.ccers, self._msg.as_string())
            print("Message Send Successful")
        except:
            print('Message Failed')
