# -*- extra stuff goes here -*-
from zope.i18nmessageid import MessageFactory as MF
from Products.ATContentTypes.interfaces import IATEvent
from Products.ATContentTypes.interfaces import IATNewsItem
from Products.ATContentTypes.interfaces import IATFile


MessageFactory = MF('resonate')
# types that allow syndication
syndication_types = (
    IATEvent,
    IATNewsItem,
    IATFile,
)


def initialize(context):
    """Initializer called when used as a Zope 2 product."""
