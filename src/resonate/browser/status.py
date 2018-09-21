"""
Browser views for syndication status.
"""

from Products.CMFCore.utils import getToolByName

from Products.Archetypes.interfaces import referenceable


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

        targets = referenceable.IReferenceable(source).getRefs(
            relationship='current_syndication_targets')
        return bool([
            target for target in targets
            if workflow.getInfoFor(
                    target, 'syndication_state') == 'syndicated'])

    def is_pending_syndication(self):
        """
        Determine if this source has any pending requests for syndication.
        """
        workflow = getToolByName(self.context, 'portal_workflow')
        source = self.context

        targets = referenceable.IReferenceable(source).getRefs(
            relationship='current_syndication_targets')
        return bool([
            target for target in targets
            if workflow.getInfoFor(
                    target, 'syndication_state') == 'pending_syndication'])

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

        targets = referenceable.IReferenceable(source).getRefs(
            relationship='current_syndication_targets')
        return bool([
            target for target in targets
            if workflow.getInfoFor(
                    target, 'syndication_move_state') == 'moved'])

    def is_pending_move(self):
        """
        Determine if this source has any pending requests for move.
        """
        workflow = getToolByName(self.context, 'portal_workflow')
        source = self.context

        targets = referenceable.IReferenceable(source).getRefs(
            relationship='current_syndication_targets')
        return bool([
            target for target in targets
            if workflow.getInfoFor(
                    target, 'syndication_move_state') == 'pending_move'])

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
