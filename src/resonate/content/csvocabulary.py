from zope.interface import implements
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary
from plone import api


class ChildSitesVocabulary(object):
    implements(IVocabularyFactory)

    def __call__(self, context):
        """get IDs and names of child sites"""
        catalog = api.portal.get_tool('portal_catalog')
        brains = catalog(
            object_provides='collective.lineage.interfaces.IChildSite'
        )
        vocabulary = []
        for brain in brains:
            obj = brain.getObject()
            vocabulary.append((obj.UID(), obj.title))
        items = [SimpleTerm(i[0], i[0], i[1]) for i in vocabulary]
        return SimpleVocabulary(items)

# resonate.vocabulary.childsites points here
ChildSitesVocabularyFactory = ChildSitesVocabulary()
