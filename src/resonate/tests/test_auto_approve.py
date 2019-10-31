"""
Managers can set which target sites where syndication is auto-approved.
"""

import transaction

from Products.CMFCore.utils import getToolByName

from plone.uuid import interfaces as uuid_ifaces

from .. import utils
from .. import testing


class TestSyndication(testing.TestCase):
    __doc__

    def test_portal_relatable(self):
        """
        The portal supports relations.
        """
        corge_news = self._createType(
            self.portal, 'News Item', 'corge-news-title')
        utils.addRelation(
            from_object=self.portal, to_object=corge_news,
            from_attribute='from-portal')
        utils.addRelation(
            from_object=corge_news, to_object=self.portal,
            from_attribute='to-portal')

        self.assertTrue(
            utils.getRelations(
                from_object=self.portal, from_attribute='from-portal'),
            'Wrong number of rels from portal')
        self.assertTrue(
            utils.getRelations(
                to_object=self.portal, from_attribute='to-portal'),
            'Wrong number of rels to portal')
        self.assertTrue(
            utils.getRelations(
                to_object=corge_news, from_attribute='from-portal'),
            'Wrong number of rels from portal')
        self.assertTrue(
            utils.getRelations(
                from_object=corge_news, from_attribute='to-portal'),
            'Wrong number of rels to portal')

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

        for child_site in (foo_child_site, qux_child_site):
            utils.addRelation(
                from_object=self.portal, to_object=child_site,
                from_attribute='resonate.auto-approve.News Item')

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

    def test_auto_approve_form(self):
        """
        The auto-approve action and form set relations.
        """
        foo_child_site = self._createChildSiteAndTarget(
            self.portal, 'foo-child-site', 'target', title='Foo Child Site')
        bar_child_site = self._createChildSiteAndTarget(
            self.portal, 'bar-child-site', 'target', title='Bar Child Site')
        qux_child_site = self._createChildSiteAndTarget(
            self.portal, 'qux-child-site', 'target')

        transaction.commit()
        self.setUpBrowser()
        self.browser.open(self.portal.absolute_url())
        self.browser.getLink(
            'Designate Syndication Auto-Approve Targets').click()
        form = self.browser.getForm('resonate.auto-approve')
        news_ctl = form.getControl(name='News Item:list')
        news_ctl.getControl(foo_child_site.Title()).selected = True
        self.assertFalse(
            news_ctl.getControl(bar_child_site.Title()).selected,
            'Child site selected by default')
        form.getControl('Designate Auto-Approve Sites').click()
        self.assertEqual(
            self.browser.url, self.portal.absolute_url(),
            'Wrong redirect after designating child sites')
        self.assertIn(
            'Auto-approve target sites designated successfully',
            self.browser.contents,
            'Wrong or missing success message')

        self.browser.getLink(
            'Designate Syndication Auto-Approve Targets').click()
        form = self.browser.getForm('resonate.auto-approve')
        news_ctl = form.getControl(name='News Item:list')
        news_ctl.getControl(qux_child_site.getId()).selected = True
        form.getControl('Designate Auto-Approve Sites').click()
        self.assertIn(
            'Auto-approve target sites designated successfully',
            self.browser.contents,
            'Wrong or missing success message')

        news_rels = [news_rel.to_object for news_rel in utils.getRelations(
            from_object=self.portal,
            from_attribute='resonate.auto-approve.News Item')]
        self.assertEqual(
            news_rels, [foo_child_site, qux_child_site],
            'Wrong auto-approve relations after submitting form')
        event_rels = utils.getRelations(
            from_object=self.portal,
            from_attribute='resonate.auto-approve.Event')
        self.assertFalse(
            event_rels,
            'Auto-approve relations set for wrong type')

        self.browser.getLink(
            'Designate Syndication Auto-Approve Targets').click()
        form = self.browser.getForm('resonate.auto-approve')
        news_ctl = form.getControl(name='News Item:list')
        self.assertTrue(
            news_ctl.getControl(foo_child_site.Title()).selected,
            'Existing values not preserved on form')
