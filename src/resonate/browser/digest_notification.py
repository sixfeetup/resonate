from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName
from plone.app.uuid.utils import uuidToObject
from plone.app.layout.navigation.root import getNavigationRootObject

from Products.Archetypes.interfaces import referenceable

from resonate.content.proxy import IProxy


class DigestNotification(BrowserView):
    """This is a view to generate an HTML email containing
    the syndication activity in digest form.
    """

    def __init__(self, *args, **kwargs):
        super(DigestNotification, self).__init__(*args, **kwargs)
        self.items_by_uid = {}

    def fix_organization_by_state(self, payload):
        wft = getToolByName(self.context, 'portal_workflow')
        source = uuidToObject(payload['object_uid'])

        if not source:
            return payload

        # we need to update the organization only for NON pending states
        if (
                'pending_syndication' in wft.getInfoFor(
                    source, 'syndication_state') or
                'pending_move' in wft.getInfoFor(
                    source, 'syndication_move_state')):
            return payload

        if IProxy.providedBy(source):
            return payload

        proxies = referenceable.IReferenceable(source).getRefs(
            relationship='current_syndication_targets')
        organization_title = []
        for proxy in proxies:
            new_organization = getNavigationRootObject(proxy, self.context)
            organization_title.append(new_organization.title_or_id())
        payload['organization_title'] = ','.join(organization_title)

        return payload

    def update(self, payload):
        """
        Update self.items with payload items.
        """
        self.item = self.fix_organization_by_state(payload)
        self.items_by_uid[self.item['object_uid']] = self.item

    def items_by_date(self):
        return sorted([
            item
            for item in self.items_by_uid.values()
        ], key=lambda item: item['last_changed'], reverse=True)
