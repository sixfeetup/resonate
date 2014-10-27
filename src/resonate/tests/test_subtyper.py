# For most cases it is easiest to reuse the test setup from nd.policy.

import unittest
from zope.interface import alsoProvides
from zope.component import getUtility
from p4a.subtyper.interfaces import ISubtyper
from plone.app.layout.navigation.interfaces import INavigationRoot

from resonate.interfaces import IEventSyndicationTarget, \
    INewsSyndicationTarget
from nd.policy.tests.base import TestCase


class TestSubtyper(TestCase):

    def test_subscription_subtyper(self):
        # create three content types and test the descriptors
        root = self._createType(self.portal, 'Folder', 'fakeroot')
        alsoProvides(root, INavigationRoot)

        f1 = self._createType(root, 'Folder', 'f1')
        f2 = self._createType(root, 'Folder', 'f2')
        f3 = self._createType(root, 'Folder', 'f3')

        self.assertFalse(IEventSyndicationTarget.providedBy(f1))
        self.assertFalse(INewsSyndicationTarget.providedBy(f2))

        subtyper = getUtility(ISubtyper)
        subtyper.change_type(f1, u'resonate.event')
        subtyper.change_type(f2, u'resonate.news')
        subtyper.change_type(f3, u'resonate.seminar')

        self.failUnless(IEventSyndicationTarget.providedBy(f1))
        self.failUnless(INewsSyndicationTarget.providedBy(f2))

    def test_subtyper_unique_check(self):
        # create fake organization Folder - we don't want
        # to call organization folder aftercreate subscribers
        center = self._createType(self.portal, 'Folder', 'fakecenter')
        alsoProvides(center, INavigationRoot)
        # and some folders
        e1 = self._createType(center, 'Folder', 'e1')
        e2 = self._createType(center, 'Folder', 'e2')
        n1 = self._createType(center, 'Folder', 'n1')
        n2 = self._createType(center, 'Folder', 'n2')
        s1 = self._createType(center, 'Folder', 's1')
        s2 = self._createType(center, 'Folder', 's2')

        subtyper = getUtility(ISubtyper)

        subtyper.change_type(e1, u'resonate.event')
        e1.reindexObject()
        self.failUnless(IEventSyndicationTarget.providedBy(e1))
        subtyper.change_type(e2, u'resonate.event')
        e2.reindexObject()
        self.assertFalse(IEventSyndicationTarget.providedBy(e2))

        subtyper.change_type(n1, u'resonate.news')
        n1.reindexObject()
        self.failUnless(INewsSyndicationTarget.providedBy(n1))
        subtyper.change_type(n2, u'resonate.news')
        n2.reindexObject()
        self.assertFalse(INewsSyndicationTarget.providedBy(n2))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSubtyper))
    return suite
