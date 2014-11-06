from zope.interface import implements
from zope.component import adapts

from archetypes.schemaextender.interfaces import ISchemaModifier

from Products.ATContentTypes.interfaces import IATEvent

from resonate.content.extenders import orderableCSTField
from resonate.content.extenders import orderableRSSField


class EventCurrentSyndicationTargetsModifier(object):

    implements(ISchemaModifier)
    adapts(IATEvent)

    def __init__(self, context):
        self.context = context

    def fiddle(self, schema):
        schema['current_syndication_targets'] = orderableCSTField.copy()


class EventRejectedSyndicationSitesModifier(object):

    implements(ISchemaModifier)
    adapts(IATEvent)

    def __init__(self, context):
        self.context = context

    def fiddle(self, schema):
        schema['rejected_syndication_sites'] = orderableRSSField.copy()
