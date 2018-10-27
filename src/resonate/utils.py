import logging
import sys

from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import getSecurityManager
from AccessControl.SecurityManagement import setSecurityManager

from zope.component.hooks import getSite
from zope.container.interfaces import INameChooser

from Products.CMFCore.tests.base.security import OmnipotentUser as \
            CMFOmnipotentUser
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.WorkflowCore import WorkflowException

from Products.statusmessages.interfaces import IStatusMessage
from plone.app.layout.navigation.root import getNavigationRoot
from plone.app.event.dx import behaviors as event_behaviors

from Products.Archetypes.interfaces import referenceable
from Products.ATContentTypes.utils import DT2dt

from plone import api

from . import behaviors


class OmnipotentUser(CMFOmnipotentUser):
    """
    Super user to workaround issues when operating as the system user.

    Instancemanger has this class and tells us this:

      Adapted from Products.CMFCore.tests.base.security.  Using that
      exact code would give problems, because the site would be owned
      by 'all_powerful_Oz', not the usual admin user.  Going e.g. to
      the sharing tab of the front page would give TypeError:
      unsubscriptable object, because that 'all_powerful_Oz' is
      nowhere in acl_users.
    """

    def __init__(self, userid='admin'):
        self.id = userid

    def getId(self):
        return self.id

    getUserName = getId

    def getRolesInContext(self, object):
        return ('ContentAdmin', 'Manager')

    def has_role(self, roles):
        return True


def sudo(func, *args, **kwargs):
    """ Function to run another operation under a new security context
    """
    portal = getSite()
    origSecurityManager = getSecurityManager()
    origUserID = origSecurityManager.getUser().getId()
    newSecurityManager(
        None, OmnipotentUser(origUserID).__of__(portal.acl_users))

    try:
        result = func(*args, **kwargs)
    finally:
        setSecurityManager(origSecurityManager)

    return result


def upgrade_logger(logger_name, level,
                   fmt="%(asctime)s %(levelname)s - %(name)s - %(message)s"):
    # Force application logging level and log output to stdout for all
    # loggers
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    logger.propagate = False
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(fmt)
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def get_organizations_by_target(context, uids):
    members = getToolByName(context, 'portal_membership').getMembersFolder()
    portal_catalog = getToolByName(context, 'portal_catalog')
    uid_catalog = getToolByName(context, 'uid_catalog')
    home_folder_path = members is not None and '/'.join(
        members.getPhysicalPath())
    context_path = '/'.join(context.getPhysicalPath())

    organizations = [
        brain.getObject()
        for brain in uid_catalog(UID=uids)
    ]
    result = {}
    for organization in organizations:
        if organization is None:
            continue
        organization_path = getNavigationRoot(organization)
        if members is not None and context_path.startswith(home_folder_path):
            # Special-case the member's home folder, since it is not a
            # navigation root but we still want to be able to request
            # syndication to the containing portal
            pass
        elif organization_path == getNavigationRoot(context):
            # Always exclude the current organization
            continue
        targets = portal_catalog(
            path=organization_path,
            object_provides=behaviors.ISyndicationTarget.__identifier__)
        for target in targets:
            if getNavigationRoot(target.getObject()) == organization_path:
                result[organization] = target.getObject()

    return result


