import logging
import sys

from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import getSecurityManager
from AccessControl.SecurityManagement import setSecurityManager

from zope.component.hooks import getSite

from Products.CMFCore.tests.base.security import OmnipotentUser as \
            CMFOmnipotentUser
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.WorkflowCore import WorkflowException

from Products.Archetypes.interfaces import IBaseObject
from Products.ATContentTypes.interfaces import IATEvent
from Products.ATContentTypes.interfaces import IATNewsItem
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.statusmessages.interfaces import IStatusMessage
from plone.app.layout.navigation.root import getNavigationRoot

from plone.uuid.interfaces import IUUID

from resonate.interfaces import IEventSyndicationTarget
from resonate.interfaces import INewsSyndicationTarget


class OmnipotentUser(CMFOmnipotentUser):
    """Omnipotent User for checking membrane catalog.
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


def safe_uid(obj):
    try:
        uid = IUUID(obj)
    except (TypeError,), err:
        # special-case Plone site objects
        if not IPloneSiteRoot.providedBy(obj):
            raise err
        uid = '/'.join(obj.getPhysicalPath())
    return uid


def getRefs(obj, fname):
    if IBaseObject.providedBy(obj):
        return obj.getField(fname).get(obj)
    else:
        return [a.to_object for a in getattr(obj, fname)]


def setRef(obj, fname, value):
    if IBaseObject.providedBy(obj):
        setATRef(obj, fname, value)
    else:
        setDTRef(obj, fname, value)


def setATRef(obj, fname, value):
    field = obj.getField(fname)
    existing = [safe_uid(a) for a in field.get(obj)]
    existing.append(safe_uid(value.to_object))
    field.set(obj, existing)


def setDTRef(obj, fname, value):
    ref_field = getattr(obj, fname)
    ref_field.append(value)
    setattr(obj, fname, ref_field)


def delRef(obj, fname, value):
    if IBaseObject.providedBy(obj):
        delATRef(obj, fname, value)
    else:
        delDTRef(obj, fname, value)


def delATRef(obj, fname, value):
    field = obj.getField(fname)
    existing = [safe_uid(a) for a in field.get(obj)]
    existing.remove(safe_uid(value.to_object))
    field.set(obj, existing)


def delDTRef(obj, fname, value):
    ref_field = getattr(obj, fname)
    ref_field.remove(value)
    setattr(obj, fname, ref_field)


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
    mtool = getToolByName(context, 'portal_membership')
    portal_catalog = getToolByName(context, 'portal_catalog')
    uid_catalog = getToolByName(context, 'uid_catalog')
    home_folder_path = '/'.join(context.getPhysicalPath())
    context_path = '/'.join(context.getPhysicalPath())
    target_iface = target_interface(context)

    organizations = [
        brain.getObject()
        for brain in uid_catalog(UID=uids)
    ]
    result = {}
    for organization in organizations:
        if organization is None:
            continue
        organization_path = getNavigationRoot(organization)
        if context_path.startswith(home_folder_path):
            # Special-case the member's home folder, since it is not a
            # navigation root but we still want to be able to request
            # syndication to the containing portal
            pass
        elif organization_path == getNavigationRoot(context):
            # Always exclude the current organization
            continue
        targets = portal_catalog(path=organization_path,
                                 object_provides=target_iface.__identifier__)
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
    f_name = portal.getProperty('email_from_name')
    f_addr = portal.getProperty('email_from_address')
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
    except NotFound, e:
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
    except Exception, e:
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
    nav_root_uid = safe_uid(nav_root)
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


def update_syndication_state(source, proxy=None):
    wf_tool = getToolByName(source, 'portal_workflow')
    targets = getRefs(source, 'current_syndication_targets')
    if proxy in targets:
        # The reference might be out of date;
        # we make sure to only consider other targets
        targets.pop(targets.index(proxy))
    if targets:
        state_id = 'syndicated'
    else:
        state_id = 'not_syndicated'
    history = wf_tool.getHistoryOf('syndication_workflow', source)
    # The move and reject_syndication transitions are
    # set to not change the state, since it can't be known
    # at that point if it should be. We update their respective
    # history record here to the correct value.
    history[-1]['syndication_state'] = state_id


def target_interface(source):
    if IATEvent.providedBy(source):
        return IEventSyndicationTarget
    if IATNewsItem.providedBy(source):
        return INewsSyndicationTarget
    return None
