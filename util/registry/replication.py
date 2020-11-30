import features
import json

from contextlib import contextmanager
from data import model

from app import image_replication_queue

DEFAULT_BATCH_SIZE = 1000


@contextmanager
def queue_replication_batch(namespace, batch_size=DEFAULT_BATCH_SIZE):
    """
    Context manager implementation which returns a target callable that takes the storage to queue
    for replication.

    When the the context block exits the items generated by the callable will be bulk inserted into
    the queue with the specified batch size.
    """
    namespace_user = model.user.get_namespace_user(namespace)

    with image_replication_queue.batch_insert(batch_size) as queue_put:

        def queue_storage_replication_batch(storage):
            if features.STORAGE_REPLICATION:
                queue_put(
                    [storage.uuid],
                    json.dumps(
                        {
                            "namespace_user_id": namespace_user.id,
                            "storage_id": storage.uuid,
                        }
                    ),
                )

        yield queue_storage_replication_batch


def queue_storage_replication(namespace, storage):
    """
    Queues replication for the given image storage under the given namespace (if enabled).
    """
    with queue_replication_batch(namespace, 1) as batch_spawn:
        batch_spawn(storage)
