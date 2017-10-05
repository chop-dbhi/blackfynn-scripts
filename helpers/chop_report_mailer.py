#!/usr/bin/env python
# chop_report_mailer.py
# chop mailer for blackfynn notifications

"""
Usage: collection_watcher.py --collection=<collection_id> --threshold=<hours> --notify=<email>
"""

from datetime import datetime
import time
from docopt import docopt

from blackfynn import Blackfynn
from blackfynn import Collection

from mailer import ChopMailer

# TODO: Consider allowing the following to be configured in config.yaml/settings
FILE_PREFIX = 'BOGUS_test_prefix'
EMAIL_SUBJ = 'TEST Blackfynn collection email'
EMAIL_SENDER = 'felmeistera@email.chop.edu'
EMAIL_RECIPIENTS = ['williamsrms@email.chop.edu',
                    'gonzalezak@email.chop.edu']
EMAIL_CCS = ['felmeistera@email.chop.edu']
# TODO: support external emails, including:           'chris@blackfynn.com']

###################################
# main():
def main():
    print "hello from main: calling bf_mail_test_one()..."
    bf_mail_test_one()
    print "goodbye from main: called bf_mail_test_one()..."


def bf_mail_test_one():
    print "DEBUG: hello from bf_mail_test_one..."
    arguments = docopt(__doc__)

    print "DEBUG: bf_mail_test_one... after args"
    bf = Blackfynn()
    print "DEBUG: bf_mail_test_one... bf client == {0}".format(bf)
    collection = bf.get(arguments['--collection'])
    current_timestamp = time.time() * 1000

    print "DEBUG: bf_mail_test_one... about to iterate on collection items..."
    for item in collection.items:
        print "DEBUG: bf_mail_test_one... iterating on item {0}...".format(item)
        milliseconds_old = current_timestamp - int(item.get_property('created').value)
        hours_old = (milliseconds_old / (1000*60*60)) % 24
        print "DEBUG: bf_mail_test_one... iterating on item {0} w/ hours old={1} of {2} threshold...".format(item, hours_old, int(arguments['--threshold']))
        if hours_old > int(arguments['--threshold']):
            print "DEBUG: sending notification"
            ###########################################
            # and mail it!
            mailer = ChopMailer()

            mailer.set_subject(EMAIL_SUBJ)
            # TODO: maybe attach something?
            # mailer.set_attachment(csv_to_attach)


            #######
            # Primary email sender, recipient and cc:
            #
            # From:
            mailer.set_sender(EMAIL_SENDER)
            #
            # To: & Cc:
            mailer.set_recipient(EMAIL_RECIPIENTS)
            mailer.set_cc(EMAIL_CCS)
            #######

            mailer.set_body("""
            Hello:<br><br>
            This is a placeholder for some future Blackfynn beef that is to come!
            Thank you,
            <br>
            Gladys, The Enterprise Informatics Group's Report Robot<br>
            <a href ="http://dbhi.chop.edu/"><i>CHOP's Department of Biomedical and Health Informatics</i></a><br>
            """)

            mailer.send()
            print('Report Generated and Sent.')

            ######################################

if __name__ == '__main__':
    main()
