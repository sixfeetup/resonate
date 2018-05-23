from zope import interface

from z3c.relationfield import schema

from plone.autoform import interfaces as autoform_ifaces
from plone.supermodel import model
from plone.formwidget import contenttree

from resonate import MessageFactory as _


class ISyndicationTarget(interface.Interface):
    """
    The target within a child site for content to be syndicated into.
    """


@interface.provider(autoform_ifaces.IFormFieldProvider)
class ISyndicationSource(model.Schema):
    """
    Content that is the source for syndication to other sites.
    """

    model.fieldset(
        'categorization', label=u"Categorization",
        fields=['current_syndication_targets', 'rejected_syndication_sites'])

    current_syndication_targets = schema.RelationList(
        title=u"Current syndication targets",
        default=[],
        readonly=True,
        required=False,
        value_type=schema.RelationChoice(
            title=_(u"Target"), source=contenttree.ObjPathSourceBinder()),
    )

    rejected_syndication_sites = schema.RelationList(
        title=u"Rejected syndication sites",
        default=[],
        readonly=True,
        required=False,
        value_type=schema.RelationChoice(
            title=_(u"Site"), source=contenttree.ObjPathSourceBinder()),
    )
