"""S3 ``Storage`` backend for the TAI ecosystem.

Importing this package fires the ``@tai42_app.storage.register_storage`` decorator on
``S3Storage`` as a side-effect — that is how the skeleton discovers the backend
(the manifest's ``storage_module: tai42_storage_s3`` names this package to import).
"""

from tai42_storage_s3.storage import S3Storage

__all__ = ["S3Storage"]
