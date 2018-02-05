# :coding: utf-8
# :copyright: Copyright (c) 2015 ftrack
import os
import sys
import threading
import logging
import datetime
import json
import time
import getpass
import uuid
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.MIMEText import MIMEText
from smtplib import SMTP

import ftrack
#from docraptor import DocRaptor

def async(fn):
    '''Run *fn* asynchronously.'''
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
    return wrapper

def sendEmail(userId, subject, message, recipients=[], filename='',):
    sender = ftrack.User(userId).getEmail()
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['Reply-to'] = sender
    msg['To'] = ', '.join(recipients)

    # That is what u see if dont have an email reader:
    msg.preamble = 'Multipart massage.\n'

    # This is the textual part:
    part = MIMEText(message)
    msg.attach(part)

    filetype = os.path.splitext(filename)[-1]

    if filetype is not '':
        if filetype == '.pdf':
            # This is the binary part:
            part = MIMEApplication(open(filename,"rb").read(), "pdf", name="reviewsession.pdf")
            part.add_header('Content-Disposition', 'attachment', filename="reviewsession.pdf")
            msg.attach(part)
        elif filetype == '.html':
            f = file(filename)
            attachment = MIMEText(f.read())
            attachment.add_header('Content-Disposition', 'attachment', filename="reviewsession.html")
            msg.attach(attachment)

    # add any smtp server
    server = SMTP('smtp.gmail.com:587')
    server.ehlo()
    server.starttls()
    # log in with your credentials
    server.login(YOUR_USERNAME,YOUR_PASSWORD)
    server.sendmail(msg['From'], msg['To'], msg.as_string())
    server.quit()

def getEntity(entityType=None, entityId=None):
    if entityType is None or entityId is None:
        return None
    return ftrack.ReviewSession(entityId)

def getPath(entityType=None, entity=None):
    parents=[]
    path = ''
    try:
        parents = entity.getParents()
    except:
        pass
    for i in parents[:-1]:
        path = (i.getName()) + " / " + path
    return path

def getEntityPath(entityType=None, entity=None):
    path=''
    parents=[]
    try:
        parents = entity.getParents()
    except:
        pass
    for i in parents:
        path = (i.getName()) + " / " + path
    path='  **' + path + entity.get('name').strip() + '**  *(' + (entityType if entityType != 'show' else 'project') + ')*'
    return path

def getEntityChildren(entityType=None, entity=None):
    '''Get all children for Review Session'''
    reviewEntities = entity.reviewSessionObjects()
    lst = []
    for i in reviewEntities:
        v = ftrack.AssetVersion(id=i.get('version_id'))
        lst.append((v,i))#getId version_id
    return lst

def getName(entityType=None, entity=None):
    if entityType != 'reviewsession':
        return xstr(entity.get('name'))
    else:
        return xstr(entity.getParent().get('name'))

def getDescription(entityType=None, entity=None):
    if entityType != 'reviewsession':
        return xstr(entity.getDescription()).encode("utf-8")
    else:
        return xstr(entity.getComment()).encode("utf-8")

def xstr(s):
    try:
        if s is None:
            return ''
        return s
    except:
        return ''

@async
def create(userId=None, entityType=None, entity=None, values=None):
    return createPDF(userId=userId,entityType=entityType, entity=entity, values=values)

