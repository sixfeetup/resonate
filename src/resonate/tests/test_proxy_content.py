# For most cases it is easiest to reuse the test setup from nd.policy.

import unittest
from z3c.relationfield import RelationValue
from zope.app.intid.interfaces import IIntIds
from zope.event import notify
from zope.component import getUtility
from zope.lifecycleevent import ObjectModifiedEvent
from plone.uuid.interfaces import IUUID
from Products.CMFCore.utils import getToolByName

from .. import testing


class TestProxyContent(testing.TestCase):

    def test_source_object_removed(self):
        # create source object and related with proxy
        p1 = self._createType(self.portal, 'resonate.proxy', 'p1')
        p2 = self._createType(self.portal, 'resonate.proxy', 'p2')
        p3 = self._createType(self.portal, 'resonate.proxy', 'p3')
        p4 = self._createType(self.portal, 'resonate.proxy', 'p4')

        # Event source object
        s1 = self._createType(self.portal, 'Event', 's1')
        s1targets = s1.getField('current_syndication_targets')
        s1targets.set(s1, [IUUID(p1), IUUID(p2)])

        p1.source_object = RelationValue(getUtility(IIntIds).getId(s1))
        notify(ObjectModifiedEvent(p1))
        p2.source_object = RelationValue(getUtility(IIntIds).getId(s1))
        notify(ObjectModifiedEvent(p2))

        self.portal.manage_delObjects(ids=['s1'])
        self.assertNotIn('p1', self.portal.objectIds())
        self.assertNotIn('p2', self.portal.objectIds())

        # Seminar source object
        s2 = self._createType(self.portal, 'Folder', 's2')
        s2.current_syndication_targets = [IUUID(p3), IUUID(p4)]

        p3.source_object = RelationValue(getUtility(IIntIds).getId(s2))
        notify(ObjectModifiedEvent(p3))
        p4.source_object = RelationValue(getUtility(IIntIds).getId(s2))
        notify(ObjectModifiedEvent(p4))

        self.portal.manage_delObjects(ids=['s2'])
        self.assertNotIn('p3', self.portal.objectIds())
        self.assertNotIn('p4', self.portal.objectIds())

    def test_source_object_title_modified(self):
        # create source object and related with proxy
        p1 = self._createType(self.portal, 'resonate.proxy', 'p1')
        p2 = self._createType(self.portal, 'resonate.proxy', 'p2')
        p3 = self._createType(self.portal, 'resonate.proxy', 'p3')
        p4 = self._createType(self.portal, 'resonate.proxy', 'p4')

        # Event source object
        s1 = self._createType(self.portal, 'Event', 's1')
        s1.setTitle('Old title')
        notify(ObjectModifiedEvent(s1))

        s1targets = s1.getField('current_syndication_targets')
        s1targets.set(s1, [IUUID(p1), IUUID(p2)])

        self.assertNotEqual(p1.title, 'New title')
        self.assertNotEqual(p2.title, 'New title')

        s1.setTitle('New title')
        notify(ObjectModifiedEvent(s1))
        self.assertEqual(p1.title, 'New title')
        self.assertEqual(p2.title, 'New title')

        # Seminar source object
        s2 = self._createType(self.portal, 'Folder', 's2')
        s2.setTitle('Old title')
        notify(ObjectModifiedEvent(s2))

        s2.current_syndication_targets = [IUUID(p3), IUUID(p4)]

        self.assertNotEqual(p3.title, 'New title')
        self.assertNotEqual(p4.title, 'New title')

        s2.setTitle('New title')
        notify(ObjectModifiedEvent(s2))
        self.assertEqual(p3.title, 'New title')
        self.assertEqual(p4.title, 'New title')

    def test_source_object_unpublished(self):
        self.loginAsPortalOwner()
        wft = getToolByName(self.portal, 'portal_workflow')

        # create source object and related with proxy
        p1 = self._createType(self.portal, 'resonate.proxy', 'p1')
        p2 = self._createType(self.portal, 'resonate.proxy', 'p2')

        # Event source object
        s1 = self._createType(self.portal, 'Event', 's1')
        s1targets = s1.getField('current_syndication_targets')
        s1targets.set(s1, [IUUID(p1), IUUID(p2)])

        wft.doActionFor(s1, "publish")
        self.failUnless(wft.getInfoFor(s1, "review_state") == "published")
        self.failUnless(wft.getInfoFor(p1, "review_state") != "published")
        self.failUnless(wft.getInfoFor(p2, "review_state") != "published")

        wft.doActionFor(p1, "publish")
        self.failUnless(wft.getInfoFor(p1, "review_state") == "published")
        wft.doActionFor(p2, "publish")
        self.failUnless(wft.getInfoFor(p2, "review_state") == "published")

        wft.doActionFor(s1, "retract")
        self.failUnless(wft.getInfoFor(s1, "review_state") != "published")
        self.failUnless(wft.getInfoFor(p1, "review_state") != "published")
        self.failUnless(wft.getInfoFor(p2, "review_state") != "published")
        self.logout()

    def test_proxy_object_removed(self):
        # create source object and related with proxy
        p1 = self._createType(self.portal, 'resonate.proxy', 'p1')
        p2 = self._createType(self.portal, 'resonate.proxy', 'p2')

        # Event source object
        s1 = self._createType(self.portal, 'Event', 's1')
        s1targets = s1.getField('current_syndication_targets')
        self.assertFalse(s1targets.get(s1))

        s1targets.set(s1, IUUID(p1))
        p1.source_object = IUUID(s1)
        self.assertEqual(len(s1targets.get(s1)), 1)

        self.skipTest(
            'TODO Fix defore delete event handler deleting proxy '
            'from under itself')
        self.portal.manage_delObjects(ids=['p1'])
        self.assertFalse(s1targets.get(s1))

        # Seminar source object
        s2 = self._createType(self.portal, 'Folder', 's2')
        self.assertFalse(s2.current_syndication_targets)

        s2.current_syndication_targets = [IUUID(p2)]
        p2.source_object = IUUID(s2)
        self.assertEqual(len(s2.current_syndication_targets), 1)

        self.portal.manage_delObjects(ids=['p2'])
        self.assertFalse(s2.current_syndication_targets)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestProxyContent))
    return suite