def sendEmailToMember(member, source, status, comment):
    status_messages = IStatusMessage(source.REQUEST)
    base_error_msg = "Unable to send syndication status notification: %s. "
    base_error_msg += "Please notify user manually."
    # set up from address and other portal-related vars
    urltool = getToolByName(source, "portal_url")
    portal = urltool.getPortalObject()
    portal_title = portal.title
    f_name = api.portal.get_registry_record('plone.email_from_name')
    f_addr = api.portal.get_registry_record('plone.email_from_address')
    if f_name and f_addr:
        mfrom = "\"%s\" <%s>" % (f_name, f_addr)
    else:
        # notify the user we were unable to make the message and send it
        msg = base_error_msg % "site from address and/or name not set"
        status_messages.add(msg, type=u'warning')
        return
    # to ensure proper encoding, is this actually needed?
    charset = portal.getProperty('email_charset')
    # set up message headers dependent on the member memberect information
    recip = member.getProperty('email')
    name = member.getProperty('fullname')

    msg_kw = {'portal_title': portal_title,
              'fullname': name,
              'source_url': source.absolute_url,
              'comment': comment,
              'status': status}
    template = '@@syndication_status_notification'
    try:
        message_template = source.restrictedTraverse(template)
    except NotFound as e:
        # notify the user that we were unable to notify by email
        msg = base_error_msg % "message template cannot be found"
        status_messages.add(msg, type=u'warning')
        return

    message = message_template(source, source.REQUEST, **msg_kw)
    subject = "Syndication Information for %s" % portal_title
    mailhost = getToolByName(source, 'MailHost')
    try:
        mailhost.send(message.strip(),
                      mto=recip,
                      mfrom=mfrom,
                      charset=charset,
                      subject=subject)
    except Exception as e:
        # naked try/excepts are bad, but I have no idea what exceptions might
        # be raised by sending the email, and the source is no help so far
        logger = logging.getLogger('sendEmailToMember')
        specific_problem = "mailhost error: %s" % str(e)
        msg = base_error_msg % specific_problem
        status_messages.add(msg, type=u'error')
        logger.exception('Error sending email; recipient: %s, from: %s',
                         recip, mfrom)
        return

    status_messages.add("Member notified of syndication change", type=u'info')


def update_payload(source, payload):
    """Update the given payload with current data for source
    (which could have been deleted since the payload was created)
    """
    if source is None:
        return payload
    payload['last_changed'] = source.modified()
    payload['object_title'] = source.title_or_id()
    wft = getToolByName(source, 'portal_workflow')
    nav_root_path = getNavigationRoot(source)
    nav_root = source.restrictedTraverse(nav_root_path)
    nav_root_uid = api.content.get_uuid(nav_root)
    state_changes = []
    try:
        review_state = wft.getInfoFor(source, 'review_state')
        state_title = wft.getTitleForStateOnType(review_state,
                                                 source.portal_type)
        state_changes.append(state_title)
        if payload['organization_uid'] == nav_root_uid:
            syndication_state = wft.getInfoFor(source, 'syndication_state')
            state_title = wft.getTitleForStateOnType(syndication_state,
                                                     source.portal_type)
        else:
            state_title = 'Content Moved'
        state_changes.append(state_title)
    except WorkflowException:
        pass
    payload['state_changes'] = state_changes
    return payload


def get_proxy_source(proxy):
    """
    Retrieve the proxy's source via the back reference.
    """
    brefs = referenceable.IReferenceable(proxy).getBRefs(
        relationship='current_syndication_targets')
    if len(brefs) > 0:
        assert len(brefs) == 1, (
            'More than one back syndication reference for proxy')
        return brefs[0]


def make_proxy(
        obj, event, target, suffix=''):
    """
    Create a proxy in a target for a given syndication action.
    """
    portal_properties = getToolByName(obj, 'portal_properties')
    encoding = portal_properties.site_properties.getProperty(
        'default_charset', 'utf-8')
    workflow = getToolByName(obj, 'portal_workflow')

    unique_id = INameChooser(target)._findUniqueName(
        obj.getId() + suffix, None)
    proxy = sudo(target.invokeFactory,
                 type_name='resonate.proxy',
                 id=unique_id)
    proxy = target[proxy]
    proxy.title = obj.Title().decode(encoding)
    proxy.description = obj.Description().decode(encoding)
    proxy.source_type = obj.portal_type
    # Submit for publication, so the item shows up in the review list
    sudo(workflow.doActionFor, proxy, 'submit')
    # Set proxy to pending syndication so reviewer can accept/reject;
    # Use the workflow object's doActionFor so that IAfterTransitionEvent
    # gets fired correctly
    sudo(workflow.doActionFor, proxy, event.transition.id)
    referenceable.IReferenceable(obj).addReference(
        referenceable.IReferenceable(proxy),
        relationship='current_syndication_targets')
    if event_behaviors.IEventBasic.providedBy(obj):
        for attr in ('start', 'end'):
            prop = getattr(obj, attr)
            if callable(prop):
                prop = DT2dt(prop())
            setattr(proxy, attr, prop)
