import email
import logging
import rfc822

from Acquisition import aq_parent
from zope.container.interfaces import INameChooser
from zope.intid.interfaces import IIntIds
from zope import component
from zope.component import getUtility
from zope.component import hooks
from p4a.subtyper.interfaces import ISubtyper
from plone.app.layout.navigation.root import getNavigationRoot
from plone.app.uuid.utils import uuidToObject
from Products.CMFCore.utils import getToolByName
from Products.statusmessages.interfaces import IStatusMessage
from Products.Archetypes.interfaces import IBaseObject
from Products.Archetypes.interfaces import IReference
from Products.ATContentTypes.interfaces import IATEvent, IATNewsItem
from Products.ATContentTypes.utils import DT2dt
from plone.dexterity.interfaces import IDexterityContent

from z3c.relationfield import RelationValue

# from nd.content.content.seminar import ISeminar

from resonate.content.proxy import IProxy
from resonate.interfaces import ISyndicationTarget
from resonate.interfaces import IEventSyndicationTarget
from resonate.interfaces import INewsSyndicationTarget
from resonate.utils import getRefs
from resonate.utils import get_organizations_by_target
from resonate.utils import safe_uid
from resonate.utils import sendEmailToMember
from resonate.utils import setRef
from resonate.utils import sudo
from resonate.utils import update_payload
from resonate.utils import update_syndication_state
from resonate import MessageFactory as _

logger = logging.getLogger(__name__)


def send_syndication_notification(obj, event):
    """When an item's syndication state changes, send a notification.
    """
    # Bail out if this isn't our workflow
    if event.workflow.id != 'syndication_workflow':
        return

    # Bail out if it's an AT object that is in the process
    # of being created
    if IBaseObject.providedBy(obj) and obj.checkCreationFlag():
        return

    portal = getToolByName(obj, 'portal_url').getPortalObject()
    catalog = getToolByName(obj, 'portal_catalog')
    mfromname = portal.email_from_name
    mfrom = portal.email_from_address
    source = hooks.getSite()
    organizations = (event.kwargs or {}).get('organizations', ())
    bccs = source.notification_emails + ', '.join(
        target_brain.getObject().notification_emails
        for target_brain in catalog(UID=organizations))
    bccs_by_addr = {}
    for name, addr in rfc822.AddressList(bccs).addresslist:
        if not bccs_by_addr.get(addr):
            bccs_by_addr[addr] = name
    mto = u', '.join(
        email.utils.formataddr((name, addr))
        for addr, name in bccs_by_addr.iteritems())

    mailhost = getToolByName(obj, 'MailHost')
    payload = {
        'new_state_id': event.new_state.id,
        'object_uid': safe_uid(obj),
        'old_state_id': event.old_state.id,
        'status': event.status,
        'transition_id': event.transition and event.transition.id or None,
    }

    # Bail out if this is the initial object creation transition
    if payload['transition_id'] is None and \
       payload['new_state_id'] == payload['old_state_id']:
        logger.debug(
            'Syndication notification NOT queued in %s for %s: %s',
            getNavigationRoot(obj),
            obj,
            payload
        )
        return

    nav_root_path = getNavigationRoot(obj)
    nav_root = obj.restrictedTraverse(nav_root_path)
    payload['organization_title'] = nav_root.title_or_id()
    payload['organization_uid'] = safe_uid(nav_root)
    update_payload(obj, payload)

    if '/' in payload['object_uid']:
        # Plone site
        proxy = portal.unrestrictedTraverse(payload['object_uid'])
    else:
        proxy = sudo(uuidToObject, payload['object_uid'])
        update_payload(proxy, payload)

    subject = ('Pending review status for {0!r}'.format(obj))
    # Create the enclosing (outer) message
    outer = email.mime.multipart.MIMEMultipart()
    # Create the HTML
    digest_notification = component.getMultiAdapter(
        (obj, obj.REQUEST), name='digest_notification')
    digest_notification.update(payload)
    html = digest_notification()
    # Create the MIME wrapper
    html_part = email.mime.text.MIMEText(
        html, _subtype='html', _charset='UTF-8')
    # Attach part
    outer.attach(html_part)
    mailhost.send(
        outer, subject=subject, mfrom="%s <%s>" % (mfromname, mfrom), mto=mto)

    logger.debug('Syndication notification queued to be sent %s for %s: %s',
                 nav_root, obj, payload)


