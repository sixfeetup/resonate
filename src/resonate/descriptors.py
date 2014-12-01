from zope import interface
from p4a.subtyper import interfaces as stifaces
from resonate import interfaces
from resonate import MessageFactory as _


# FIXME: these adapters should be in their respective packages
class EventDescriptor(object):
    """A descriptor for the Event subtype.
    """
    interface.implements(stifaces.IFolderishContentTypeDescriptor)
    title = _(u'Event syndication')
    description = _(u'Event syndication target')
    type_interface = interfaces.IEventSyndicationTarget


class NewsDescriptor(object):
    """A descriptor for the News subtype.
    """
    interface.implements(stifaces.IFolderishContentTypeDescriptor)
    title = _(u'News syndication')
    description = _(u'News syndication target')
    type_interface = interfaces.INewsSyndicationTarget


class FileTargetDescriptor(object):
    """A descriptor for the File subtype.
    """
    interface.implements(stifaces.IFolderishContentTypeDescriptor)
    title = _(u'File syndication')
    description = _(u'File syndication target')
    type_interface = interfaces.IFileSyndicationTarget