def createPDF(userId=None, entityType=None, entity=None, values=None):
    description = u'Review summary'
    job = ftrack.createJob(
        description=description,
        status='running',
        user=userId
    )
    email = bool(values['email'])
    subject = values['subject']
    message = values['message']
    #replace {session} with session name
    subject = subject.replace("{session}",entity.get('name'))
    message = message.replace("{session}",entity.get('name'))

    try:
        html = "\
            <html>\
                <head>\
                    <style media='all'>\
                        @page { padding: 0pt}\
                        @page { margin: 0pt; }\
                        @page { size: A4}\
                        img { page-break-inside: avoid; }\
                        .break { clear:both; page-break-after:always; }\
                        td, th { page-break-inside: avoid; word-wrap: break-word; }\
                    </style>\
                    <link rel='stylesheet' href='https://maxcdn.bootstrapcdn.com/bootstrap/3.3.2/css/bootstrap.min.css' media='all'>\
                    <link rel='stylesheet' href='https://maxcdn.bootstrapcdn.com/bootstrap/3.3.2/css/bootstrap-theme.min.css' media='all'>\
                </head>\
            <body>\
                <div class='jumbotron' style='padding:20px; padding-top;0px; margin-bottom:0px'>\
                    <h1>" + entity.get('name') + "</h1>\
                    <p>" + entity.get('description') + "</p>\
                    <div class='media' style='margin-top:5px; margin-bottom: 5px'>\
                        <div class='media-left'>\
                            <img width='40px' src='"+xstr(ftrack.User(entity.get('created_by')).getThumbnail()) + "' class='media-object img-circle' style='width:40px;'>\
                        </div>\
                        <div class='media-body text-muted'>\
                            Created by " + ftrack.User(entity.get('created_by')).getName() + "<br/>\
                            " + str(entity.get('created_at').strftime('%A %d, %Y')) +  "\
                        </div>\
                    </div>\
                </div>\
                <table class='table table-striped' style='' >\
                    <tr>\
                        <th style='min-width:3px; max-width:3px; width:3px'>#</th>\
                        <th>Media information</th>\
                        <th>Comments</th>\
                    </tr>"
        lst = getEntityChildren(entityType=entityType, entity=entity)
        for i,reviewSessionObject in enumerate(lst):
            html = html + "\
                    <tr>\
                        <td class=''>\
                            <h4 class='text-muted' style='margin-top:0px'>" + str(i+1) + "</h4>\
                        </td>\
                        <td style='width:250px'>\
                            <div class='thumbnail'>\
                                <img class='img-responsive' src='" + xstr(reviewSessionObject[0].getThumbnail()) + "'>\
                                <div class='caption'>\
                                    <small><strong>" + getName(entityType=entityType, entity=reviewSessionObject[0]) +"</strong></small>\
                                    <p class='text-muted small'>" + getPath(entityType=entityType, entity=reviewSessionObject[0]) + "</p>\
                                    <p>\
                                        <div style='margin-top:10px'>\
                                            <span class='text-success glyphicon glyphicon-thumbs-up' style='padding-right:5px' aria-hidden='true'></span><strong><span style='padding-right:10px'>0</span></strong><span class='text-danger glyphicon glyphicon-thumbs-down' style='padding-right:5px' aria-hidden='true'></span><strong>0</strong>\
                                        </div>\
                                    </p>\
                                </div>\
                            </div>\
                        </td>\
                        <td style=''>\
                            <small>\
                                <ul class='media-list'>"
            notes = reviewSessionObject[1].getNotes()
            if not len(notes):
                html= html + "\
                                    <li class='media' style='max-width:430px;'>\
                                        <p class='lead text-muted text-center' style='padding-top:60px'>\
                                            Bummer, there are no comments here!\
                                        </p>\
                                    </li>"
            for note in notes:
                html = html + "\
                                    <li class='media' style='max-width:430px;'>\
                                        <div class='media-left'>\
                                            <img src='https://www.ftrack.com/wp-content/uploads/haz2.png' class='media-object img-circle' style='width:40px'>\
                                        </div>\
                                        <div class='media-body'>\
                                            <h4 class='media-heading'>\
                                                Collaborator\
                                            </h4>\
                                            <small class='text-muted'>" + str(note.getDate().strftime('%I:%M%p, %A %d, %Y')) + "</small>\
                                            <p>" + note.getText() + "</p>"
                frame = note.getMeta('reviewFrame')
                if frame is not None:
                    html = html + "\
                                            <p><span class='label label-primary'>Frame " + str(json.loads(frame)['number']) + "</span></p>"
                attachments = note.getAttachments()
                for a in attachments:
                    html = html + "\
                                            <img src='" + a.getURL() + "' class='' style='max-width:120px; margin-bottom:5px'>"
                replies = note.getNotes()
                for reply in replies:
                    html = html + "\
                                            <div class='media' style='max-width:380px;'>\
                                                <div class='media-left'>\
                                                    <img src='https://www.ftrack.com/wp-content/uploads/fl.png' class='media-object img-circle' style='width:40px'>\
                                                </div>\
                                                <div class='media-body'>\
                                                    <h4 class='media-heading'>\
                                                        Collaborator\
                                                    </h4>\
                                                    <small class='text-muted'>" + str(reply.getDate().strftime('%I:%M%p, %A %d, %Y')) + "</small>\
                                                    <p>" + reply.getText() + "</p>\
                                                </div>\
                                            </div>"
                html = html + "\
                                        </div>\
                                    </li>"
            html = html + "\
                                <br/>\
                                </ul>\
                            </small>\
                        </td>\
                    </tr>"
        html = html + "\
                    </table>\
                </body>\
                </html>"

        # html alternative to create PDF (see below)
        filename = "review-session-{0}.html".format(str(uuid.uuid1()))
        html_file= open(filename,"w")
        html_file.write(html.encode("utf-8"))
        html_file.close()

        # signup for docraptor (free trial) or use other PDF generator library
        # install docraptor with "pip install python-docraptor"

        # docraptor = DocRaptor(ADD YOUR API KEY HERE)
        # filename = "review-session-{0}.pdf".format(str(uuid.uuid1()))
        # resp = docraptor.create({
        #                             'document_content': html,
        #                             'document_type':'pdf',
        #                             'test': False,
        #                             'strict': 'none',
        #                             'async': True,
        #                             'prince_options': {'media': 'screen', 'insecure':False, 'input':'html'}
        #                             })

        # status_id = resp['status_id']

        # resp = docraptor.status(status_id)
        # while resp['status'] != 'completed':
        #     time.sleep(3)
        #     resp = docraptor.status(status_id)

        # f = open(filename, "w+b")
        # f.write(docraptor.download(resp['download_key']).content)
        # f.seek(0)

        job.createAttachment(f, fileName=filename)
        job.setStatus('done')

        if email:
            sendEmail(userId=userId, subject=subject, message=message, recipients = [ftrack.User(userId).getEmail()], filename = "filename")

        os.remove(filename)
    except:
        job.setStatus('failed')

