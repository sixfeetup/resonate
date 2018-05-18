from plone.app.testing import PloneWithPackageLayer
from plone.app.testing import IntegrationTesting
from plone.app.testing import FunctionalTesting

from Products.membrane import testing as membrane

import resonate


RESONATE = PloneWithPackageLayer(
    zcml_package=resonate,
    zcml_filename='testing.zcml',
    gs_profile_id='resonate:testing',
    name="RESONATE")

RESONATE_INTEGRATION = IntegrationTesting(
    bases=(membrane.MEMBRANE_PROFILES_FIXTURE, RESONATE),
    name="RESONATE_INTEGRATION")

RESONATE_FUNCTIONAL = FunctionalTesting(
    bases=(membrane.MEMBRANE_PROFILES_FIXTURE, RESONATE),
    name="RESONATE_FUNCTIONAL")
