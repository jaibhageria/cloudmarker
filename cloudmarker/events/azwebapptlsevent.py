"""Microsoft web app minimum TLS version event.

This module defines the :class:`AzWebAppTLSEvent` class that identifies
a web app with minimum TLS version not equal to the required minimum TLS
version. This plugin works on the web apps config properties found in the
``com`` bucket of ``web_app`` records.
"""


import logging

from cloudmarker import util

_log = logging.getLogger(__name__)


class AzWebAppTLSEvent:
    """Azure web app minimum TLS version check event plugin."""

    def __init__(self, _min_tls_version=1.2):
        """Create an instance of :class:`AzWebAppTLSEvent`.

        Arguments:
            _min_tls_version (float): Minimum required TLS version.

        """
        self._min_tls_version = _min_tls_version
        _log.info("Initialized; minimum TLS version: %.1f",
                  self._min_tls_version)

    def eval(self, record):
        """Evaluate Azure web app to check for insecure TLS config.

        Arguments:
            record (dict): A web app record.

        Yields:
            dict: An event record representing a web app with insecure
            TLS config.

        """
        com = record.get('com')
        ext = record.get('ext')
        if ext is None:
            return

        if ext.get('record_type') != 'web_app_config':
            return

        min_tls_version = ext.get('min_tls_version')

        if float(min_tls_version) < self._min_tls_version:
            yield from _get_azure_web_app_tls_event(
                com, ext, self._min_tls_version)

    def done(self):
        """Perform cleanup work.

        Currently, this method does nothing. This may change in future.
        """


def _get_azure_web_app_tls_event(com, ext, min_tls_version):
    """Evaluate Azure web app config for insecure min TLS version.

    Arguments:
        com (dict): Azure web app record `com` bucket
        ext (dict): Azure web app record `ext` bucket
        min_tls_version (float): Minimum required TLS version

    Returns:
        dict: An event record representing web apps not using a minimum
        TLS version

    """
    friendly_cloud_type = util.friendly_string(com.get('cloud_type'))
    reference = com.get('reference')
    description = (
        '{} web app {} has insecure minimum TLS version.'
        .format(friendly_cloud_type, reference)
    )
    recommendation = (
        'Check {} web app {} and ensure the minimum TLS version is set to {}.'
        .format(friendly_cloud_type, reference, str(min_tls_version))
    )

    event_record = {
        # Preserve the extended properties from the web app
        # record because they provide useful context to
        # locate the web app that led to the event.
        'ext': util.merge_dicts(ext, {
            'record_type': 'web_app_tls_event'
        }),
        'com': {
            'cloud_type': com.get('cloud_type'),
            'record_type': 'web_app_tls_event',
            'reference': reference,
            'description': description,
            'recommendation': recommendation,
        }
    }
    _log.info('Generating web_app_tls_event; %r', event_record)
    yield event_record
