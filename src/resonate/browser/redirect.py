"""
Redirect to the source object's URL, if current user doesn't have permission
to edit the proxy
"""

from Acquisition import aq_parent

from Products.CMFCore.utils import getToolByName
from plone.dexterity.browser.view import DefaultView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFCore.permissions import ModifyPortalContent
from Products.statusmessages.interfaces import IStatusMessage

from .. import utils


class ProxyRedirect(DefaultView):
    index = ViewPageTemplateFile('templates/proxy.pt')

    def __call__(self):
        context = self.context
        mtool = getToolByName(context, 'portal_membership')
        can_edit = mtool.checkPermission(ModifyPortalContent, context)

        if can_edit:
            return super(ProxyRedirect, self).__call__()
        else:
            source_url = utils.get_proxy_source(context).virtual_url_path()
            return context.REQUEST.RESPONSE.redirect('/' + source_url)


class TransitionRedirectParentView(object):
    """
    Perform the workflow transition and then redirect to the parent.

    Useful for situations where the transition results in the removal of the
    object being transitioned such as the reject transitions.
    """

    def __call__(self, workflow_action):
        """
        Perform the workflow transition and then redirect to the parent.

        Useful for situations where the transition results in the removal of
        the object being transitioned such as the reject transitions.

        """
        workflow = getToolByName(self.context, 'portal_workflow')
        action_info = workflow.getActionInfo(
            'workflow/' + workflow_action, self.context)
        workflow.doActionFor(self.context, workflow_action)

        parent = aq_parent(self.context)
        msg = 'The "{0}" action was successful on "{1}"'.format(
            action_info['title'], self.context.title_or_id())
        IStatusMessage(self.request).addStatusMessage(msg, type='info')
        return self.request.RESPONSE.redirect(parent.absolute_url())
