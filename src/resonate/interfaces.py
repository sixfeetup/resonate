from zope.interface import Attribute
from zope.interface import Interface


class ISyndicationNotificationTool(Interface):
    """The portal syndication notification utility.
    """

    requeue_limit = Attribute(u"Re-queue Limit")

    def get_queue(obj):
        """Get the notification queue for an object
        (must support IUUID).
        """

    def put_notification(obj, payload):
        """Add an arbitrary payload for a particular object
        (must support IUUID).
        """

    def pull_notification(obj, index):
        """Pull a notification payload for an object at index.
        """

    def requeue_notification(obj, payload):
        """Re-queue a notification with an arbitrary payload for an object
        (must support IUUID).
        """


class ISyndicationTarget(Interface):
    """A marker interface."""


# FIXME: these adapters should be in their respective packages
class IEventSyndicationTarget(ISyndicationTarget):
    """A marker interface for Event syndication target."""


class INewsSyndicationTarget(ISyndicationTarget):
    """A marker interface for News syndication target."""
