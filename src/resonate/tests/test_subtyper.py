# For most cases it is easiest to reuse the test setup from nd.policy.

import unittest
from zope.interface import alsoProvides
from zope.component import getUtility
from p4a.subtyper.interfaces import ISubtyper
from plone.app.layout.navigation.interfaces import INavigationRoot

from nd.syndication.interfaces import IEventSyndicationTarget, \
    INewsSyndicationTarget, ISeminarSyndicationTarget
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
        self.assertFalse(ISeminarSyndicationTarget.providedBy(f3))

        subtyper = getUtility(ISubtyper)
        subtyper.change_type(f1, u'nd.syndication.event')
        subtyper.change_type(f2, u'nd.syndication.news')
        subtyper.change_type(f3, u'nd.syndication.seminar')

        self.failUnless(IEventSyndicationTarget.providedBy(f1))
        self.failUnless(INewsSyndicationTarget.providedBy(f2))
        self.failUnless(ISeminarSyndicationTarget.providedBy(f3))

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

        subtyper.change_type(e1, u'nd.syndication.event')
        e1.reindexObject()
        self.failUnless(IEventSyndicationTarget.providedBy(e1))
        subtyper.change_type(e2, u'nd.syndication.event')
        e2.reindexObject()
        self.assertFalse(IEventSyndicationTarget.providedBy(e2))

        subtyper.change_type(n1, u'nd.syndication.news')
        n1.reindexObject()
        self.failUnless(INewsSyndicationTarget.providedBy(n1))
        subtyper.change_type(n2, u'nd.syndication.news')
        n2.reindexObject()
        self.assertFalse(INewsSyndicationTarget.providedBy(n2))

        subtyper.change_type(s1, u'nd.syndication.seminar')
        s1.reindexObject()
        self.failUnless(ISeminarSyndicationTarget.providedBy(s1))
        subtyper.change_type(s2, u'nd.syndication.seminar')
        s2.reindexObject()
        self.assertFalse(ISeminarSyndicationTarget.providedBy(s2))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSubtyper))
    return suite