class ReviewSummary(ftrack.Action):
    '''Generate review session summary PDF.'''

    label = 'Review Summary'
    identifier = 'com.ftrack.reviewsummary'

    def register(self):
        '''Register action.'''
        ftrack.EVENT_HUB.subscribe(
            'topic=ftrack.action.discover and source.user.username={0}'.format(
                getpass.getuser()
            ),
            self.discover
        )

        ftrack.EVENT_HUB.subscribe(
            'topic=ftrack.action.launch and source.user.username={0} '
            'and data.actionIdentifier={1}'.format(
                getpass.getuser(), self.identifier
            ),
            self.launch
        )

    def discover(self, event):
        '''Return action config if triggered on a single selection.'''
        data = event['data']

        # If selection contains more than one item return early since
        # this action can only handle a single version.
        selection = data.get('selection', [])
        self.logger.info('Got selection: {0}'.format(selection))
        if len(selection) != 1 or selection[0]['entityType'] != 'reviewsession':
            return

        return {
            'items': [{
                'label': self.label,
                'actionIdentifier': self.identifier,
                'icon':"https://www.ftrack.com/wp-content/uploads/googledocs.png"
            }]
        }

    def launch(self, event):
        userId = event['source']['user']['id']
        data = event['data']
        selection = data.get('selection', [])
        entityId = selection[0]['entityId']
        entityType = selection[0]['entityType']
        entity = getEntity(entityType=entityType, entityId=entityId)

        if 'values' in event['data']:
            # Do something with the values or return a new form.
            values = event['data']['values']
            ftrack.EVENT_HUB.publishReply(
                event,
                data={
                    'success': True,
                    'message': 'Action was successfull'
                }
            )
            create(userId=userId, entityType=entityType, entity=entity, values=values)
            return

        return {
            'items': [
                {
                    'type': 'label',
                    'value': 'Your selection: ' + getEntityPath(entityType=entityType,entity=entity)
                }, {
                    'type': 'label',
                    'value': '___'
                }, {
                    'label': 'Email PDF to collaborators',
                    'type': 'enumerator',
                    'name': 'email',
                    'value':'0',
                    'data': [
                    {
                    'label': 'No',
                    'value': '0'
                }, {
                    'label': 'Yes',
                    'value': '1'
                }
                ]
                },{
                    'label': 'Email subject',
                    'type': 'text',
                    'value': 'Review session notes - {session}',
                    'name': 'subject'
                },{
                    'label': 'Message',
                    'name': 'message',
                    'value': 'Hello,\nhere are the review notes for {{session}}.\n\nThank you,\n{0}'.format(ftrack.User(userId).getName()),
                    'type': 'textarea'
                }
            ]
        }


def register(registry, **kw):
    '''Register action. Called when used as an event plugin.'''
    logger = logging.getLogger(
        'com.ftrack.reviewsummary'
    )

    if registry is not ftrack.EVENT_HANDLERS:
        # Exit to avoid registering this plugin again.
        return

    # Validate that registry is an instance of ftrack.Registry. If not,
    # assume that register is being called from a new or incompatible API and
    # return without doing anything.
    if not isinstance(registry, ftrack.Registry):
        logger.debug(
            'Not subscribing plugin as passed argument {0!r} is not an '
            'ftrack.Registry instance.'.format(registry)
        )
        return

    action = ReviewSummary()
    action.register()


def main():
    '''Register action and listen for events.'''
    logging.basicConfig(level=logging.INFO)

    ftrack.setup()
    action = ReviewSummary()
    action.register()

    ftrack.EVENT_HUB.wait()


if __name__ == '__main__':
    main()
