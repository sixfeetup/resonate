from Products.CMFCore.utils import getToolByName

from plone.app import testing
from plone.app.testing import PloneWithPackageLayer
from plone.app.testing import IntegrationTesting
from plone.app.testing import FunctionalTesting
from plone.app.testing import bbb as ptc

import resonate


RESONATE = PloneWithPackageLayer(
    zcml_package=resonate,
    zcml_filename='testing.zcml',
    gs_profile_id='resonate:testing',
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