def check_unique_subtype(event):
    """Make sure there is only one subtyped folder in organization for
       given interface.
    """
    if not ISyndicationTarget in event.subtype.type_interface.__bases__:
        return
    catalog = getToolByName(event.object, 'portal_catalog')
    organization_path = getNavigationRoot(event.object)
    already_subtyped = catalog(path=organization_path,
                object_provides=event.subtype.type_interface.__identifier__)
    already_subtyped = [
        a
        for a in already_subtyped
        if getNavigationRoot(a.getObject()) == organization_path and
           a.UID != safe_uid(event.object)
    ]
    if already_subtyped:
        subtyper = getUtility(ISubtyper)
        subtyper._remove_type(event.object)
        msg = _(u'%s target folder already exists for this Organization.' %
                event.subtype.title)
        request = event.object.REQUEST
        IStatusMessage(request).addStatusMessage(msg, type='info')


def update_proxy_fields(obj, event):
    """Update proxy title when source title is modified
    """
    if not (IATEvent.providedBy(obj) or
            IATNewsItem.providedBy(obj)):
        return
    proxies = getRefs(obj, 'current_syndication_targets')

    if not proxies:
        return

    calendar = getToolByName(obj, 'portal_calendar')
    event_types = calendar.calendar_types
    portal_properties = getToolByName(obj, 'portal_properties')
    encoding = portal_properties.site_properties.getProperty('default_charset',
                                                             'utf-8')

    source_title = obj.title_or_id()
    if not isinstance(source_title, unicode):
        source_title = unicode(obj.title_or_id(), encoding)
    for proxy in proxies:
        reindex = False
        if not IProxy.providedBy(proxy):
            continue
        if source_title != proxy.title:
            proxy.title = source_title
            reindex = True
        elif obj.portal_type in event_types:
            if obj.start != proxy.start:
                proxy.start = obj.start
                reindex = True
            if obj.end != proxy.end:
                proxy.end = obj.end
                reindex = True
        if reindex:
            proxy.reindexObject()


def remove_at_proxy(obj, event):
    """Remove proxy after reference is removed
    """
    if not IReference.providedBy(obj):
        return
    source = obj.getSourceObject()
    if not IBaseObject.providedBy(source):
        return
    proxy = obj.getTargetObject()
    if not IProxy.providedBy(proxy):
        return

    proxy.source_object = None
    parent = aq_parent(proxy)
    parent.manage_delObjects(ids=[proxy.getId()])


def remove_dexterity_proxies(obj, event):
    """Remove proxy after source object is removed
    """
    if not IDexterityContent.providedBy(obj):
        return
    for rv in obj.current_syndication_targets:
        proxy = rv.to_object
        proxy.source_object = None
        parent = aq_parent(proxy)
        parent.manage_delObjects(ids=[proxy.getId()])


def unpublish_proxy(obj, event):
    """Unpublish proxy after source object is unpublished
    """
    if not (IATEvent.providedBy(obj) or
            IATNewsItem.providedBy(obj)):
        return
    proxies = getRefs(obj, 'current_syndication_targets')

    if not proxies:
        return

    old_state = event.old_state.id
    if old_state != 'published':
        return

    wft = getToolByName(obj, 'portal_workflow')
    for proxy in proxies:
        if wft.getInfoFor(proxy, "review_state") == "published":
            sudo(wft.doActionFor, proxy, 'retract')


def cleanup_source_after_proxy_remove(obj, event):
    """Cleanup source reference field after proxy object has been removed
    """
    if not obj.source_object:
        return

    source = obj.source_object.to_object
    if not source:
        return

    #  only Seminar (dexterity type) needs actual cleanup
    #  AT based objects are doing it by themselves
    # TODO: replace with generic test for dexterity types?
    # if ISeminar.providedBy(source):
    #     cleaned_up = [
    #         rv
    #         for rv in source.current_syndication_targets
    #         if safe_uid(rv.to_object) != safe_uid(obj)
    #     ]
    #     source.current_syndication_targets = cleaned_up


