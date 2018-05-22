# For most cases it is easiest to reuse the test setup from nd.policy.

import unittest
import types
from zope.event import notify
from zope.lifecycleevent import ObjectCreatedEvent
from plone.uuid.interfaces import IUUID
from Products.CMFCore.utils import getToolByName

from resonate.utils import update_payload

from .. import testing


def fake_send(self, mail_text, *args, **kwargs):
    """
    mock up the send method so that emails do not actually get sent
    during unit tests.
    """
    if not hasattr(self, 'mails'):
        self.mails = []
    self.mails.append(mail_text)


class TestSyndication(testing.TestCase):

    def afterSetUp(self):
        self.portal.MailHost.send = types.MethodType(fake_send,
                                                     self.portal.MailHost)

    def add_and_approve_member(self):
        membrane = self.portal.membrane_tool
        member = self._createType(
            self.portal,
            'nd.content.member',
            'm1',
        )
        member.first_name = 'John'
        member.last_name = 'Smith'
        member.username = 'jsmith'
        member.email = 'john@example.org'
        notify(ObjectCreatedEvent(member))

        wft = self.portal.portal_workflow
        self.setRoles(('Reviewer', ))
        wft.doActionFor(member, 'approve')
        membrane.reindexObject(member)

        uid_c = self.portal.uid_catalog
        uid_c.manage_reindexIndex('UID')

        # give user contributor rights for portal
        self.folder.manage_setLocalRoles(
            member.unique_userid, ['Contributor', ])
        return member, member.unique_userid

    def test_accept_syndication_transition(self):
        self.loginAsPortalOwner()
        wft = getToolByName(self.portal, 'portal_workflow')

        types = [('nd.content.seminar',
                  'seminars',
                  lambda x: x.current_syndication_targets),
                 ('Event',
                  'events',
                  lambda x: x.getField('current_syndication_targets').get(x)),
                 ('News Item',
                  'news',
                  lambda x: x.getField('current_syndication_targets').get(x)),
                  ]

        for idx, _type in enumerate(types):
            typename, target, syndication_targets = _type
            _id = '%s_obj' + str(idx)

            # create source object and two organization foldes
            s1 = self._createType(self.portal, typename, _id % 's1')
            c1 = self._createType(self.portal, 'nd.content.center', _id % 'c1')
            c2 = self._createType(self.portal, 'nd.content.center', _id % 'c2')

            # perform accept_syndication transition
            wft.doActionFor(s1, "request_syndication")
            wft.doActionFor(s1, "accept_syndication", organizations=[c1, c2])

            self.assertTrue(c1[target].objectIds())
            self.assertTrue(c2[target].objectIds())

            p1 = c1[target].objectValues()[0]
            p2 = c2[target].objectValues()[0]

            self.assertEqual(p1.source_object, IUUID(s1))
            self.assertEqual(p2.source_object, IUUID(s1))
            self.assertEqual(len(syndication_targets(s1)), 2)

        self.logout()

    def test_reject_syndication_transition(self):
        self.loginAsPortalOwner()
        wft = getToolByName(self.portal, 'portal_workflow')

        types = [('nd.content.seminar',
                  'seminars',
                  lambda x: x.rejected_syndication_sites),
                 ('Event',
                  'events',
                  lambda x: x.getField('rejected_syndication_sites').get(x)),
                 ('News Item',
                  'news',
                  lambda x: x.getField('rejected_syndication_sites').get(x)),
                  ]

        for idx, _type in enumerate(types):
            typename, target, rejected_sites = _type
            _id = '%s_obj' + str(idx)

            # create source object and two organization foldes
            s1 = self._createType(self.portal, typename, _id % 's1')
            c1 = self._createType(self.portal, 'nd.content.center', _id % 'c1')
            self.assertFalse(rejected_sites(s1))

            # perform reject_syndication transition
            wft.doActionFor(s1, "request_syndication")
            wft.doActionFor(s1, "reject_syndication", organization=c1)

            self.assertEqual(len(rejected_sites(s1)), 1)

        self.logout()

    def test_request_move_transition(self):
        self.loginAsPortalOwner()
        wft = getToolByName(self.portal, 'portal_workflow')

        s1 = self._createType(self.portal, 'Event', 's1')
        c1 = self._createType(self.portal, 'nd.content.center', 'c1')
        wft.doActionFor(s1, "request_move", organization=IUUID(c1))

        self.assertEqual(wft.getStatusOf('syndication_workflow',
                                         s1)['organization'], IUUID(c1))
        self.logout()

    def test_accept_move_transition(self):
        wft = getToolByName(self.portal, 'portal_workflow')

        types = [('nd.content.seminar',
                  'seminars'),
                 ('Event',
                  'events'),
                 ('News Item',
                  'news'),
                  ]

        for idx, _type in enumerate(types):
            typename, target = _type
            _id = '%s_obj' + str(idx)

            self.loginAsPortalOwner()
            s1 = self._createType(self.portal, typename, _id % 's')
            c1 = self._createType(self.portal, 'nd.content.center', _id % 'c')

            self.assertFalse(c1.events.objectIds())

            wft.doActionFor(s1, "request_move", organization=IUUID(c1))
            self.logout()
            wft.doActionFor(s1, "move")
            self.assertIn(_id % 's', c1[target].objectIds())

    def test_syndication_notifications(self):
        self.loginAsPortalOwner()
        wft = getToolByName(self.portal, 'portal_workflow')

        s1 = self._createType(self.portal, 'Event', 's1')
        s2 = self._createType(self.portal, 'Event', 's2')
        c1 = self._createType(self.portal, 'nd.content.center', 'c1')
        m1, mid1 = self.add_and_approve_member()
        self.logout()

        self.assertFalse(getattr(self.portal.MailHost, 'mails', None))

        self.login(mid1)
        wft.doActionFor(s1, "request_syndication")
        wft.doActionFor(s2, "request_syndication")

        self.logout()
        self.loginAsPortalOwner()

        wft.doActionFor(s1, "reject_syndication", organization=c1)
        self.assertEqual(len(self.portal.MailHost.mails), 1)
        self.assertIn('John Smith', self.portal.MailHost.mails[0])
        self.assertIn('has not been approved', self.portal.MailHost.mails[0])

        wft.doActionFor(s2, "accept_syndication", organizations=[c1])
        self.assertEqual(len(self.portal.MailHost.mails), 2)
        self.assertIn('John Smith', self.portal.MailHost.mails[1])
        self.assertIn('has been approved', self.portal.MailHost.mails[1])

        self.logout()

    def test_syndication_digest_template(self):
        # create several items that will be syndicated
        self.loginAsPortalOwner()
        wft = getToolByName(self.portal, 'portal_workflow')

        c1 = self._createType(self.portal, 'nd.content.center', 'c1')
        c1.setTitle('Center1')
        c2 = self._createType(self.portal, 'nd.content.center', 'c2')
        c2.setTitle('Center2')
        c3 = self._createType(self.portal, 'nd.content.center', 'c3')
        c3.setTitle('Center3')

        s1 = self._createType(c1, 'Event', 's1')
        s1.setTitle('Event1')
        wft.doActionFor(s1, "publish")
        wft.doActionFor(s1, "request_syndication")
        s2 = self._createType(c1, 'Event', 's2')
        s2.setTitle('Event2')
        wft.doActionFor(s2, "request_move", organization=IUUID(c2))
        s3 = self._createType(c1, 'News Item', 's3')
        s3.setTitle('News Item1')
        wft.doActionFor(s3, "request_syndication")
        s4 = self._createType(c1, 'News Item', 's4')
        s4.setTitle('News Item2')
        wft.doActionFor(s4, "request_syndication")

        digest = c1.unrestrictedTraverse('@@digest_notification')
        payload = [(s1, c2)]
        digest.update(payload)
        self.assertEqual(digest.items[0]['title'], 'Event1')
        self.assertEqual(digest.items[0]['organization'], 'Center2')
        self.assertEqual(digest.items[0]['status'],
                         ['published', 'pending_syndication'])

        digest = c1.unrestrictedTraverse('@@digest_notification')
        payload = [(s2, c2)]
        digest.update(payload)
        self.assertEqual(digest.items[0]['title'], 'Event2')
        self.assertEqual(digest.items[0]['organization'], 'Center2')
        self.assertEqual(digest.items[0]['status'],
                         ['private', 'pending_move'])

        digest = c1.unrestrictedTraverse('@@digest_notification')
        payload = [(s1, c2),
                   (s2, c2),
                   (s3, c3),
                   (s4, c3)]
        digest.update(payload)
        self.assertEqual(len(digest.items), 4)

        self.logout()

    def test_syndication_digest_for_proxies(self):
        # create several items that will be syndicated
        self.loginAsPortalOwner()
        wft = getToolByName(self.portal, 'portal_workflow')

        c1 = self._createType(self.portal, 'nd.content.center', 'c1')
        c1.setTitle('Center1')
        c2 = self._createType(self.portal, 'nd.content.center', 'c2')
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

        c1 = self._createType(self.portal, 'nd.content.center', 'c1')
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
        self.assertIn("Last Changed (*)", html)
        self.assertIn("border=\"1\"", html)
        link = '<a href="http://nohost/plone/@@redirect-to-uuid/%s">Event1</a>'
        self.assertIn(link % IUUID(s1), html)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSyndication))
    return suite
