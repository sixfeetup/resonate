from zope.interface import implements
from zope.component import adapts

from archetypes.schemaextender.interfaces import ISchemaModifier

from Products.ATContentTypes.interfaces import IATFile

from resonate.content.extenders import orderableCSTField
from resonate.content.extenders import orderableRSSField


class FileCurrentSyndicationTargetsModifier(object):

    implements(ISchemaModifier)
    adapts(IATFile)

    def __init__(self, context):
        self.context = context

    def fiddle(self, schema):
        schema['current_syndication_targets'] = orderableCSTField.copy()


class FileRejectedSyndicationSitesModifier(object):

    implements(ISchemaModifier)
    adapts(IATFile)

    def __init__(self, context):
        self.context = context

    def fiddle(self, schema):
        schema['rejected_syndication_sites'] = orderableRSSField.copy()
