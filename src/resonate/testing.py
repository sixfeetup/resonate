from plone.app.testing import PloneWithPackageLayer
from plone.app.testing import IntegrationTesting
from plone.app.testing import FunctionalTesting

import nd.syndication


ND_SYNDICATION = PloneWithPackageLayer(
    zcml_package=nd.syndication,
    zcml_filename='testing.zcml',
    gs_profile_id='nd.syndication:testing',
    name="ND_SYNDICATION")

ND_SYNDICATION_INTEGRATION = IntegrationTesting(
    bases=(ND_SYNDICATION, ),
    name="ND_SYNDICATION_INTEGRATION")

ND_SYNDICATION_FUNCTIONAL = FunctionalTesting(
    bases=(ND_SYNDICATION, ),
    name="ND_SYNDICATION_FUNCTIONAL")
