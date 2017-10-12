#!/usr/bin/env python

from blackfynn import Blackfynn
from mailer import ChopMailer

FILE_PREFIX = 'BOGUS_test_prefix'
EMAIL_SUBJ = 'Blackfynn: BioRC Failed Extract Digest'
EMAIL_SENDER = 'felmeistera@email.chop.edu'
EMAIL_RECIPIENTS = ['williamsrms@email.chop.edu', 'gonzalezak@email.chop.edu']
EMAIL_CCS = ['felmeistera@email.chop.edu']

def main():
    send_digest()

def send_digest():
    report = []
    report.append("<h2>Blackfynn: BioRC Failed Extract Digest</h2>")
    bf = Blackfynn()
    root = bf.get('N:collection:4fec4882-925c-4328-bbfd-d1de953ba225')
    for bucket in root.items:
        include_count = True if bucket.id == "N:collection:0e476218-ccb9-4c4d-bdb4-e72d0a0f88fd" else False
        bucket_digest(report, bucket, include_count)
    send_report(report)

def bucket_digest(report, bucket, include_count):
    report.append(bucket.name + ":<br />")
    if bucket.items:
        report.append("<ul>")
        for item in bucket.items:
            report.append("<li>")            
            report.append(item.name)
            if include_count:
                report.append(" (" + str(len(item.items)) + " pending)")
            report.append("</li>")
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
