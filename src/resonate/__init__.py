# -*- extra stuff goes here -*-
from zope.i18nmessageid import MessageFactory as MF

MessageFactory = MF('nd.syndication')


def initialize(context):
    """Initializer called when used as a Zope 2 product."""
