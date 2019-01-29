"""Worker functions.

The functions in this module wrap around plugin classes such that these
worker functions can be specified as the ``target`` parameter while
launching a new subprocess with :class:`multiprocessing.Process`.

Each worker function can run as a separate subprocess. While wrapping
around a plugin class, each worker function creates the multiprocessing
queues necessary to pass records from one plugin class to another.
"""


import logging

_logger = logging.getLogger(__name__)


def cloud_worker(worker_name, cloud_plugin, output_queues):
    """Worker function for cloud plugins.

    This function expects the ``cloud_plugin`` object to implement a
    ``read`` method that yields records. This function calls this
    ``read`` method to retrieve records and puts each record into each
    queue in ``output_queues``.

    Arguments:
        worker_name (str): Display name for the worker.
        cloud_plugin (object): Cloud plugin object.
        output_queues (list): List of :class:`multiprocessing.Queue`
            objects to write records to.
    """
    _logger.info('%s: Started', worker_name)
    for record in cloud_plugin.read():
        for q in output_queues:
            q.put(record)
    cloud_plugin.done()
    _logger.info('%s: Stopped', worker_name)


def store_worker(worker_name, store_plugin, input_queue):
    """Worker function for store plugins.

    This function expects the ``store_plugin`` object to implement a
    ``write`` method that accepts a single record as a parameter and a
    ``done`` method to perform cleanup work in the end.

    This function gets records from ``input_queue`` and passes each
    record to the ``write`` method of ``store_plugin``.

    When there are no more records in the ``input_queue``, i.e., once
    ``None`` is found in the ``input_queue``, this function calls the
    ``done`` method of the ``store_plugin`` to indicate that record
    processing is over.

    Arguments:
        worker_name (str): Display name for the worker.
        store_plugin (object): Store plugin object.
        input_queue (multiprocessing.Queue): Queue to read records from.
    """
    _logger.info('%s: Started', worker_name)
    while True:
        record = input_queue.get()
        if record is None:
            store_plugin.done()
            break
        store_plugin.write(record)
    _logger.info('%s: Stopped', worker_name)


def check_worker(worker_name, check_plugin, input_queue, output_queues):
    """Worker function for check plugins.

    This function expects the ``check_plugin`` object to implement a
    ``eval`` method that accepts a single record as a parameter and
    yields one or more records, and a ``done`` method to perform cleanup
    work in the end.

    This function gets records from ``input_queue`` and passes each
    record to the ``eval`` method of ``check_plugin``. Then it puts each
    record yielded by the ``eval`` method into each queue in
    ``output_queues``.

    When there are no more records in the ``input_queue``, i.e., once
    ``None`` is found in the ``input_queue``, this function calls the
    ``done`` method of the ``store_plugin`` to indicate that record
    processing is over.

    Arguments:
        worker_name (str): Display name for the worker.
        store_plugin (object): Store plugin object.
        input_queue (multiprocessing.Queue): Queue to read records from.
        output_queues (list): List of :class:`multiprocessing.Queue`
            objects to write records to.
    """
    _logger.info('%s: Started', worker_name)
    while True:
        record = input_queue.get()
        if record is None:
            check_plugin.done()
            break

        for event_record in check_plugin.eval(record):
            for q in output_queues:
                q.put(event_record)

    _logger.info('%s: Stopped', worker_name)