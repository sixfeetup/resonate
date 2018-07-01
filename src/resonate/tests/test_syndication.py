# For most cases it is easiest to reuse the test setup from nd.policy.

import unittest

from zope import interface

from plone.uuid.interfaces import IUUID
from Products.CMFCore.utils import getToolByName

from plone.app import testing as plone_testing

from collective.lineage import utils as lineage_utils

from resonate.utils import update_payload
from .. import behaviors

from .. import testing


class TestSyndication(testing.TestCase):

    def add_and_approve_member(self):
        registration = getToolByName(self.portal, 'portal_registration')
        member = registration.addMember(
            'first_member', plone_testing.TEST_USER_PASSWORD)
        # give user contributor rights for portal
        self.folder.manage_setLocalRoles(member.id, ['Contributor', ])
        return member, member.id

    def _createChildSiteAndTarget(self, context, id_, target):
        """
        Create a container as a navigation root with a child site target.
        """
        obj = self._createType(context, 'Folder', id_)
        lineage_utils.enable_childsite(obj)
        target_obj = self._createType(obj, 'Folder', target)
        interface.alsoProvides(target_obj, behaviors.ISyndicationTarget)
        target_obj.reindexObject()
        return obj

    def test_accept_syndication_transition(self):
        self.loginAsPortalOwner()
        wft = getToolByName(self.portal, 'portal_workflow')

        types = [
            ('Folder',
             'seminars',
             lambda x: x.current_syndication_targets),
            ('Event',
             'events',
             lambda x: x.current_syndication_targets),
            ('News Item',
             'news',
             lambda x: x.current_syndication_targets),
        ]

        for idx, _type in enumerate(types):
            typename, target, syndication_targets = _type
            _id = '%s_obj' + str(idx)

            # create source object and two organization foldes
            s1 = self._createType(self.portal, typename, _id % 's1')
            c1 = self._createChildSiteAndTarget(
                self.portal, _id % 'c1', target)
            c2 = self._createChildSiteAndTarget(
                self.portal, _id % 'c2', target)

            # perform accept_syndication transition
            wft.doActionFor(
                s1, "request_syndication",
                organizations=[IUUID(c1), IUUID(c2)])
            self.assertTrue(c1[target].objectIds())
            self.assertTrue(c2[target].objectIds())

            p1 = c1[target].objectValues()[0]
            wft.doActionFor(p1, "accept_syndication")
            p2 = c2[target].objectValues()[0]
            wft.doActionFor(p2, "accept_syndication")

            self.assertEqual(IUUID(p1.source_object.to_object), IUUID(s1))
            self.assertEqual(IUUID(p2.source_object.to_object), IUUID(s1))
            self.assertEqual(len(syndication_targets(s1)), 2)

        self.logout()

    def test_reject_syndication_transition(self):
        self.loginAsPortalOwner()
        wft = getToolByName(self.portal, 'portal_workflow')

        types = [
            ('Folder',
             'seminars',
             lambda x: x.rejected_syndication_sites),
            ('Event',
             'events',
             lambda x: x.rejected_syndication_sites),
            ('News Item',
             'news',
             lambda x: x.rejected_syndication_sites),
        ]

        for idx, _type in enumerate(types):
            typename, target, rejected_sites = _type
            _id = '%s_obj' + str(idx)

            # create source object and two organization foldes
            s1 = self._createType(self.portal, typename, _id % 's1')
            c1 = self._createChildSiteAndTarget(
                self.portal, _id % 'c1', target)
            self.assertFalse(rejected_sites(s1))

            # perform reject_syndication transition
            wft.doActionFor(s1, "request_syndication", organization=IUUID(c1))
            p1 = c1[target][s1.id]
            wft.doActionFor(p1, "reject_syndication")

            self.assertEqual(len(rejected_sites(s1)), 1)

        self.logout()

    def test_request_move_transition(self):
        self.loginAsPortalOwner()
        wft = getToolByName(self.portal, 'portal_workflow')

        s1 = self._createType(self.portal, 'Event', 's1')
        c1 = self._createType(self.portal, 'Folder', 'c1')
        wft.doActionFor(s1, "request_move", organization=IUUID(c1))

        self.assertEqual(wft.getStatusOf('syndication_workflow',
                                         s1)['organization'], IUUID(c1))
        self.logout()

    def test_accept_move_transition(self):
        wft = getToolByName(self.portal, 'portal_workflow')

        types = [
            ('Folder', 'seminars'),
            ('Event', 'events'),
            ('News Item', 'news'),
        ]

        self.loginAsPortalOwner()
        for idx, _type in enumerate(types):
            typename, target = _type
            _id = '%s_obj' + str(idx)

            s1 = self._createType(self.portal, typename, _id % 's')
            c1 = self._createChildSiteAndTarget(
                self.portal, _id % 'c1', target)
            c2 = self._createChildSiteAndTarget(
                self.portal, _id % 'c2', target)

            # perform accept_syndication transition
            wft.doActionFor(
                s1, "request_syndication", organizations=[IUUID(c2)])
            p2 = c2[target].objectValues()[0]
            wft.doActionFor(p2, "accept_syndication")

            self.assertFalse(c1[target].objectIds())

            wft.doActionFor(s1, "request_move", organization=IUUID(c1))
            p1_id = (_id % 's') + '-proxy'
            self.assertIn(p1_id, c1[target].objectIds())
            p1 = c1[target][p1_id]
            wft.doActionFor(p1, "move")
            self.assertNotIn(s1.id, self.portal.objectIds())

    def test_syndication_notifications(self):
        self.portal.notification_emails = (
            'John Smith <john.smith@example.com>')

        self.loginAsPortalOwner()
        wft = getToolByName(self.portal, 'portal_workflow')

        self.folder = self._createType(self.portal, 'Folder', 'foo_folder')
        s1 = self._createType(self.portal, 'Event', 's1')
        s2 = self._createType(self.portal, 'Event', 's2')
        c1 = self._createChildSiteAndTarget(
            self.portal, 'c1', 'target')
        m1, mid1 = self.add_and_approve_member()

        self.assertFalse(getattr(self.portal.MailHost, 'messages', None))

        wft.doActionFor(s1, "request_syndication", organization=IUUID(c1))
        wft.doActionFor(s2, "request_syndication", organizations=[IUUID(c1)])

        self.portal.MailHost.messages[:] = []
        wft.doActionFor(c1.target[s1.id], "reject_syndication")
        self.assertEqual(len(self.portal.MailHost.messages), 1)
        self.assertIn(
            'John Smith', str(self.portal.MailHost.messages[0]))

        wft.doActionFor(c1.target[s2.id], "accept_syndication")
        self.assertEqual(len(self.portal.MailHost.messages), 2)
        self.assertIn(
            'John Smith', str(self.portal.MailHost.messages[1]))

    def test_syndication_digest_for_proxies(self):
        # create several items that will be syndicated
        self.loginAsPortalOwner()
        wft = getToolByName(self.portal, 'portal_workflow')

        c1 = self._createChildSiteAndTarget(
            self.portal, 'c1', 'events')
        c1.setTitle('Center1')
        c2 = self._createChildSiteAndTarget(
            self.portal, 'c2', 'events')
        c2.setTitle('Center2')

        s1 = self._createType(c1, 'Event', 's1')
        s1.setTitle('Event1')
        wft.doActionFor(s1, "publish")
        wft.doActionFor(s1, "request_syndication")
        wft.doActionFor(s1, "accept_syndication")

        p1 = self._createType(c2.events, 'resonate.proxy', 'p1')

        digest = c1.unrestrictedTraverse('@@digest_notification')
        payload = {
            'object_uid': IUUID(s1),
            'organization_title': 'Center1',
            'organization_uid': IUUID(c1)}
        digest.update(payload)
        self.assertEqual(len(digest.items_by_uid.keys()), 1)
        payload = {
            'object_uid': IUUID(p1),
            'organization_title': 'Center2',
            'organization_uid': IUUID(c2)}
        digest.update(payload)
        self.assertEqual(len(digest.items_by_uid.keys()), 2)

    def test_syndication_digest_template_rendering(self):
        self.loginAsPortalOwner()
        wft = getToolByName(self.portal, 'portal_workflow')

        c1 = self._createType(self.portal, 'Folder', 'c1')
        c1.setTitle('Center1')

        s1 = self._createType(c1, 'Event', 's1')
        s1.setTitle('Event1')
        wft.doActionFor(s1, "publish")
        wft.doActionFor(s1, "request_syndication")

        digest = c1.unrestrictedTraverse('@@digest_notification')
        payload = {
            'object_uid': IUUID(s1),
            'organization_title': 'Center1',
            'organization_uid': IUUID(c1)}
        update_payload(s1, payload)
        digest.update(payload)
        html = digest()
        self.assertIn("Last Changed", html)
        link = (
            '<a href="http://nohost/plone/@@redirect-to-uuid/%s">%s</a>')
        self.assertIn(link % (IUUID(s1), c1.Title()), html)

    def test_adding_syndication_source_behavior(self):
        """
        The syndication source behavior can be added to a content type:

        Without removing other behaviors.
        """
        types = getToolByName(self.portal, 'portal_types')
        behaviors = types['Document'].behaviors
        self.assertIn(
            'plone.app.content.interfaces.INameFromTitle', behaviors,
            'Default behaviors removed')
        self.assertIn(
            'resonate.behaviors.ISyndicationSource', behaviors,
            'Missing the syndication source behavior')

    def test_choosing_child_sites(self):
        """
        The selection view lists lineage child sites.
        """
        workflow = getToolByName(self.portal, 'portal_workflow')
        self.loginAsPortalOwner()

        foo_child_site = self._createChildSiteAndTarget(
            self.portal, 'foo-child-site', 'target')
        workflow.doActionFor(foo_child_site, 'publish')
        foo_event = self._createType(foo_child_site, 'Event', 'foo-event')
        workflow.doActionFor(foo_event, 'publish')

        bar_child_site = self._createChildSiteAndTarget(
            self.portal, 'bar-child-site', 'target')
        workflow.doActionFor(bar_child_site, 'publish')

        select_view = foo_event.unrestrictedTraverse(
            '@@select-organizations')
        available_organizations = select_view.available_organizations()

        self.assertTrue(
            available_organizations,
            'No child sites listed')
        self.assertEqual(
            available_organizations[0].token, bar_child_site.UID(),
            'Wrong child site UID token')


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSyndication))
    return suite
