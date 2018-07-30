from zope import schema

from plone.directives import form
from plone.formwidget.contenttree import ObjPathSourceBinder

from resonate import MessageFactory as _


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
