#!/usr/bin/env python

from datetime import datetime
import time

from blackfynn import Blackfynn
from blackfynn import Collection
from mailer import ChopMailer

FILE_PREFIX = 'BOGUS_test_prefix'
EMAIL_SUBJ = 'Blackfynn: BioRC Failed Extract Digest'
EMAIL_SENDER = 'felmeistera@email.chop.edu'
EMAIL_RECIPIENTS = ['williamsrms@email.chop.edu', 'gonzalezak@email.chop.edu']
EMAIL_CCS = ['felmeistera@email.chop.edu']

def main():
    digest = assemble_digest()
    send_report()

def assemble_digest():
    report = []
    report.append("<h2>Blackfynn: BioRC Failed Extract Digest</h2>")
    bf = Blackfynn()
    root = bf.get('N:collection:4fec4882-925c-4328-bbfd-d1de953ba225')
    for bucket in root.items:
        report.append(bucket_digest(bucket))
    send_report(report)

def bucket_digest(bucket):
    report.append(bucket.name + ":<br />")
    if bucket.items:
        report.append("<ul>")
        for extract in bucket.items:
            report.append("<li>" + extract.name + "</li>")
        report.append("</ul>")
    report.append("<br /><br />")

def send_report(report):
    mailer = ChopMailer()
    mailer.set_subject(EMAIL_SUBJ)
    mailer.set_sender(EMAIL_SENDER)
    mailer.set_recipient(EMAIL_RECIPIENTS)
    mailer.set_cc(EMAIL_CCS)
    body = ''.join(report)
    mailer.set_body(body)
    mailer.send()

if __name__ == '__main__':
    main()
