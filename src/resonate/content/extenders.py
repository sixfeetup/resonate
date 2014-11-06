from archetypes.schemaextender.field import ExtensionField
from archetypes.referencebrowserwidget import ReferenceBrowserWidget

from Products.OrderableReferenceField import OrderableReferenceField
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
