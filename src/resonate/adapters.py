from zope.interface import implements
from zope.component import adapts, getMultiAdapter
from plone.app.uuid.utils import uuidToObject
from plone.app.layout.navigation.root import getNavigationRootObject
from Products.CMFCore.utils import getToolByName
from Products.ATContentTypes.interfaces import IATEvent, IATNewsItem
from Products.ATContentTypes.interfaces import IATFolder

from borg.localrole.default_adapter import DefaultLocalRoleAdapter
from borg.localrole.interfaces import ILocalRoleProvider

from nd.content.interfaces import IMemberFolder
from nd.content.content.seminar import ISeminar
from nd.syndication.utils import getRefs
from nd.syndication.utils import safe_uid


class MemberFolderRoleAdapter(DefaultLocalRoleAdapter):
    adapts(IMemberFolder)
    implements(ILocalRoleProvider)

    @property
    def _rolemap(self):
        rolemap = {}
        profilelinks = getMultiAdapter((self.context, self.context.REQUEST),
                                       name='profilelinks')
        member = profilelinks.member_from_portfolio()
        if not member:
            return rolemap

        catalog = getToolByName(self.context, 'portal_catalog')
        students = catalog(advisors=safe_uid(member),
                           graduated_undergraduated='Graduate Student')
        for student in students:
            rolemap[student.id] = ['Contributor']
        return rolemap


class NonMemberSourceRoleAdapter(DefaultLocalRoleAdapter):
    implements(ILocalRoleProvider)

    @property
    def _rolemap(self):
        rolemap = {}
        if not (IATEvent.providedBy(self.context) or \
                IATNewsItem.providedBy(self.context) or \
                ISeminar.providedBy(self.context)):
                return rolemap
        proxies = getRefs(self.context, 'current_syndication_targets')

        if not proxies:
            return rolemap

        portal_url = getToolByName(self.context, 'portal_url')
        portal = portal_url.getPortalObject()
        catalog = getToolByName(self.context, 'portal_catalog')
        o_uids = [safe_uid(getNavigationRootObject(proxy, portal)) \
                                                        for proxy in proxies]
        brains = catalog(portal_type='nd.content.member', affiliations=o_uids)
        for brain in brains:
            rolemap[brain.id] = ['Reviewer']
        return rolemap


class NonMemberRoleAdapter(DefaultLocalRoleAdapter):
    adapts(IATFolder)
    implements(ILocalRoleProvider)

    def organizations(self):
        uids = []
        folder_path = '/'.join(self.context.getPhysicalPath())
        portal_url = getToolByName(self.context, 'portal_url')
        portal = portal_url.getPortalObject()
        catalog = getToolByName(self.context, 'portal_catalog')
        reference = getToolByName(self.context, 'reference_catalog')
        brains = catalog(portal_type=['News Item',
                                      'Event', 'nd.content.seminar'],
                         path={'query': folder_path, 'depth': 2})
        source_uids = [b.UID for b in brains]
        for rel in reference(sourceUID=source_uids,
                             relationship='syndicatesTo'):
            proxy = uuidToObject(rel.targetUID)
            if not proxy:
                continue
            uid = safe_uid(getNavigationRootObject(proxy, portal))
            if uid:
                uids.append(uid)
        return uids

    @property
    def _rolemap(self):
        rolemap = {}
        o_uids = self.organizations()
        if not o_uids:
            return rolemap

        catalog = getToolByName(self.context, 'portal_catalog')
        brains = catalog(portal_type='nd.content.member', affiliations=o_uids)
        for brain in brains:
            rolemap[brain.id] = ['Deleter']

        return rolemap