def accept_syndication(obj, event):
    """
    Update source object to syndicated.
    """
    # Bail out if this isn't our workflow
    if event.workflow.id != 'syndication_workflow':
        return

    # and not our transition
    transition_id = event.transition and event.transition.id or None
    if transition_id != 'accept_syndication':
        return

    wf_tool = getToolByName(obj, 'portal_workflow')
    syndication_state = wf_tool.getInfoFor(obj.source_object.to_object,
                                           "syndication_state")
    if syndication_state != "syndicated":
        sudo(wf_tool.doActionFor, obj.source_object.to_object, transition_id)
    # Automatically publish proxy object
    wf_tool.doActionFor(obj, 'publish')


def reject_syndication(obj, event):
    """
    Update the source object's rejected_syndication_sites
    with a reference to the proxy object's site and remove
    proxy object.
    """
    # Bail out if this isn't our workflow
    if event.workflow.id != 'syndication_workflow':
        return

    # and not our transition
    transition_id = event.transition and event.transition.id or None
    if transition_id != 'reject_syndication':
        return

    organization_path = getNavigationRoot(obj)
    organization = obj.restrictedTraverse(organization_path)

    intids = getUtility(IIntIds)

    source = obj.source_object.to_object
    # Use the workflow object's doActionFor so that IAfterTransitionEvent
    # gets fired correctly
    sudo(event.workflow.doActionFor, source, 'reject_syndication')
    sudo(update_syndication_state, source, obj)
    if not (IATEvent.providedBy(source) or
            IATNewsItem.providedBy(source)):
        return
    org_id = intids.getId(organization)
    sudo(setRef, source, 'rejected_syndication_sites', RelationValue(org_id))
    parent_folder = aq_parent(obj)
    parent_folder.manage_delObjects([obj.getId()])


def accept_move(proxy, event):
    """
    Move the content to the correct location
    based on the target organization chosen.
    """
    # Bail out if this isn't our workflow
    if event.workflow.id != 'syndication_workflow':
        return

    # and not our transition
    transition_id = event.transition and event.transition.id or None
    if transition_id != 'move':
        return

    # Use original object for target / history
    if not IProxy.providedBy(proxy):
        return
    # FIXME: these adapters should be in their respective packages
    elif IATEvent.providedBy(proxy.source_object.to_object):
        target_iface = IEventSyndicationTarget
    elif IATNewsItem.providedBy(proxy.source_object.to_object):
        target_iface = INewsSyndicationTarget
    else:
        return
    wft = getToolByName(proxy, 'portal_workflow')
    history = wft.getHistoryOf('syndication_workflow',
                               proxy.source_object.to_object)

    # last history entry is for current transition_id
    # we need to get the previous one
    last_request_move = [
        wfh
        for wfh in reversed(history)
        if wfh['action'] == 'request_move'
    ][0]

    organization = sudo(uuidToObject, last_request_move['organization'])
    catalog = getToolByName(proxy, 'portal_catalog')
    organization_path = getNavigationRoot(organization)
    targets = catalog(path=organization_path,
                      object_provides=target_iface.__identifier__)
    for target in targets:
        target_obj = target.getObject()
        if getNavigationRoot(target_obj) == organization_path:
            break

    # Delete the proxy
    proxy_parent = aq_parent(proxy)
    sudo(proxy_parent.manage_delObjects, ids=[proxy.getId()])
    # Move original object into place
    source_parent = aq_parent(proxy.source_object.to_object)
    paste_id = proxy.source_object.to_object.getId()
    paste = sudo(source_parent.manage_cutObjects,
                 ids=[paste_id])
    sudo(target_obj.manage_pasteObjects, paste)
    # Automatically publish moved object
    moved_obj = target_obj[paste_id]
    if wft.getInfoFor(moved_obj, "review_state") != "published":
        sudo(wft.doActionFor, moved_obj, 'publish')
    # Update moved object's syndication_state
    if wft.getInfoFor(moved_obj, "syndication_state") == "pending_move":
        sudo(wft.doActionFor, moved_obj, 'move')
        sudo(update_syndication_state, moved_obj)


