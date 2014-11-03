"""
Redirect to the source object's URL, if current user doesn't have permission
to edit the proxy
"""
from Products.CMFCore.utils import getToolByName
from plone.dexterity.browser.view import DefaultView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFCore.permissions import ModifyPortalContent


class ProxyRedirect(DefaultView):
    index = ViewPageTemplateFile('templates/proxy.pt')

    def __call__(self):
        context = self.context
        mtool = getToolByName(context, 'portal_membership')
        can_edit = mtool.checkPermission(ModifyPortalContent, context)

        if can_edit:
            return super(ProxyRedirect, self).__call__()
        else:
            source_url = context.source_object.to_object.virtual_url_path()
            return context.REQUEST.RESPONSE.redirect('/' + source_url)
