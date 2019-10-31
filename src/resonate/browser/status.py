"""
Browser views for syndication status.
"""

from Products.CMFCore.utils import getToolByName

from plone.app.layout.navigation import root

from .. import utils


class SyndicationSourceStatusView(object):
    """
    Reflect the syndication status of this source.
    """

    def is_syndicated(self):
        """
        Determine if this source has been accepted for syndication.
        """
        workflow = getToolByName(self.context, 'portal_workflow')
        source = self.context

        for target_relation in source.current_syndication_targets:
            if workflow.getInfoFor(
                    target_relation.to_object, 'syndication_state'
            ) == 'syndicated':
                return True

    def is_pending_syndication(self):
        """
        Determine if this source has any pending requests for syndication.
        """
        workflow = getToolByName(self.context, 'portal_workflow')
        source = self.context

        for target_relation in source.current_syndication_targets:
            if workflow.getInfoFor(
                    target_relation.to_object, 'syndication_state'
            ) == 'pending_syndication':
                return True

    def is_syndication_accepted(self):
        """
        Determine if this source is syndicated and has no pending requests.
        """
        return self.is_syndicated() and not self.is_pending_syndication()

    def is_syndication_rejected(self):
        """
        Determine if this source is not syndicated and is not pending.
        """
        return not self.is_syndicated() and not self.is_pending_syndication()

    def is_moved(self):
        """
        Determine if this source has been accepted to be moved.
        """
        workflow = getToolByName(self.context, 'portal_workflow')
        source = self.context

        for target_relation in source.current_syndication_targets:
            if workflow.getInfoFor(
                    target_relation.to_object, 'syndication_move_state'
            ) == 'moved':
                return True

    def is_pending_move(self):
        """
        Determine if this source has any pending requests for move.
        """
        workflow = getToolByName(self.context, 'portal_workflow')
        source = self.context

        for target_relation in source.current_syndication_targets:
            if workflow.getInfoFor(
                    target_relation.to_object, 'syndication_move_state'
            ) == 'pending_move':
                return True

    def is_move_accepted(self):
        """
        Determine if this source has been moved and has no pending requests.
        """
        return self.is_moved() and not self.is_pending_move()

    def is_move_rejected(self):
        """
        Determine if this source has not been moved and is not pending.
        """
        return not self.is_moved() and not self.is_pending_move()


class SyndicationProxyStatusView(object):
    """
    Reflect the syndication status of this proxy in a target site.
    """

    RELATIONSHIP_TEMPLATE = 'resonate.auto-approve.{0}'

    def is_syndication_auto_approved(self):
        """
        Is syndication approved from the source to this target site and type.
        """
        portal = getToolByName(self.context, 'portal_url').getPortalObject()

        proxy = self.context
        target_site = root.getNavigationRootObject(proxy, portal)

        source = utils.get_proxy_source(proxy)
        source_site = root.getNavigationRootObject(source, portal)

        return bool(utils.getRelations(
            from_object=source_site, to_object=target_site,
            from_attribute=self.RELATIONSHIP_TEMPLATE.format(
                source.getPortalTypeName())))
