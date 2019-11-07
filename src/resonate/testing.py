from Products.CMFCore.utils import getToolByName

from plone.testing import zope
from plone.app import testing
from plone.app.testing import PloneWithPackageLayer
from plone.app.testing import IntegrationTesting
from plone.app.testing import FunctionalTesting
from plone.app.testing import bbb as ptc

from collective.lineage import utils as lineage_utils

import resonate


RESONATE = PloneWithPackageLayer(
    zcml_package=resonate,
    zcml_filename='configure.zcml',
    gs_profile_id='resonate:content',
    name="RESONATE")
BASES = (RESONATE, testing.MOCK_MAILHOST_FIXTURE)

RESONATE_INTEGRATION = IntegrationTesting(
    bases=BASES, name="RESONATE_INTEGRATION")

RESONATE_FUNCTIONAL = FunctionalTesting(
    bases=BASES, name="RESONATE_FUNCTIONAL")


class TestCase(ptc.PloneTestCase):
    """We use this base class for all the tests in this package. If
    necessary, we can put common utility or setup code in here. This
    applies to unit test cases.
    """
    layer = RESONATE_FUNCTIONAL

    def _createType(
            self, context, portal_type, id, wf_transitions=[],
            *args, **kwargs):
        """create an object in the proper context
        """
        self.setRoles(('Manager', ))
        ttool = getToolByName(context, 'portal_types')
        wftool = getToolByName(context, 'portal_workflow')
        fti = ttool.getTypeInfo(portal_type)
        fti.constructInstance(context, id, *args, **kwargs)
        obj = getattr(context.aq_inner.aq_explicit, id)
        for transition in wf_transitions:
            wftool.doActionFor(obj, transition)
        # XXX: This could certainly cause some problems
        self.setRoles(())
        return obj

    def _createChildSiteAndTarget(self, context, id_, target, *args, **kwargs):
        """
        Create a container as a navigation root with a child site target.
        """
        obj = self._createType(context, 'Folder', id_, *args, **kwargs)
        lineage_utils.enable_childsite(obj)
        target_obj = self._createType(obj, 'Folder', target)
        target_obj.unrestrictedTraverse('@@syn_target_tool').enable()
        return obj

    def setUpBrowser(self):
        """
        Start a logged in browser session.
        """
        app = self.layer['app']
        self.browser = zope.Browser(app)
        self.browser.handleErrors = False  # Don't get HTTP 500 pages

        portal = self.layer['portal']
        portal_url = portal.absolute_url()

        self.browser.open(portal_url + '/login_form')
        self.browser.getControl(
            name='__ac_name').value = testing.SITE_OWNER_NAME
        self.browser.getControl(
            name='__ac_password').value = testing.SITE_OWNER_PASSWORD
        self.browser.getControl('Log in').click()
        self.assertIn(
            "You are now logged in", self.browser.contents,
            'Missing login confirmation message')
