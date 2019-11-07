from zope import interface
from zope import component

from z3c.form import interfaces as form_ifaces
from z3c.form import field
from z3c.form import form
from z3c.relationfield import schema

from plone.autoform import interfaces as autoform_ifaces
from plone.supermodel import model

from resonate import MessageFactory as _


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

    model.fieldset(
        'categorization', label=u"Categorization",
        fields=['current_syndication_targets', 'rejected_syndication_sites'])

    current_syndication_targets = schema.RelationList(
        title=u"Current syndication targets",
        default=[],
        required=False,
        value_type=schema.RelationChoice(
            title=_(u"Target"), vocabulary='plone.app.vocabularies.Catalog'),
    )

    rejected_syndication_sites = schema.RelationList(
        title=u"Rejected syndication sites",
        default=[],
        required=False,
        value_type=schema.RelationChoice(
            title=_(u"Site"), vocabulary='plone.app.vocabularies.Catalog'),
    )


class SyndicationSourceEditForm(form.EditForm):
    """
    An edit form to re-use form logic for manipulating relations.
    """

    fields = field.Fields(ISyndicationSource)

    def __init__(self, context, request=None):
        """
        Make the request optional.
        """
        super(SyndicationSourceEditForm, self).__init__(context, request)

    def get_data(self, field_name):
        """
        Retrieve the data from the manager as the widget would.
        """
        data_manager = component.getMultiAdapter(
            (self.context, self.fields[field_name].field),
            form_ifaces.IDataManager)
        return data_manager.get()
