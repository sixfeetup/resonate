"""
Arbitrary set up to be run when the resonate profile is installed.
"""

from zope import component

from Products.CMFCore.utils import getToolByName

from plone.uuid import handlers
from five.intid import intid


def register_portal_intid(event):
    """
    Enable the portal to support zc.relations and UUIDs.
    """
    if event.profile_id != 'profile-resonate:default':
        return

    intids = component.queryUtility(intid.IIntIds)
    portal = getToolByName(event.tool, 'portal_url').getPortalObject()
    handlers.addAttributeUUID(portal, None)
    if intids.queryId(portal) is None:
        intid.addIntIdSubscriber(portal, event)
