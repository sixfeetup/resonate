from zope import interface
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary

from plone import api


@interface.implementer(IVocabularyFactory)
class ChildSitesVocabulary(object):

    def __call__(self, context):
        """get IDs and names of child sites"""
        nav_root = api.portal.get_navigation_root(context)
        nav_root_uid = api.content.get_uuid(nav_root)

        catalog = api.portal.get_tool('portal_catalog')
        brains = catalog(
            object_provides='plone.app.layout.navigation'
            '.interfaces.INavigationRoot'
        )
        vocabulary = []
        for brain in brains:
            if brain.UID == nav_root_uid:
                continue
            vocabulary.append((brain.UID, brain.Title or brain.getId))
        items = [SimpleTerm(i[0], i[0], i[1]) for i in vocabulary]
        return SimpleVocabulary(items)

# resonate.vocabulary.childsites points here
ChildSitesVocabularyFactory = ChildSitesVocabulary()
