"""
Browser views for source and target sites, the portal itself and child sites.
"""

from zope import component
from zope.schema import interfaces as schema_ifaces

from Products.statusmessages import interfaces as status_ifaces

from plone import api

from .. import utils
from . import status


class ResonateSiteAutoApproveForm(object):
    """
    Browser form to designate sites where syndication is auto-approved.
    """

    RELATIONSHIP_TEMPLATE = (
        status.SyndicationProxyStatusView.RELATIONSHIP_TEMPLATE)

    def __call__(self):
        """
        Render the form or handle a submission.
        """
        if 'submit' in self.request.form:
            catalog = api.portal.get_tool('portal_catalog')
            for portal_type in self.syndication_types():
                relationship = self.RELATIONSHIP_TEMPLATE.format(
                    portal_type.getId())
                for target_site_uuid in self.request.form.get(
                        portal_type.getId(), []):
                    target_site = catalog(UID=target_site_uuid)[0].getObject()
                    if not utils.getRelations(
                            from_object=self.context, to_object=target_site,
                            from_attribute=relationship):
                        utils.addRelation(
                            self.context, target_site, relationship)

            status = status_ifaces.IStatusMessage(self.request)
            status.addStatusMessage(
                'Auto-approve target sites designated successfully')

            return self.request.RESPONSE.redirect(self.context.absolute_url())

        return super(ResonateSiteAutoApproveForm, self).__call__()

    def can_designate_auto_approve(self):
        """
        Is it possible to designate auto-approval sites?

        Are there types with the syndication workflow and are there more than
        one source/target site available.
        """
        return bool(self.syndication_types() and self.target_sites())

    def syndication_types(self):
        """
        Which portal types is syndication enabled for.
        """
        types = api.portal.get_tool('portal_types')
        workflow = api.portal.get_tool('portal_workflow')
        return [
            portal_type for portal_type in types.listTypeInfo()
            if 'syndication_source_workflow' in workflow.getChainFor(
                    portal_type.getId())]

    def target_sites(self):
        """
        Lookup the sites that can be targets for this site.
        """
        org_vocab = component.getUtility(
            schema_ifaces.IVocabularyFactory,
            'resonate.vocabulary.childsites')
        return org_vocab(self.context)

    def designated_target_sites(self, portal_type):
        """
        Which target sites have been designated for this portal content type.
        """
        return [relation.to_object for relation in utils.getRelations(
            from_object=self.context,
            from_attribute=self.RELATIONSHIP_TEMPLATE.format(portal_type))]
