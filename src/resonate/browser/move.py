import logging

from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from Products.statusmessages.interfaces import IStatusMessage

from .. import utils
from resonate.content.proxy import IProxy
from resonate.utils import get_organizations_by_target


logger = logging.getLogger(__name__)


class MoveContent(BrowserView):
    """This is a view that simply triggers the move transition,
    then redirects the user to the new location.
    """

    def __call__(self):
        """Process the move transition.
        """
        if not IProxy.providedBy(self.context):
            msg = 'You must accept the move from the destination target.'
            IStatusMessage(self.request).addStatusMessage(msg, type='error')
            return

        wf_tool = getToolByName(self.context, 'portal_workflow')
        source_obj = utils.get_proxy_source(self.context)
        history = wf_tool.getHistoryOf('syndication_source_workflow', source_obj)
        wf_tool.doActionFor(self.context, 'move')

        # Get the last request_move organization
        target_org_uid = None
        for h in reversed(history):
            if h['action'] == 'request_move':
                target_org_uid = h['organization']
                break

        if target_org_uid:
            organizations = get_organizations_by_target(source_obj,
                                                        target_org_uid)
            target = organizations.values()[0]
            new_obj = target[utils.get_proxy_source(self.context).getId()]
            new_url = new_obj.absolute_url()
            msg = 'Successfully moved "%s"' % source_obj.title_or_id()
            IStatusMessage(self.request).addStatusMessage(msg, type='info')
            return self.request.RESPONSE.redirect(new_url)
