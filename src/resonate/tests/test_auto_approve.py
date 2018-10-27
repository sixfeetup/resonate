"""
Managers can set which target sites where syndication is auto-approved.
"""

from Products.CMFCore.utils import getToolByName

from plone.uuid import interfaces as uuid_ifaces

from Products.Archetypes.interfaces import referenceable

from .. import testing


class TestSyndication(testing.TestCase):
    __doc__

    def test_portal_referencable(self):
        """
        The portal supports Archetypes references.
        """
        portal_uid = uuid_ifaces.IUUID(self.portal)
        self.assertTrue(
            portal_uid,
            'Missing portal UID')
        uid_brains = self.portal.uid_catalog(UID=portal_uid)
        self.assertEqual(
            len(uid_brains), 1,
            'Wrong number of portal UID results in the catalog')
        portal_refs = referenceable.IReferenceable(self.portal)

        corge_news = self._createType(
            self.portal, 'News Item', 'corge-news-title')
        corge_refs = referenceable.IReferenceable(corge_news)
        portal_refs.addReference(corge_refs, relationship='from-portal')
        corge_refs.addReference(portal_refs, relationship='to-portal')

        self.assertTrue(
            portal_refs.getRefs('from-portal'),
            'Wrong number of refs from portal')
        self.assertTrue(
            portal_refs.getBRefs('to-portal'),
            'Wrong number of refs to portal')
        self.assertTrue(
            corge_refs.getBRefs('from-portal'),
            'Wrong number of refs from portal')
        self.assertTrue(
            corge_refs.getRefs('to-portal'),
            'Wrong number of refs to portal')

    def test_auto_approve_workflow(self):
        """
        The auto-approve automatic transition applies as appropriate.
        """
        foo_child_site = self._createChildSiteAndTarget(
            self.portal, 'foo-child-site', 'target', title='Foo Child Site')
        bar_child_site = self._createChildSiteAndTarget(
            self.portal, 'bar-child-site', 'target', title='Bar Child Site')
        qux_child_site = self._createChildSiteAndTarget(
            self.portal, 'qux-child-site', 'target', title='Qux Child Site')

        portal_refs = referenceable.IReferenceable(self.portal)
        for child_site in (foo_child_site, qux_child_site):
            portal_refs.addReference(
                referenceable.IReferenceable(child_site),
                relationship='resonate.auto-approve.News Item')

        corge_news = self._createType(
            self.portal, 'News Item', 'corge-news-title')
        grault_event = self._createType(
            self.portal, 'Event', 'grault-event')

        # Request and approve the non-auto-approve site first so that we can
        # confirm auto-approval triggers the state change on the source
        # objects when all requests are approved.
        workflow = getToolByName(self.portal, 'portal_workflow')
        for content in corge_news, grault_event:
            workflow.doActionFor(
                content, "request_syndication", organizations=[
                    uuid_ifaces.IUUID(bar_child_site)])
        news_state = workflow.getInfoFor(
            bar_child_site.target[corge_news.getId()],
            'syndication_state')
        self.assertEqual(
            news_state, 'pending_syndication',
            'Wrong unapproved syndication workflow state')
        self.assertEqual(
            workflow.getInfoFor(corge_news, 'syndication_state'),
            'pending_syndication',
            'Wrong unapproved syndication source workflow state')

        self.setRoles(('Manager', ))
        workflow.doActionFor(
            bar_child_site.target[corge_news.getId()], "accept_syndication")
        for content in corge_news, grault_event:
            workflow.doActionFor(
                content, "request_syndication", organizations=[
                    uuid_ifaces.IUUID(foo_child_site),
                    uuid_ifaces.IUUID(qux_child_site)])

        for child_site in [foo_child_site, bar_child_site, qux_child_site]:
            for content in corge_news, grault_event:
                self.assertIn(
                    content.getId(), child_site.target.objectIds(),
                    'Content missing from target site after request')

            news_proxy = child_site.target[corge_news.getId()]
            self.assertEqual(
                workflow.getInfoFor(news_proxy, 'syndication_state'),
                'syndicated',
                'Wrong auto-approved syndication workflow state')
            self.assertEqual(
                workflow.getInfoFor(news_proxy, 'review_state'),
                'published',
                'Wrong auto-approved syndication workflow state')
            self.assertEqual(
                workflow.getInfoFor(corge_news, 'syndication_state'),
                'syndicated',
                'Wrong auto-approved syndicated source workflow state')

            event_state = workflow.getInfoFor(
                child_site.target[grault_event.getId()],
                'syndication_state')
            self.assertEqual(
                event_state, 'pending_syndication',
                'Wrong unapproved syndication workflow state')

        for child_site in [foo_child_site, qux_child_site]:
            news_state = workflow.getInfoFor(
                child_site.target[corge_news.getId()],
                'syndication_state')
            self.assertEqual(
                news_state, 'syndicated',
                'Wrong auto-approved syndication workflow state')
