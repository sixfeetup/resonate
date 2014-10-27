from zope import interface
from p4a.subtyper import interfaces as stifaces
from nd.syndication import interfaces
from nd.syndication import MessageFactory as _


# FIXME: these adapters should be in their respective packages
class EventDescriptor(object):
    """A descriptor for the Event subtype.
    """
    interface.implements(stifaces.IFolderishContentTypeDescriptor)
    title = _(u'Event syndication')
    description = _(u'Event target syndication')
    type_interface = interfaces.IEventSyndicationTarget


class NewsDescriptor(object):
    """A descriptor for the News subtype.
    """
    interface.implements(stifaces.IFolderishContentTypeDescriptor)
    title = _(u'News syndication')
    description = _(u'News target syndication')
    type_interface = interfaces.INewsSyndicationTarget


class SeminarDescriptor(object):
    """A descriptor for the Seminar subtype.
    """
    interface.implements(stifaces.IFolderishContentTypeDescriptor)
    title = _(u'Seminar syndication')
    description = _(u'Seminar target syndication')
    type_interface = interfaces.ISeminarSyndicationTarget
