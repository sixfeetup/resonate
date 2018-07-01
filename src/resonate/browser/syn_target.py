"""
A utility browser view for managing syndication targets.
"""

from Acquisition import aq_parent

from Products.Five import browser

from Products.CMFPlone import utils

from .. import behaviors


class SynTargetTool(browser.BrowserView):
    """
    A utility browser view for managing syndication targets.
    """

    def __init__(self, context, request):
        """
        Capture the context and request.
        """
        super(SynTargetTool, self).__init__(context, request)
        self.context = self._get_context(context, request)

    def _get_context(self, context, request):
        """
        Walk up parents until a non-default-page is found.
        """
        if not context:
            return None
        if utils.isDefaultPage(context, request):
            return self._get_context(aq_parent(context), request)
        return context

    @property
    def disabled(self):
        """True, if context is not a lineage subsite but could possibly be one.
        """
        return not self.enabled

    @property
    def enabled(self):
        """True, if context is a lineage subsite.
        """
        return behaviors.ISyndicationTarget.providedBy(self.context)

    def enable(self):
        """Enable a lineage subsite on this context.
        """
        behaviors.enable_syn_target(self.context)

        # redirect
        self.request.response.redirect(self.context.absolute_url())

    def disable(self):
        """Disable a lineage subsite on this context.
        """
        behaviors.disable_syn_target(self.context)

        # redirect
        self.request.response.redirect(self.context.absolute_url())
