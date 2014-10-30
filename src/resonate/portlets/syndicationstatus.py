from zope.interface import implements
from AccessControl.unauthorized import Unauthorized

from plone.portlets.interfaces import IPortletDataProvider
from plone.app.portlets.portlets import base
from plone.app.layout.navigation.root import getNavigationRoot
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFCore.utils import getToolByName
from Products.Archetypes.interfaces import IBaseObject

from resonate import MessageFactory as _
from resonate.utils import getRefs


class ISyndicationStatusPortlet(IPortletDataProvider):
    """A portlet

    It inherits from IPortletDataProvider because for this portlet, the
    data that is being rendered and the portlet assignment itself are the
    same.
    """


class Assignment(base.Assignment):
    """Portlet assignment.
    """

    implements(ISyndicationStatusPortlet)

    def __init__(self):
        pass


class Renderer(base.Renderer):
    """Portlet renderer.

    This is registered in configure.zcml. The referenced page template is
    rendered, and the implicit variable 'view' will refer to an instance
    of this class. Other methods can be added and referenced in the template.
    """

    render = ViewPageTemplateFile('syndicationstatus.pt')

    def _get_targets_by_state(self, state):
        if IBaseObject.providedBy(self.context):
            proxies = getRefs(self.context, 'current_syndication_targets')
        else:
            proxies = []

        organization_paths = set()
        wft = getToolByName(self.context, 'portal_workflow')
        for proxy in proxies:
            status = wft.getInfoFor(proxy, 'review_state')
            if status != state:
                continue
            path = getNavigationRoot(proxy)
            if not path:
                continue
            organization_paths.add(path)

        organizations = []
        for path in organization_paths:
            try:
                organizations.append(self.context.restrictedTraverse(path))
            except Unauthorized:
                pass

        return organizations

    def syndication_targets(self):
        return self._get_targets_by_state('published')

    def submitted_syndications(self):
        return self._get_targets_by_state('pending')

    def rejected_syndications(self):
        if IBaseObject.providedBy(self.context):
            rejected = getRefs(self.context, 'rejected_syndication_sites')
        else:
            rejected = []
        return rejected

    @property
    def available(self):
        mtool = getToolByName(self.context, 'portal_membership')
        member = mtool.getAuthenticatedMember()
        if not member.has_permission('Review portal content', self.context):
            return False
        elif (self.syndication_targets()
              or self.submitted_syndications()
              or self.rejected_syndications()):
            return True
        else:
            return False

    @property
    def title(self):
        """This property is used to give the title of the portlet in the
        "manage portlets" screen.
        """
        return _(u"Syndication status")


class AddForm(base.NullAddForm):
    """Portlet add form.
    """

    def create(self):
        return Assignment()
