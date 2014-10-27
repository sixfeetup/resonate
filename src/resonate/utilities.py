import logging

from BTrees.OOBTree import OOBTree
from OFS.SimpleItem import SimpleItem
from Persistence import Persistent
from zope.interface import implements

from zc.queue import CompositeQueue

from resonate.interfaces import ISyndicationNotificationTool
from resonate.utils import safe_uid

logger = logging.getLogger('resonate.notifications')


# BBB Disabled in favor of "real time" notifications instead of digests.
# Kept in place in case we want to enable it later.
class SyndicationNotificationTool(Persistent, SimpleItem):
    """
    See INotificationUtility for details
    """
    implements(ISyndicationNotificationTool)

    requeue_limit = 7

    def __init__(self):
        self.queues = OOBTree()
        self.requeue_limit = 7

    def get_queue(self, obj):
        uid = safe_uid(obj)
        return self.queues[uid]

    def put_notification(self, obj, payload):
        uid = safe_uid(obj)
        self.queues.setdefault(uid, CompositeQueue()).put(payload)

    def pull_notification(self, obj, index=0):
        uid = safe_uid(obj)
        # Can raise the following errors, must be handled by caller:
        #   KeyError: if the object has had no notifications queued yet
        #   IndexError: if the requested index isn't present in the queue
        return self.queues[uid].pull(index)

    def requeue_notification(self, obj, payload):
        curr_try = payload.get('retries', 0)
        payload['retries'] = curr_try + 1
        if payload['retries'] <= self.requeue_limit:
            # re-try for a week
            logger.info(
                'Re-queueing %r: %r', obj, payload)
            self.put_notification(obj, payload)
        else:
            logger.warning(
                'Not requeuing (retries exceeded) %r: %r', obj, payload)
