from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
import sys
import transaction
import getopt

from AccessControl.SecurityManagement import getSecurityManager
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import setSecurityManager
from Products.CMFCore.utils import getToolByName
from Testing.makerequest import makerequest
from zope.component import getMultiAdapter
from zope.app.component.hooks import setSite
from plone.app.uuid.utils import uuidToObject

from nd.content.content.member import IMember
from nd.syndication.utils import sudo
from nd.syndication.utils import upgrade_logger
from nd.syndication.utils import update_payload

logger = logging.getLogger(__name__)


def usage():
    print """
This script will send digest notification to subscribers.
Options that are available:

    -s, --site=:    Choose an alternative id for your plone site - default 'nd'
    -d  --domain=:  Choose URL SERVER_NAME, defalut 'www.nd.edu'
    -h, --help:     Prints this message to stdout.
"""

def arg_handler():
    site_id = 'nd'
    domain = 'www.nd.edu'
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hd:s:',
                  ['help', 'site=', 'domain='])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit()
        elif opt in ('-s', '--site'):
            site_id = arg
        elif opt in ('-d', '--domain'):
            domain = arg
    return site_id, domain


# BBB Disabled in favor of "real time" notifications instead of digests.
# Kept in place in case we want to enable it later.
def create_digest(app):
    plone_site_id, domain = arg_handler()
    upgrade_logger(__name__, logging.DEBUG)
    email_counter = {}
    review_perm = 'Review portal content'
    app = makerequest(app, environ={'SERVER_NAME': domain})
    portal = app[plone_site_id]
    setSite(portal)
    mfromname = portal.email_from_name
    mfrom = portal.email_from_address
    notification_tool = getToolByName(portal, 'portal_syn_notification')
    acl_users = getToolByName(portal, 'acl_users')
    mailhost = getToolByName(portal, 'MailHost')
    membrane = getToolByName(portal, 'membrane_tool')
    all_user_ids = acl_users.getUserIds()
    membrane_brains = membrane(exact_getUserId=all_user_ids)
    membrane_users = {}
    for brain in membrane_brains:
        try:
            membrane_users[brain.getId] = IMember(brain.getObject())
        except (AttributeError,), err:
            logger.warning("Couldn't find membrane object for user: %s", err)

    managers = {
        'curr': getSecurityManager()
    }

    logger.info('Starting syndication digest creation.')

    for nav_root_uid, queue in notification_tool.queues.items():
        # Create view instance for each organization, so that state
        # is not preserved
        digest_notification = getMultiAdapter((portal, portal.REQUEST),
                                              name='digest_notification')
        # Create the enclosing (outer) message
        outer = MIMEMultipart()
        setSecurityManager(managers['curr'])
        organization = uuidToObject(nav_root_uid)
        org_path = '/'.join(organization.getPhysicalPath())
        subject = 'Pending review status daily digest ' \
                  'for College of Engineering'
        while queue:
            payload = queue.pull()
            if '/' in payload['object_uid']:
                # Plone site
                proxy = portal.unrestrictedTraverse(payload['object_uid'])
            else:
                proxy = sudo(uuidToObject, payload['object_uid'])
            update_payload(proxy, payload)
            logger.debug('Adding activity for %r: %r',
                         organization, proxy or 'Proxy deleted')
            digest_notification.update(payload)

        if not digest_notification.items_by_uid:
            logger.info('No activity for: %r', organization)
            continue
        # Create the HTML
        html = digest_notification()

        # Create the MIME wrapper
        html_part = MIMEText(html, _subtype='html', _charset='UTF-8')

        # Attach part
        outer.attach(html_part)

        # If we're processing a re-queued item with failed user_id's,
        # only notify those that failed
        payload.setdefault('failed_user_ids', set())
        if payload['failed_user_ids']:
            notify_users_ids = payload['failed_user_ids']
        else:
            notify_users_ids = all_user_ids

        for user_id in notify_users_ids:
            user = acl_users.getUserById(user_id)
            newSecurityManager(portal.REQUEST, user)
            can_review = user is not None and \
                         getSecurityManager().checkPermission(review_perm,
                                                              organization)
            receive_digest = user_id in membrane_users and \
                             membrane_users[user_id].receive_daily_digest
            user_email = user is not None and user.getProperty('email')
            # Retain this check for failed_user_ids, as the user's permissions
            # might have changed
            if can_review and receive_digest and user_email:
                msg = 'Notifying %s: can_review=%s, receive_daily_digest=%s, email=%s'
                logger.info(msg, user, can_review, receive_digest, user_email)
                try:
                    mailhost.send(outer,
                                  subject=subject,
                                  mfrom="%s <%s>" % (mfromname, mfrom),
                                  mto=user_email)
                    email_counter.setdefault(org_path, []).append(user_id)
                    if user_id in payload['failed_user_ids']:
                        payload['failed_user_ids'].remove(user_id)
                except Exception, e:
                    msg = 'Problem notifying user %r; re-queueing.'
                    logger.exception(msg, user)
                    payload['failed_user_ids'].add(user_id)
                    notification_tool.requeue_notification(organization,
                                                           payload)
                    continue

    logger.info('Syndication digest creation finished: %d message(s) sent (%s).',
                sum([len(user_ids)
                     for user_ids in email_counter.values()]),
                email_counter)

    transaction.commit()
