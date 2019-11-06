# For most cases it is easiest to reuse the test setup from nd.policy.

import unittest
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent
from Products.CMFCore.utils import getToolByName

from .. import utils
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
        utils.addRelation(
            from_object=s1, to_object=p1,
            from_attribute='current_syndication_targets')
        utils.addRelation(
            from_object=s1, to_object=p2,
            from_attribute='current_syndication_targets')

        notify(ObjectModifiedEvent(p1))
        notify(ObjectModifiedEvent(p2))

        self.portal.manage_delObjects(ids=['s1'])
        self.assertNotIn('p1', self.portal.objectIds())
        self.assertNotIn('p2', self.portal.objectIds())

        # Seminar source object
        s2 = self._createType(self.portal, 'News Item', 's2')
        utils.addRelation(
            from_object=s2, to_object=p3,
            from_attribute='current_syndication_targets')
        utils.addRelation(
            from_object=s2, to_object=p4,
            from_attribute='current_syndication_targets')

        notify(ObjectModifiedEvent(p3))
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

        utils.addRelation(
            from_object=s1, to_object=p1,
            from_attribute='current_syndication_targets')
        utils.addRelation(
            from_object=s1, to_object=p2,
            from_attribute='current_syndication_targets')

        self.assertNotEqual(p1.title, 'New title')
        self.assertNotEqual(p2.title, 'New title')

        s1.setTitle('New title')
        notify(ObjectModifiedEvent(s1))
        self.assertEqual(p1.title, 'New title')
        self.assertEqual(p2.title, 'New title')

        # News Item source object
        s2 = self._createType(self.portal, 'News Item', 's2')
        s2.setTitle('Old title')
        notify(ObjectModifiedEvent(s2))

        utils.addRelation(
            from_object=s2, to_object=p3,
            from_attribute='current_syndication_targets')
        utils.addRelation(
            from_object=s2, to_object=p4,
            from_attribute='current_syndication_targets')

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
        utils.addRelation(
            from_object=s1, to_object=p1,
            from_attribute='current_syndication_targets')
        utils.addRelation(
            from_object=s1, to_object=p2,
            from_attribute='current_syndication_targets')

        wft.doActionFor(s1, "publish")
        self.assertEqual(wft.getInfoFor(s1, "review_state"), "published")
        self.assertNotEqual(wft.getInfoFor(p1, "review_state"), "published")
        self.assertNotEqual(wft.getInfoFor(p2, "review_state"), "published")

        wft.doActionFor(p1, "publish")
        self.assertEqual(wft.getInfoFor(p1, "review_state"), "published")
        wft.doActionFor(p2, "publish")
        self.assertEqual(wft.getInfoFor(p2, "review_state"), "published")

        wft.doActionFor(s1, "retract")
        self.assertNotEqual(wft.getInfoFor(s1, "review_state"), "published")
        self.assertNotEqual(wft.getInfoFor(p1, "review_state"), "published")
        self.assertNotEqual(wft.getInfoFor(p2, "review_state"), "published")
        self.logout()

    def test_proxy_object_removed(self):
        # create source object and related with proxy
        p1 = self._createType(self.portal, 'resonate.proxy', 'p1')
        p2 = self._createType(self.portal, 'resonate.proxy', 'p2')

        # Event source object
        s1 = self._createType(self.portal, 'Event', 's1')
        self.assertFalse(utils.getRelations(
            from_object=s1, from_attribute='current_syndication_targets'))

        utils.addRelation(
            from_object=s1, to_object=p1,
            from_attribute='current_syndication_targets')

        self.portal.manage_delObjects(ids=['p1'])
        self.assertFalse(utils.getRelations(
            from_object=s1, from_attribute='current_syndication_targets'))

        # News Item source object
        s2 = self._createType(self.portal, 'News Item', 's2')
        self.assertFalse(utils.getRelations(
            from_object=s1, from_attribute='current_syndication_targets'))

        utils.addRelation(
            from_object=s2, to_object=p2,
            from_attribute='current_syndication_targets')

        self.portal.manage_delObjects(ids=['p2'])
        self.assertFalse(utils.getRelations(
            from_object=s2, from_attribute='current_syndication_targets'))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestProxyContent))
    return suite
