from zope import interface

from plone.autoform import interfaces as autoform_ifaces
from plone.supermodel import model


class ISyndicationTarget(interface.Interface):
    """
    The target within a child site for content to be syndicated into.
    """


def enable_syn_target(context):
    interface.alsoProvides(context, ISyndicationTarget)
    context.reindexObject(idxs=('object_provides'))


def disable_syn_target(context):
    interface.noLongerProvides(context, ISyndicationTarget)
    context.reindexObject(idxs=('object_provides'))


@interface.provider(autoform_ifaces.IFormFieldProvider)
class ISyndicationSource(model.Schema):
    """
    Content that is the source for syndication to other sites.
    """
