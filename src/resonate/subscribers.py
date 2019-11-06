import email
import logging

import six
from six import moves

from Acquisition import aq_parent

from zope import component
from zope.component import hooks
from zope import globalrequest

from plone.app.layout.navigation.root import getNavigationRoot
from plone.app.uuid.utils import uuidToObject
from Products.CMFCore.utils import getToolByName

from plone.app.event.dx import behaviors as event_behaviors

from plone import api

from resonate.content.proxy import IProxy
from . import utils
from . import behaviors
from resonate.utils import get_organizations_by_target
from resonate.utils import sendEmailToMember
from resonate.utils import sudo
from resonate.utils import update_payload

logger = logging.getLogger(__name__)


def send_syndication_notification(obj, event):
    """When an item's syndication state changes, send a notification.
    """
    # Bail out if this isn't our workflow
    if event.workflow.id not in {
            'syndication_source_workflow',
            'syndication_source_move_workflow'}:
        return

    # Don't sent an email for the empty transition that is just meant to
    # trigger automatic transitions
    transition_id = event.transition and event.transition.id or None
    if transition_id in {'review_syndication', 'review_move'}:
        return

    portal = getToolByName(obj, 'portal_url').getPortalObject()
    catalog = getToolByName(obj, 'portal_catalog')
    mfromname = api.portal.get_registry_record('plone.email_from_name')
    mfrom = api.portal.get_registry_record('plone.email_from_address')
    source = hooks.getSite()
    organizations = (event.kwargs or {}).get('organizations', ())
    bccs = getattr(source, 'notification_emails', '')
    for target_brain in catalog(UID=organizations):
        target_addr = getattr(
            target_brain.getObject(),
            'notification_emails',
            None
        )
        if target_addr:
            bccs += ', ' + target_addr
    if bccs == '':
        return
    bccs_by_addr = {}
    for name, addr in email.utils.getaddresses([bccs]):
        if not bccs_by_addr.get(addr):
            bccs_by_addr[addr] = name
    mto = u', '.join(
        email.utils.formataddr((name, addr))
        for addr, name in bccs_by_addr.items())

    mailhost = getToolByName(obj, 'MailHost')
    payload = {
        'new_state_id': event.new_state.id,
        'object_uid': api.content.get_uuid(obj),
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
    payload['organization_uid'] = api.content.get_uuid(nav_root)
    update_payload(obj, payload)

    if '/' in payload['object_uid']:
        # Plone site
        proxy = portal.unrestrictedTraverse(payload['object_uid'])
    else:
        proxy = sudo(uuidToObject, payload['object_uid'])
        update_payload(proxy, payload)

    subject = ('Pending review status for {0!r}'.format(obj))
    # Create the enclosing (outer) message
    outer = moves.email_mime_multipart.MIMEMultipart()
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


def update_proxy_fields(obj, event):
    """Update proxy title when source title is modified
    """
    proxy_relations = utils.getRelations(
        from_object=obj, from_attribute='current_syndication_targets')
    if not proxy_relations:
        return

    portal_properties = getToolByName(obj, 'portal_properties')
    encoding = portal_properties.site_properties.getProperty('default_charset',
                                                             'utf-8')

    source_title = obj.title_or_id()
    if not isinstance(source_title, six.string_types):
        source_title = unicode(obj.title_or_id(), encoding)
    for proxy_relation in proxy_relations:
        proxy = proxy_relation.to_object
        reindex = False
        if not IProxy.providedBy(proxy):
            continue
        if source_title != proxy.title:
            proxy.title = source_title
            reindex = True
        elif event_behaviors.IEventBasic.providedBy(obj):
            if obj.start != proxy.start:
                proxy.start = obj.start
                reindex = True
            if obj.end != proxy.end:
                proxy.end = obj.end
                reindex = True
        if reindex:
            proxy.reindexObject()


def remove_proxy_relations(obj, event):
    """
    Remove a source's relations after proxy object is deleted.
    """
    utils.removeRelations(
        to_object=obj,
        from_attribute='current_syndication_targets')


def remove_source_proxies(obj, event):
    """
    Remove a sources proxies after source object is deleted.
    """
    proxy_relations = utils.getRelations(
        from_object=obj,
        from_attribute='current_syndication_targets')
    for proxy_relation in proxy_relations:
        proxy = proxy_relation.to_object
        parent = aq_parent(proxy)
        parent.manage_delObjects(ids=[proxy.getId()])


def unpublish_proxy(obj, event):
    """Unpublish proxy after source object is unpublished
    """
    proxy_relations = utils.getRelations(
        from_object=obj,
        from_attribute='current_syndication_targets')
    if not proxy_relations:
        return

    old_state = event.old_state.id
    if old_state != 'published':
        return

    wft = getToolByName(obj, 'portal_workflow')
    for proxy_relation in proxy_relations:
        proxy = proxy_relation.to_object
        if wft.getInfoFor(proxy, "review_state") == "published":
            sudo(wft.doActionFor, proxy, 'retract')


def accept_syndication(obj, event):
    """
    Update source object to syndicated.
    """
    # Bail out if this isn't our workflow
    if event.workflow.id != 'syndication_proxy_workflow':
        return

    # and not our transition
    transition_id = event.transition and event.transition.id or None
    if transition_id not in {
            'accept_syndication', 'auto_approve_syndication'}:
        return

    wf_tool = getToolByName(obj, 'portal_workflow')
    source = utils.get_proxy_source(obj)
    if wf_tool.getInfoFor(source, 'syndication_state') != 'syndicated':
        sudo(
            wf_tool.doActionFor, source,
            'review_syndication')
    # Automatically publish proxy object
    wf_tool.doActionFor(obj, 'publish')


def reject_syndication(obj, event):
    """
    Update the source object's rejected_syndication_sites
    with a relation to the proxy object's site and remove
    proxy object.
    """
    # Bail out if this isn't our workflow
    if event.workflow.id != 'syndication_proxy_workflow':
        return

    # and not our transition
    transition_id = event.transition and event.transition.id or None
    if transition_id != 'reject_syndication':
        return

    workflow = getToolByName(obj, 'portal_workflow')

    organization_path = getNavigationRoot(obj)
    organization = obj.restrictedTraverse(organization_path)

    source = utils.get_proxy_source(obj)

    utils.addRelation(
        from_object=source, to_object=organization,
        from_attribute='rejected_syndication_sites')
    utils.removeRelations(
        from_object=source, to_object=obj,
        from_attribute='current_syndication_targets')

    # Use the workflow object's doActionFor so that IAfterTransitionEvent
    # gets fired correctly
    sudo(workflow.doActionFor, source, 'review_syndication')

    # Remove the proxy for this syndication request
    aq_parent(obj).manage_delObjects([obj.getId()])


def accept_move(proxy, event):
    """
    Move the content to the correct location
    based on the target organization chosen.
    """
    # Bail out if this isn't our workflow
    if event.workflow.id != 'syndication_proxy_move_workflow':
        return

    # and not our transition
    transition_id = event.transition and event.transition.id or None
    if transition_id != 'move':
        return

    wft = getToolByName(proxy, 'portal_workflow')
    history = wft.getHistoryOf(
        'syndication_source_move_workflow', utils.get_proxy_source(proxy))

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
    targets = catalog(
        path=organization_path,
        object_provides=behaviors.ISyndicationTarget.__identifier__)
    for target in targets:
        target_obj = target.getObject()
        if getNavigationRoot(target_obj) == organization_path:
            break
    else:
        raise ValueError(
            'Could not find organization for target of {0!r}'.format(proxy))

    # Move original object into place
    source = utils.get_proxy_source(proxy)
    source_parent = aq_parent(source)
    paste_id = source.getId()
    paste = sudo(source_parent.manage_cutObjects,
                 ids=[paste_id])
    sudo(target_obj.manage_pasteObjects, paste)

    # Automatically publish moved object
    moved_obj = target_obj[paste_id]
    if wft.getInfoFor(moved_obj, "review_state") != "published":
        sudo(wft.doActionFor, moved_obj, 'publish')

    # Update moved object's syndication_state
    sudo(wft.doActionFor, moved_obj, 'review_move')

    # Remove the proxy for this move request
    aq_parent(proxy).manage_delObjects([proxy.getId()])

    request = globalrequest.getRequest()
    if request is not None:
        request['redirect_to'] = '/'.join(
            moved_obj.getPhysicalPath()[
                len(api.portal.get().getPhysicalPath()):])


def reject_move(obj, event):
    """
    Remove the proxy after a rejected move.
    """
    # Bail out if this isn't our workflow
    if event.workflow.id != 'syndication_proxy_move_workflow':
        return

    # and not our transition
    transition_id = event.transition and event.transition.id or None
    if transition_id != 'reject_move':
        return

    # Use the workflow object's doActionFor so that IAfterTransitionEvent
    # gets fired correctly
    workflow = getToolByName(obj, 'portal_workflow')
    source = utils.get_proxy_source(obj)
    sudo(workflow.doActionFor, source, 'review_move')

    # Remove the proxy for this move request
    aq_parent(obj).manage_delObjects([obj.getId()])


def notify_syndication_change(obj, event):
    """
    When a syndication request is accepted or rejected,
    the comment for the action needs to be emailed to the request originator.
    """
    # Bail out if this isn't our workflow
    if event.workflow.id not in {
            'syndication_source_workflow',
            'syndication_source_move_workflow'}:
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
    history = wft.getHistoryOf(event.workflow.id, obj)
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
    When an Event or News Item completes the request_syndication
    transition, create the proxy object in each target organization's
    folder.
    """
    # Bail out if this isn't our workflow
    if event.workflow.id != 'syndication_source_workflow':
        return

    # and not our transition
    transition_id = event.transition and event.transition.id or None
    if transition_id != 'request_syndication':
        return

    organizations = event.kwargs.get('organizations')
    organizations = get_organizations_by_target(obj, organizations)
    for organization, target in organizations.items():
        utils.make_proxy(obj, event, target)


def request_move(obj, event):
    """
    Create the proxy for a source move request.
    """
    # Bail out if this isn't our workflow
    if event.workflow.id != 'syndication_source_move_workflow':
        return

    # and not our transition
    transition_id = event.transition and event.transition.id or None
    if transition_id != 'request_move':
        return

    organization = event.kwargs.get('organization')
    organizations = get_organizations_by_target(obj, [organization])
    target, = organizations.values()
    utils.make_proxy(obj, event, target, suffix='-proxy')
