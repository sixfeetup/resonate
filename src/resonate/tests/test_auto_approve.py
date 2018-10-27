"""
Managers can set which target sites where syndication is auto-approved.
"""

from plone.uuid import interfaces as uuid_ifaces

from Products.Archetypes.interfaces import referenceable

from .. import testing


class TestSyndication(testing.TestCase):
    __doc__

    def test_portal_referencable(self):
        """
        The portal supports Archetypes references.
        """
        portal_uid = uuid_ifaces.IUUID(self.portal)
        self.assertTrue(
            portal_uid,
            'Missing portal UID')
        uid_brains = self.portal.uid_catalog(UID=portal_uid)
        self.assertEqual(
            len(uid_brains), 1,
            'Wrong number of portal UID results in the catalog')
        portal_refs = referenceable.IReferenceable(self.portal)

        corge_news = self._createType(
            self.portal, 'News Item', 'corge-news-title')
        corge_refs = referenceable.IReferenceable(corge_news)
        portal_refs.addReference(corge_refs, relationship='from-portal')
        corge_refs.addReference(portal_refs, relationship='to-portal')

        self.assertTrue(
            portal_refs.getRefs('from-portal'),
            'Wrong number of refs from portal')
        self.assertTrue(
            portal_refs.getBRefs('to-portal'),
            'Wrong number of refs to portal')
        self.assertTrue(
            corge_refs.getBRefs('from-portal'),
            'Wrong number of refs from portal')
        self.assertTrue(
            corge_refs.getRefs('to-portal'),
            'Wrong number of refs to portal')
