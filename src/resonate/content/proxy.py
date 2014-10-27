from zope import schema
from five import grok

from z3c.relationfield.schema import RelationChoice
from plone.directives import form
from plone.directives import dexterity
from plone.formwidget.contenttree import ObjPathSourceBinder

from nd.syndication import MessageFactory as _


class IProxy(form.Schema):
    """
    Proxy
    """
    title = schema.TextLine(
        title=_(u"Title"),
        required=True,
        readonly=True,
    )

    description = schema.Text(
        title=_(u"Description"),
        required=False,
    )

    source_object = RelationChoice(
        title=_(u"Source object"),
        source=ObjPathSourceBinder(),
        required=True,
        readonly=True,
    )

    source_type = schema.TextLine(
        title=_(u"Source Type"),
        required=True,
        readonly=True,
    )

    start = schema.Datetime(
        title=_(u"Source Start Date"),
        required=False,
        readonly=True,
    )

    end = schema.Datetime(
        title=_(u"Source End Date"),
        required=False,
        readonly=True,
    )
