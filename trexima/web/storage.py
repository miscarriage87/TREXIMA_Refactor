"""
TREXIMA v4.0 - Object Storage Service

S3-compatible storage service for SAP BTP Object Store.
Handles file upload, download, and management.
"""

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
import os
import json
from datetime import datetime
from typing import BinaryIO, Dict, Any, Optional, List
import logging
from io import BytesIO

logger = logging.getLogger(__name__)


class ObjectStorageService:
    """
    S3-compatible Object Storage service for SAP BTP.

    Handles all file operations for:
    - User uploaded files (data models, picklists)
    - Generated files (workbooks, import XMLs)
    - Temporary files
    """

    def __init__(self, app=None):
        """Initialize storage service."""
        self.bucket = None
        self.client = None
        self._initialized = False

        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize with Flask app context."""
        # Get credentials from VCAP_SERVICES
        vcap_services = os.environ.get('VCAP_SERVICES', '{}')

        try:
            vcap = json.loads(vcap_services)
        except json.JSONDecodeError:
            logger.warning("Could not parse VCAP_SERVICES, using fallback config")
            vcap = {}

        # Look for objectstore service (SAP BTP naming)
        objectstore_creds = None

        # Try different service names
        for service_name in ['objectstore', 's3', 'trexima-storage']:
            if service_name in vcap:
                objectstore_creds = vcap[service_name][0].get('credentials', {})
                break

        if not objectstore_creds:
            # Fallback to environment variables for local development
            objectstore_creds = {
                'bucket': os.environ.get('S3_BUCKET', 'trexima-storage'),
                'host': os.environ.get('S3_ENDPOINT', 'http://localhost:9000'),
                'access_key_id': os.environ.get('S3_ACCESS_KEY', 'minioadmin'),
                'secret_access_key': os.environ.get('S3_SECRET_KEY', 'minioadmin'),
                'region': os.environ.get('S3_REGION', 'us-east-1')
            }
            logger.info("Using fallback/local S3 configuration")

        self.bucket = objectstore_creds.get('bucket')

        # Determine endpoint URL
        endpoint_url = objectstore_creds.get('host') or objectstore_creds.get('endpoint')
        if endpoint_url and not endpoint_url.startswith('http'):
            endpoint_url = f"https://{endpoint_url}"

        try:
            self.client = boto3.client(
                's3',
                endpoint_url=endpoint_url,
                aws_access_key_id=objectstore_creds.get('access_key_id'),
                aws_secret_access_key=objectstore_creds.get('secret_access_key'),
                region_name=objectstore_creds.get('region', 'us-east-1'),
                config=Config(
                    signature_version='s3v4',
                    retries={'max_attempts': 3, 'mode': 'standard'}
                )
            )
            self._initialized = True
            logger.info(f"Object Storage initialized with bucket: {self.bucket}")
        except Exception as e:
            logger.error(f"Failed to initialize Object Storage: {e}")
            self._initialized = False

    @property
    def is_initialized(self) -> bool:
        """Check if storage is properly initialized."""
        return self._initialized and self.client is not None

    def _ensure_initialized(self):
        """Ensure storage is initialized before operations."""
        if not self.is_initialized:
            raise RuntimeError("Object Storage not initialized. Call init_app() first.")

    # =========================================================================
    # KEY GENERATION
    # =========================================================================

    @staticmethod
    def generate_upload_key(user_id: str, project_id: str, file_type: str, original_name: str) -> str:
        """Generate storage key for uploaded file."""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        safe_name = original_name.replace(' ', '_').replace('/', '_')
        return f"users/{user_id}/projects/{project_id}/uploads/{file_type}_{timestamp}_{safe_name}"

    @staticmethod
    def generate_output_key(user_id: str, project_id: str, file_type: str, filename: str) -> str:
        """Generate storage key for generated output file."""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        safe_name = filename.replace(' ', '_').replace('/', '_')
        return f"users/{user_id}/projects/{project_id}/generated/{file_type}_{timestamp}_{safe_name}"

    @staticmethod
    def generate_temp_key(session_id: str, filename: str) -> str:
        """Generate storage key for temporary file."""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        safe_name = filename.replace(' ', '_').replace('/', '_')
        return f"temp/{session_id}/{timestamp}_{safe_name}"

    # =========================================================================
    # UPLOAD OPERATIONS
    # =========================================================================

    def upload_file(self, file_obj: BinaryIO, key: str, content_type: str = None) -> Dict[str, Any]:
        """
        Upload a file to Object Store.

        Args:
            file_obj: File-like object to upload
            key: Storage key
            content_type: MIME type of the file

        Returns:
            Dict with key, size, and etag
        """
        self._ensure_initialized()

        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type

        try:
            self.client.upload_fileobj(file_obj, self.bucket, key, ExtraArgs=extra_args)

            # Get file metadata
            response = self.client.head_object(Bucket=self.bucket, Key=key)

            logger.info(f"Uploaded file to {key}")
            return {
                'key': key,
                'size': response['ContentLength'],
                'etag': response['ETag'].strip('"'),
                'content_type': content_type
            }
        except ClientError as e:
            logger.error(f"Failed to upload file {key}: {e}")
            raise

    def upload_bytes(self, data: bytes, key: str, content_type: str = None) -> Dict[str, Any]:
        """
        Upload bytes data to Object Store.

        Args:
            data: Bytes to upload
            key: Storage key
            content_type: MIME type

        Returns:
            Dict with key, size, and etag
        """
        return self.upload_file(BytesIO(data), key, content_type)

    # =========================================================================
    # DOWNLOAD OPERATIONS
    # =========================================================================

    def download_file(self, key: str) -> bytes:
        """
        Download a file from Object Store.

        Args:
            key: Storage key

        Returns:
            File contents as bytes
        """
        self._ensure_initialized()

        try:
            response = self.client.get_object(Bucket=self.bucket, Key=key)
            data = response['Body'].read()
            logger.info(f"Downloaded file from {key}")
            return data
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.warning(f"File not found: {key}")
                raise FileNotFoundError(f"File not found: {key}")
            logger.error(f"Failed to download file {key}: {e}")
            raise

    def download_to_file(self, key: str, local_path: str) -> str:
        """
        Download a file to local filesystem.

        Args:
            key: Storage key
            local_path: Local file path

        Returns:
            Local file path
        """
        self._ensure_initialized()

        try:
            self.client.download_file(self.bucket, key, local_path)
            logger.info(f"Downloaded {key} to {local_path}")
            return local_path
        except ClientError as e:
            logger.error(f"Failed to download file {key}: {e}")
            raise

    def get_download_url(self, key: str, expires_in: int = 3600, filename: str = None) -> str:
        """
        Generate a pre-signed download URL.

        Args:
            key: Storage key
            expires_in: URL expiry time in seconds (default 1 hour)
            filename: Optional filename for Content-Disposition header

        Returns:
            Pre-signed URL string
        """
        self._ensure_initialized()

        params = {'Bucket': self.bucket, 'Key': key}

        if filename:
            params['ResponseContentDisposition'] = f'attachment; filename="{filename}"'

        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params=params,
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate download URL for {key}: {e}")
            raise

    # =========================================================================
    # DELETE OPERATIONS
    # =========================================================================

    def delete_file(self, key: str) -> bool:
        """
        Delete a file from Object Store.

        Args:
            key: Storage key

        Returns:
            True if deleted successfully
        """
        self._ensure_initialized()

        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
            logger.info(f"Deleted file: {key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete file {key}: {e}")
            return False

    def delete_prefix(self, prefix: str) -> int:
        """
        Delete all files with a given prefix.

        Args:
            prefix: Key prefix to match

        Returns:
            Number of files deleted
        """
        self._ensure_initialized()

        deleted_count = 0

        try:
            paginator = self.client.get_paginator('list_objects_v2')

            for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
                if 'Contents' not in page:
                    continue

                objects = [{'Key': obj['Key']} for obj in page['Contents']]

                if objects:
                    response = self.client.delete_objects(
                        Bucket=self.bucket,
                        Delete={'Objects': objects}
                    )
                    deleted_count += len(response.get('Deleted', []))

            logger.info(f"Deleted {deleted_count} files with prefix: {prefix}")
            return deleted_count
        except ClientError as e:
            logger.error(f"Failed to delete files with prefix {prefix}: {e}")
            raise

    def delete_project_files(self, user_id: str, project_id: str) -> int:
        """
        Delete all files for a project.

        Args:
            user_id: User ID
            project_id: Project ID

        Returns:
            Number of files deleted
        """
        prefix = f"users/{user_id}/projects/{project_id}/"
        return self.delete_prefix(prefix)

    def delete_user_files(self, user_id: str) -> int:
        """
        Delete all files for a user.

        Args:
            user_id: User ID

        Returns:
            Number of files deleted
        """
        prefix = f"users/{user_id}/"
        return self.delete_prefix(prefix)

    # =========================================================================
    # UTILITY OPERATIONS
    # =========================================================================

    def file_exists(self, key: str) -> bool:
        """
        Check if a file exists.

        Args:
            key: Storage key

        Returns:
            True if file exists
        """
        self._ensure_initialized()

        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise

    def get_file_info(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get file metadata.

        Args:
            key: Storage key

        Returns:
            Dict with size, content_type, last_modified, or None if not found
        """
        self._ensure_initialized()

        try:
            response = self.client.head_object(Bucket=self.bucket, Key=key)
            return {
                'key': key,
                'size': response['ContentLength'],
                'content_type': response.get('ContentType'),
                'last_modified': response.get('LastModified'),
                'etag': response['ETag'].strip('"')
            }
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return None
            raise

    def list_files(self, prefix: str, max_keys: int = 1000) -> List[Dict[str, Any]]:
        """
        List files with a given prefix.

        Args:
            prefix: Key prefix to match
            max_keys: Maximum number of keys to return

        Returns:
            List of file info dicts
        """
        self._ensure_initialized()

        files = []

        try:
            paginator = self.client.get_paginator('list_objects_v2')

            for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix, PaginationConfig={'MaxItems': max_keys}):
                if 'Contents' not in page:
                    continue

                for obj in page['Contents']:
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'],
                        'etag': obj['ETag'].strip('"')
                    })

            return files
        except ClientError as e:
            logger.error(f"Failed to list files with prefix {prefix}: {e}")
            raise

    def get_storage_usage(self, user_id: str = None) -> Dict[str, Any]:
        """
        Get storage usage statistics.

        Args:
            user_id: Optional user ID to filter by

        Returns:
            Dict with total_files, total_size, breakdown by category
        """
        self._ensure_initialized()

        prefix = f"users/{user_id}/" if user_id else "users/"

        stats = {
            'total_files': 0,
            'total_size': 0,
            'uploads': {'count': 0, 'size': 0},
            'generated': {'count': 0, 'size': 0}
        }

        try:
            files = self.list_files(prefix, max_keys=10000)

            for f in files:
                stats['total_files'] += 1
                stats['total_size'] += f['size']

                if '/uploads/' in f['key']:
                    stats['uploads']['count'] += 1
                    stats['uploads']['size'] += f['size']
                elif '/generated/' in f['key']:
                    stats['generated']['count'] += 1
                    stats['generated']['size'] += f['size']

            return stats
        except ClientError as e:
            logger.error(f"Failed to get storage usage: {e}")
            return stats


# Singleton instance
storage_service = ObjectStorageService()


def init_storage(app):
    """Initialize storage with Flask app."""
    storage_service.init_app(app)
    return storage_service
