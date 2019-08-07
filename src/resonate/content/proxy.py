from zope import schema

from Products.CMFCore.utils import getToolByName

from plone.supermodel import model
from plone.uuid import interfaces as uuid_ifaces
from plone import indexer
from plone.app.layout.navigation import root

from resonate import MessageFactory as _


class IProxy(model.Schema):
    """
    Proxy
    """
    title = schema.TextLine(
        title=_(u"Title"),
        required=True,
        readonly=True,
    )

    description = schema.Text(
        title=_(u"Description"),
        required=False,
    )

    source_type = schema.TextLine(
        title=_(u"Source Type"),
        required=True,
        readonly=True,
    )

    start = schema.Datetime(
        title=_(u"Source Start Date"),
        required=False,
        readonly=True,
    )

    end = schema.Datetime(
        title=_(u"Source End Date"),
        required=False,
        readonly=True,
    )


@indexer.indexer(IProxy)
def navigation_root_uuid(obj):
    """
    Return the UUID for the navigation root.
    """
    portal_url = getToolByName(obj, 'portal_url')
    portal = portal_url.getPortalObject()
    nav_root = root.getNavigationRootObject(obj, portal)
    if nav_root is portal:
        return
    return uuid_ifaces.IUUID(nav_root)
