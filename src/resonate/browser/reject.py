import logging

from Acquisition import aq_parent
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from Products.statusmessages.interfaces import IStatusMessage

logger = logging.getLogger(__name__)


class RejectSyndication(BrowserView):
    """This is a view that simply triggers the reject transition,
    then redirects the user to the new location.
    """

    def __call__(self):
        """Process the move transition.
        """
        wf_tool = getToolByName(self.context, 'portal_workflow')
        wf_tool.doActionFor(self.context, 'reject_syndication')

        parent = aq_parent(self.context)
        msg = 'Successfully rejected "%s"' % self.context.title_or_id()
        IStatusMessage(self.request).addStatusMessage(msg, type='info')
        return self.request.RESPONSE.redirect(parent.absolute_url())
