from zope.interface import implements
from zope.component import adapts

from archetypes.schemaextender.interfaces import ISchemaModifier

from Products.ATContentTypes.interfaces import IATNewsItem

from resonate.content.extenders import orderableCSTField
from resonate.content.extenders import orderableRSSField


class NewsItemCurrentSyndicationTargetsModifier(object):

    implements(ISchemaModifier)
    adapts(IATNewsItem)

    def __init__(self, context):
        self.context = context

    def fiddle(self, schema):
        schema['current_syndication_targets'] = orderableCSTField.copy()


class NewsItemRejectedSyndicationSitesModifier(object):

    implements(ISchemaModifier)
    adapts(IATNewsItem)

    def __init__(self, context):
        self.context = context

    def fiddle(self, schema):
        schema['rejected_syndication_sites'] = orderableRSSField.copy()
