.. contents::

Introduction
============

This package introduces a system of syndicating content between micro-sites.
The general idea is that users can request syndication to another micro-site
in the Plone site umbrella, and the reviewers for this other site can choose
to accept or reject this syndication. The workflow relies on a micro-site
container that provides both IUUID and INavigationRoot.

Any portal type that has the syndication_workflow in it's chain will have
a queue of workflow transitions created. An example of adding this workflow
to a type's chain would look like this (in your product's workflows.xml):

    <bindings>
        <type type_id="Event">
            <bound-workflow workflow_id="simple_publication_workflow"/>
            <bound-workflow workflow_id="syndication_workflow"/>
        </type>
    </bindings

Here is an example of interacting with the queue for a micro-site:

    from pprint import pprint
    from Products.CMFCore.utils import getToolByName
    from plone.app.layout.navigation.root import getNavigationRoot
    from nd.syndication.interfaces import ISyndicationNotificationTool

    nav_root_path = getNavigationRoot(context)
    nav_root = context.restrictedTraverse(nav_root_path)
    notification_tool = getToolByName(nav_root, 'portal_syn_notification')
    queue = notification_tool.get_queue(nav_root)
    while queue:
        payload = queue.pull()
        pprint(payload)

Which can yield:

    {   'new_state_id': 'pending_syndication',
        'object_uid': '83a5d883-b9d2-4f7d-bc66-3c4f57c4184f',
        'old_state_id': 'not_syndicated',
        'status': {   'action': 'request_syndication',
                      'actor': 'staff',
                      'comments': '',
                      'syndication_state': 'pending_syndication',
                      'time': DateTime('2012/11/16 13:05:30.643109 US/Eastern')},
        'transition_id': 'request_syndication'}

The information in the payload can then be consumed by a script to create a
digest for interested parties.
