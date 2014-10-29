from zope.interface import implements
from zope.component import adapts

from archetypes.schemaextender.field import ExtensionField
from archetypes.schemaextender.interfaces import ISchemaModifier
from archetypes.referencebrowserwidget import ReferenceBrowserWidget

from Products.OrderableReferenceField import OrderableReferenceField
from Products.ATContentTypes.interfaces import IATNewsItem
from Products.CMFCore.permissions import ModifyPortalContent

from Products.ATContentTypes import ATCTMessageFactory as _


class OrderableReferenceExtensionField(ExtensionField,
                                       OrderableReferenceField):
    pass


orderableCSTField = OrderableReferenceExtensionField(
    'current_syndication_targets',
    relationship='syndicatesTo',
    multiValued=True,
    languageIndependent=False,
    modes=('view',),
    write_permission=ModifyPortalContent,
    schemata='categorization',
    widget=ReferenceBrowserWidget(
        allow_search=True,
        allow_browse=True,
        show_indexes=False,
        allow_sorting=True,
        label=_(u'Current syndication targets'),
        visible={'edit': 'visible', 'view': 'invisible'},
        )
    )


class NewsItemCurrentSyndicationTargetsModifier(object):

    implements(ISchemaModifier)
    adapts(IATNewsItem)

    def __init__(self, context):
        self.context = context

    def fiddle(self, schema):
        schema['current_syndication_targets'] = orderableCSTField.copy()


orderableRSSField = OrderableReferenceExtensionField(
    'rejected_syndication_sites',
    relationship='rejectsFrom',
    multiValued=True,
    languageIndependent=False,
    modes=('view',),
    write_permission=ModifyPortalContent,
    schemata='categorization',
    widget=ReferenceBrowserWidget(
        allow_search=True,
        allow_browse=True,
        show_indexes=False,
        allow_sorting=True,
        label=_(u'Rejected syndication sites'),
        visible={'edit': 'visible', 'view': 'invisible'},
        )
    )


class NewsItemRejectedSyndicationSitesModifier(object):

    implements(ISchemaModifier)
    adapts(IATNewsItem)

    def __init__(self, context):
        self.context = context

    def fiddle(self, schema):
        schema['rejected_syndication_sites'] = orderableRSSField.copy()
