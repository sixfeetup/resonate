from zope.interface import implements
from zope.component import adapts

from archetypes.schemaextender.field import ExtensionField
from archetypes.schemaextender.interfaces import ISchemaModifier
from archetypes.referencebrowserwidget import ReferenceBrowserWidget

from Products.ATContentTypes.interfaces import IATEvent
from Products.OrderableReferenceField import OrderableReferenceField
from Products.CMFCore.permissions import ModifyPortalContent
from Products.ATContentTypes import ATCTMessageFactory as _


class OrderableReferenceExtensionField(ExtensionField,
                                       OrderableReferenceField):
    pass


orderableRelatedItemsField = OrderableReferenceExtensionField(
    'relatedItems',
    relationship='relatesTo',
    multiValued=True,
    isMetadata=True,
    languageIndependent=False,
    index='KeywordIndex',
    write_permission=ModifyPortalContent,
    schemata='categorization',
    widget=ReferenceBrowserWidget(
        allow_search=True,
        allow_browse=True,
        show_indexes=False,
        allow_sorting=True,
        force_close_on_insert=False,
        label=_(u'label_related_items', default=u'Related Items'),
        visible={'edit': 'visible', 'view': 'invisible'},
        )
    )


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


class EventCurrentSyndicationTargetsModifier(object):

    implements(ISchemaModifier)
    adapts(IATEvent)

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


class EventRejectedSyndicationSitesModifier(object):

    implements(ISchemaModifier)
    adapts(IATEvent)

    def __init__(self, context):
        self.context = context

    def fiddle(self, schema):
        schema['rejected_syndication_sites'] = orderableRSSField.copy()
