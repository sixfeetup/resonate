"""
Arbitrary set up to be run when the resonate profile is installed.
"""

from Products.CMFCore.utils import getToolByName

from plone.app.referenceablebehavior import uidcatalog
from plone.uuid import handlers


def make_portal_referenceable(event):
    """
    Enable the portal to support Archetypes references.
    """
    if event.profile_id != 'profile-resonate:default':
        return

    portal = getToolByName(event.tool, 'portal_url').getPortalObject()
    handlers.addAttributeUUID(portal, None)
    uidcatalog.added_handler(portal, event)
