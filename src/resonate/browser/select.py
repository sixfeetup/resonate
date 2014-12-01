import logging

from AccessControl import ClassSecurityInfo
from Acquisition import aq_inner
from zope.component import getUtility
from zope.component import getMultiAdapter
from zope.component.hooks import getSite
from zope.schema.interfaces import IVocabularyFactory

from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView
from Products.statusmessages.interfaces import IStatusMessage

from plone.app.layout.navigation.root import getNavigationRoot

from resonate.utils import getRefs
from resonate.utils import get_organizations_by_target
from resonate.utils import safe_uid

logger = logging.getLogger(__name__)


class SelectOrganizations(BrowserView):
    """This is a form that asks the user what organization they
    would like to syndicate the current item upon using a specific
    transition.
    """
    security = ClassSecurityInfo()

    security.declareProtected('cmf.ReviewPortalContent', '__call__')

    def __call__(self):
        """Show or process the form
        """
        context = aq_inner(self.context)
        # The standard workflow action url
        wf_url = '%s/content_status_modify?workflow_action=%s'
        status = IStatusMessage(self.request)
        not_supported_msg = (
            'This item does not support the syndication workflow.'
        )
        # Get the transition name from the request (see the action url)
        current_transition = self.request.get('transition', None)
        submitted = self.request.form.get('submit', None)

        wf_tool = getToolByName(self, 'portal_workflow')

        # If the form hasn't been submitted, just return the template
        if submitted is None and not self.organization_uids:
            return self.index()

        # Make sure that they selected an option
        no_org = not self.organization_uids
        if submitted is not None and no_org:
            msg = 'You must choose an organization.'
            status.addStatusMessage(msg, type='error')
            return self.index()

        wf_chain = wf_tool.getChainFor(context)
        # A check to make sure this item has the syndication_workflow applied,
        # if not, just do the standard action
        if 'syndication_workflow' not in wf_chain:
            status.addStatusMessage(not_supported_msg, type='warn')
            if current_transition is None:
                return self.request.RESPONSE.redirect(self.default_view_url)
            else:
                # Use the standard action url
                return self.request.RESPONSE.redirect(
                    wf_url % (context.absolute_url(), current_transition))

        if self.target_proxies:
            # If the proxy already exists in this organization,
            # return
            msg = u'Item is already syndicated to this organization.'
            status.addStatusMessage(msg, type='error')
            return self.index()

        if current_transition == 'request_move':
            wf_tool.doActionFor(context, 'request_move',
                                organization=self.organization_uids[0])
        elif current_transition == 'request_syndication':
            wf_tool.doActionFor(context, 'request_syndication',
                                organizations=self.organization_uids)

        return self.request.RESPONSE.redirect(self.default_view_url)

    def available_organizations(self):
        """Return a list of available organizations to syndicate content to,
        formatted for display as a combo-box.
        """

        org_vocab = getUtility(IVocabularyFactory,
                               'resonate.vocabulary.childsites')
        terms = org_vocab(self.context)

        portal = getSite()
        nav_root_path = getNavigationRoot(self.context)
        nav_root = portal.restrictedTraverse(nav_root_path)
        nav_root_uid = safe_uid(nav_root)

        # Get all org uids except the one we are in
        org_uids = set(terms.by_value.keys()) - set((nav_root_uid,))
        existing_orgs = set([
            tp.containing_organization
            for tp in self.target_proxies
        ])
        org_uids = org_uids - existing_orgs
        organizations = get_organizations_by_target(
            self.context,
            list(org_uids),
        )
        result = []
        for organization in organizations:
            try:
                term = terms.getTerm(safe_uid(organization))
            except LookupError:
                continue
            result.append(term)

        return result

    @property
    def target_proxies(self):
        pc = getToolByName(self, 'portal_catalog')
        current_syndication_targets = getRefs(self.context,
                                              'current_syndication_targets')
        kw = dict(
            portal_type='resonate.proxy',
            UID=[safe_uid(t)
                 for t in current_syndication_targets],
        )
        if self.organization_uids:
            # Verify this object has not already been syndicated to the
            # requested organization
            kw['containing_organization'] = self.organization_uids
        target_proxies = pc(**kw)
        return target_proxies

    @property
    def organization_uids(self):
        # The list of organizations to syndicate this content to
        organization_uids = self.request.form.get('organizations', [])
        # Be sure that we have a list and not string:
        if isinstance(organization_uids, basestring):
            organization_uids = [organization_uids]
        return organization_uids

    @property
    def default_view_url(self):
        context = aq_inner(self.context)
        cstate = getMultiAdapter(
            (context, self.request),
            name='plone_context_state',
        )
        return cstate.view_url()
