import unittest

from zope.event import notify
from zope.lifecycleevent import ObjectCreatedEvent
from zope.lifecycleevent import ObjectModifiedEvent
from plone.uuid.interfaces import IUUID

from Products.CMFCore.utils import getToolByName
from Products.Archetypes.event import ObjectInitializedEvent

from .. import testing


class TestLocalRoles(testing.TestCase):

    def set_member_field(self, member, field, val):
        setattr(member, field, val)
        notify(ObjectModifiedEvent(member))

    def set_affiliations(self, member, val):
        new_vals = []
        for n, i in enumerate(val):
            new_vals.append({'affiliation': IUUID(i),
                             'position': 'None',
                             'main': False,
                             'order': n + 1})

        self.set_member_field(member, 'affiliations', new_vals)

    def test_grad_students_role_in_faculty_portfolio(self):
        mtool = self.portal.portal_membership
        membrane = getToolByName(self.portal, 'membrane_tool')
        # Create user joe
        joe = self._createType(self.portal, 'nd.content.member', 'joe')
        joe.first_name = 'joe'
        joe.last_name = 'none'
        joe.username = 'joenone'
        notify(ObjectCreatedEvent(joe))
        membrane.reindexObject(joe)

        # and it's member folder
        self.setRoles(('Manager', ))
        mtool.createMemberarea(joe.unique_userid.lower())
        portfolio = mtool.getHomeFolder(joe.unique_userid.lower())
        notify(ObjectInitializedEvent(portfolio))

        # Create user bob and make him a student
        bob = self._createType(self.portal, 'nd.content.member', 'bob')
        bob.first_name = 'bob'
        bob.last_name = 'none'
        bob.username = 'bnone'
        bob.graduated_undergraduated = u'Graduate Student'
        bob.member_option = 'Current Student'
        notify(ObjectCreatedEvent(bob))
        membrane.reindexObject(bob)
        bob.reindexObject()

        bob_member = mtool.getMemberById(bob.unique_userid.lower())
        self.assertEqual(bob_member.getRolesInContext(portfolio),
                         ['Authenticated'])

        # Add joe as advisor
        IStudent(bob).advisors = [IUUID(joe)]
        bob.reindexObject()

        # He is a contributor now
        self.assertTrue('Contributor' in \
                         bob_member.getRolesInContext(portfolio))
        self.logout()

    def test_non_member_as_reviewer(self):
        self.loginAsPortalOwner()
        wft = getToolByName(self.portal, 'portal_workflow')
        mtool = self.portal.portal_membership
        membrane = getToolByName(self.portal, 'membrane_tool')

        types = ['nd.content.seminar',
                 'Event',
                 'News Item']

        for idx, typename in enumerate(types):
            _id = '%s_obj' + str(idx)

            # Create a source object and syndicate it
            s1 = self._createType(self.portal, typename, _id % 's1')
            c1 = self._createType(self.portal, 'nd.content.center', _id % 'c1')
            c2 = self._createType(self.portal, 'nd.content.center', _id % 'c2')
            c3 = self._createType(self.portal, 'nd.content.center', _id % 'c3')

            # And a portal member
            joe = self._createType(self.portal, 'nd.content.member', _id % 'm')
            joe.first_name = 'joe'
            joe.last_name = str(idx)
            joe.username = 'j' + str(idx)
            notify(ObjectCreatedEvent(joe))
            membrane.reindexObject(joe)
            joe.reindexObject()
            member = mtool.getMemberById(joe.unique_userid.lower())

            wft.doActionFor(s1, "request_syndication")
            wft.doActionFor(s1, "accept_syndication", organizations=[c1, c2])
            self.assertEqual(member.getRolesInContext(s1), ['Authenticated'])

            self.set_affiliations(joe, [c3])
            self.assertEqual(member.getRolesInContext(s1), ['Authenticated'])

            self.set_affiliations(joe, [c1])
            self.assertTrue('Reviewer' in member.getRolesInContext(s1))

        self.logout()

    def test_non_member_as_deleter(self):
        self.loginAsPortalOwner()

        mtool = self.portal.portal_membership
        membrane = getToolByName(self.portal, 'membrane_tool')
        wft = getToolByName(self.portal, 'portal_workflow')

        types = ['nd.content.seminar',
                 'Event',
                 'News Item']

        for idx, typename in enumerate(types):
            _id = '%s_obj' + str(idx)

            # Create a source object and syndicate it
            f1 = self._createType(self.portal, 'Folder', _id % 'f')
            s1 = self._createType(f1, 'Event', _id % 's')
            c1 = self._createType(self.portal, 'nd.content.center', _id % 'c1')
            c2 = self._createType(self.portal, 'nd.content.center', _id % 'c2')

            # And a portal member
            joe = self._createType(self.portal, 'nd.content.member', _id % 'm')
            joe.first_name = 'joe'
            joe.last_name = str(idx)
            joe.username = 'j' + str(idx)
            notify(ObjectCreatedEvent(joe))
            membrane.reindexObject(joe)
            joe.reindexObject()
            member = mtool.getMemberById(joe.unique_userid.lower())

            wft.doActionFor(s1, "request_syndication")
            wft.doActionFor(s1, "accept_syndication", organizations=[c1, c2])
            self.assertEqual(member.getRolesInContext(f1), ['Authenticated'])

            self.set_affiliations(joe, [c1])
            self.assertTrue('Deleter' in member.getRolesInContext(f1))

            self.set_affiliations(joe, [c1, c2])
            self.assertTrue('Deleter' in member.getRolesInContext(f1))

        self.logout()


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestLocalRoles))
    return suite
