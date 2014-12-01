# -*- extra stuff goes here -*-
from zope.i18nmessageid import MessageFactory as MF
from Products.ATContentTypes.interfaces import IATEvent
from Products.ATContentTypes.interfaces import IATNewsItem


MessageFactory = MF('resonate')
# types that allow syndication
syndication_types = (
    IATEvent,
    IATNewsItem,
)


def initialize(context):
    """Initializer called when used as a Zope 2 product."""