def notify_syndication_change(obj, event):
    """
    When a syndication request is accepted or rejected,
    the comment for the action needs to be emailed to the request originator.
    """
    # Bail out if this isn't our workflow
    if event.workflow.id != 'syndication_workflow':
        return

    if IProxy.providedBy(obj):
        # Only notify for the real content object
        return

    transition_id = event.transition and event.transition.id or None
    init_status = {
        'accept_syndication': ['request_syndication'],
        'move': ['request_move'],
        'reject_syndication': ['request_move', 'request_syndication'],
    }
    if transition_id in ('accept_syndication', 'move'):
        status = 'accepted'
    elif transition_id in ('reject_syndication',):
        status = 'rejected'
    else:
        return

    mtool = getToolByName(obj, 'portal_membership')
    wft = getToolByName(obj, 'portal_workflow')
    history = wft.getHistoryOf('syndication_workflow', obj)
    comment = event.kwargs['comment']

    # Get the last actor
    actor = None
    for h in reversed(history):
        if h['action'] in init_status[transition_id]:
            actor = h['actor']
            break
    if not actor:
        return

    member = mtool.getMemberById(actor)
    if not member:
        return

    sendEmailToMember(member, obj, status, comment)


def request_syndication(obj, event):
    """
    When an Event, News Item or Seminar completes the request_syndication
    transition, create the proxy object in each target organization's
    folder.
    """
    # Bail out if this isn't our workflow
    if event.workflow.id != 'syndication_workflow':
        return

    # and not our transition
    transition_id = event.transition and event.transition.id or None
    if transition_id not in ('request_move', 'request_syndication'):
        return

    organizations = event.kwargs.get('organizations')
    if not organizations:
        organization = event.kwargs.get('organization')
        if not organization:
            return
        organizations = [organization]

    portal_properties = getToolByName(obj, 'portal_properties')
    calendar = getToolByName(obj, 'portal_calendar')
    event_types = calendar.calendar_types
    wf_tool = getToolByName(obj, 'portal_workflow')
    intids = getUtility(IIntIds)
    source_id = intids.getId(obj)
    organizations = get_organizations_by_target(obj, organizations)
    encoding = portal_properties.site_properties.getProperty('default_charset',
                                                             'utf-8')
    for organization, target in organizations.items():
        # Create the proxy
        if transition_id == 'request_move':
            # Tack on -proxy, so that collective.indexing doesn't get confused
            # when we later paste the source object back into the same folder
            oid = INameChooser(target)._findUniqueName(obj.getId() + '-proxy',
                                                       None)
        else:
            oid = INameChooser(target)._findUniqueName(obj.getId(), None)
        proxy = sudo(target.invokeFactory,
                     type_name='resonate.proxy',
                     id=oid)
        proxy = target[proxy]
        proxy.source_object = RelationValue(source_id)
        proxy.title = unicode(obj.Title(), encoding)
        proxy.description = unicode(obj.Description(), encoding)
        proxy.source_type = obj.portal_type
        # Submit for publication, so the item shows up in the review list
        sudo(wf_tool.doActionFor, proxy, 'submit')
        # Set proxy to pending syndication so reviewer can accept/reject;
        # Use the workflow object's doActionFor so that IAfterTransitionEvent
        # gets fired correctly
        sudo(event.workflow.doActionFor, proxy, transition_id)
        proxy_id = intids.getId(proxy)
        setRef(obj, 'current_syndication_targets', RelationValue(proxy_id))
        if obj.portal_type in event_types:
            for attr in ('start', 'end'):
                prop = getattr(obj, attr)
                if callable(prop):
                    prop = DT2dt(prop())
                setattr(proxy, attr, prop)
