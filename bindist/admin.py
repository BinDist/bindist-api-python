"""Admin/Management API client."""

import base64
import hashlib
from typing import Any

from .base import BaseClient, ApiResponse


class AdminClient(BaseClient):
    """
    Client for admin/management API endpoints.

    Use this client for administrative operations like creating customers,
    applications, and uploading versions.
    """

    def create_customer(
        self,
        name: str,
        parent_customer_id: str = "admin",
        notes: str | None = None,
    ) -> ApiResponse:
        """
        Create a new customer with an API key.

        Args:
            name: Customer display name
            parent_customer_id: Parent customer ID (default: admin)
            notes: Optional customer notes

        Returns:
            ApiResponse with customer details and API key
        """
        payload: dict[str, Any] = {
            "name": name,
        }
        if notes:
            payload["notes"] = notes

        return self.post(
            f"/management/customers/{parent_customer_id}/apikeys",
            json=payload,
        )

    def create_application(
        self,
        application_id: str,
        name: str,
        customer_ids: list[str],
        description: str | None = None,
        tags: list[str] | None = None,
    ) -> ApiResponse:
        """
        Create a new application.

        Args:
            application_id: Unique application identifier
            name: Application display name
            customer_ids: List of customer IDs to assign
            description: Optional description
            tags: Optional list of tags

        Returns:
            ApiResponse with application details
        """
        payload = {
            "applicationId": application_id,
            "name": name,
            "customerIds": customer_ids,
        }
        if description:
            payload["description"] = description
        if tags:
            payload["tags"] = tags

        return self.post("/management/applications", json=payload)

    def upload_small_file(
        self,
        application_id: str,
        version: str,
        file_name: str,
        file_content: bytes,
        release_notes: str | None = None,
    ) -> ApiResponse:
        """
        Upload a small file (< 10MB) directly.

        Args:
            application_id: Application ID
            version: Version string (e.g., "1.0.0")
            file_name: Name of the file
            file_content: File content as bytes
            release_notes: Optional release notes

        Returns:
            ApiResponse with version details
        """
        payload = {
            "applicationId": application_id,
            "version": version,
            "fileName": file_name,
            "fileContent": base64.b64encode(file_content).decode("utf-8"),
            "fileType": "MAIN",
        }
        if release_notes:
            payload["releaseNotes"] = release_notes

        return self.post("/management/upload", json=payload)

    def get_large_upload_url(
        self,
        application_id: str,
        version: str,
        file_name: str,
        file_size: int,
        content_type: str = "application/octet-stream",
    ) -> ApiResponse:
        """
        Get a pre-signed URL for large file upload.

        Args:
            application_id: Application ID
            version: Version string
            file_name: Name of the file
            file_size: Size of the file in bytes
            content_type: MIME type of the file

        Returns:
            ApiResponse with uploadId and uploadUrl
        """
        payload = {
            "applicationId": application_id,
            "version": version,
            "fileName": file_name,
            "fileSize": file_size,
            "contentType": content_type,
        }

        return self.post("/management/upload/large-url", json=payload)

    def complete_large_upload(
        self,
        upload_id: str,
        application_id: str,
        version: str,
        file_name: str,
        file_size: int,
        checksum: str,
        release_notes: str | None = None,
    ) -> ApiResponse:
        """
        Complete a large file upload.

        Args:
            upload_id: Upload ID from get_large_upload_url
            application_id: Application ID
            version: Version string
            file_name: Name of the file
            file_size: Size of the file in bytes
            checksum: SHA256 checksum of the file
            release_notes: Optional release notes

        Returns:
            ApiResponse with version details
        """
        payload = {
            "uploadId": upload_id,
            "applicationId": application_id,
            "version": version,
            "fileName": file_name,
            "fileSize": file_size,
            "checksum": checksum,
        }
        if release_notes:
            payload["releaseNotes"] = release_notes

        return self.post("/management/upload/large-complete", json=payload)

    def upload_large_file(
        self,
        application_id: str,
        version: str,
        file_name: str,
        file_content: bytes,
        release_notes: str | None = None,
    ) -> ApiResponse:
        """
        Upload a large file using multi-step process.

        Args:
            application_id: Application ID
            version: Version string
            file_name: Name of the file
            file_content: File content as bytes
            release_notes: Optional release notes

        Returns:
            ApiResponse with version details
        """
        file_size = len(file_content)
        checksum = hashlib.sha256(file_content).hexdigest()

        # Step 1: Get upload URL
        url_response = self.get_large_upload_url(
            application_id=application_id,
            version=version,
            file_name=file_name,
            file_size=file_size,
        )

        if not url_response.success or url_response.data is None:
            return url_response

        upload_id: str = url_response.data["uploadId"]
        upload_url: str = url_response.data["uploadUrl"]

        # Step 2: Upload to S3
        s3_response = self.put_binary(upload_url, file_content)
        if s3_response.status_code != 200:
            from .base import ApiResponse as AR

            return AR(
                success=False,
                status_code=s3_response.status_code,
                data=None,
                error={"message": f"S3 upload failed: {s3_response.text}"},
                meta=None,
                raw={"error": s3_response.text},
            )

        # Step 3: Complete upload
        return self.complete_large_upload(
            upload_id=upload_id,
            application_id=application_id,
            version=version,
            file_name=file_name,
            file_size=file_size,
            checksum=checksum,
            release_notes=release_notes,
        )

    def update_version(
        self,
        application_id: str,
        version: str,
        is_enabled: bool | None = None,
        is_active: bool | None = None,
        release_notes: str | None = None,
        minimum_client_version: str | None = None,
    ) -> ApiResponse:
        """
        Update version metadata.

        Args:
            application_id: Application ID
            version: Version string
            is_enabled: Enable/disable for production
            is_active: Activate/deactivate version
            release_notes: Update release notes
            minimum_client_version: Set minimum client version

        Returns:
            ApiResponse with updated version details
        """
        payload: dict[str, Any] = {}
        if is_enabled is not None:
            payload["isEnabled"] = is_enabled
        if is_active is not None:
            payload["isActive"] = is_active
        if release_notes is not None:
            payload["releaseNotes"] = release_notes
        if minimum_client_version is not None:
            payload["minimumClientVersion"] = minimum_client_version

        return self.patch(
            f"/applications/{application_id}/versions/{version}",
            json=payload,
        )

    def update_customer(
        self,
        customer_id: str,
        name: str | None = None,
        is_active: bool | None = None,
        notes: str | None = None,
    ) -> ApiResponse:
        """
        Update customer metadata.

        Args:
            customer_id: Customer ID
            name: New display name
            is_active: Enable/disable customer
            notes: Update notes

        Returns:
            ApiResponse with updated customer details
        """
        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if is_active is not None:
            payload["isActive"] = is_active
        if notes is not None:
            payload["notes"] = notes

        return self.patch(
            f"/management/customers/{customer_id}",
            json=payload,
        )

    def delete_application(self, application_id: str) -> ApiResponse:
        """
        Soft-delete an application.

        Args:
            application_id: Application ID to delete

        Returns:
            ApiResponse with deletion status
        """
        return self.delete(f"/management/applications/{application_id}")

    def list_activity(
        self,
        activity_type: str | None = None,
        application_id: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> ApiResponse:
        """
        List upload and download activity.

        Args:
            activity_type: Filter by type ('upload' or 'download')
            application_id: Filter by application
            page: Page number
            page_size: Items per page

        Returns:
            ApiResponse with activity list
        """
        params: dict[str, Any] = {
            "page": page,
            "pageSize": page_size,
        }
        if activity_type:
            params["type"] = activity_type
        if application_id:
            params["applicationId"] = application_id

        return self.get("/activity", params=params)

    def list_customers(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> ApiResponse:
        """
        List all customers.

        Args:
            page: Page number
            page_size: Items per page

        Returns:
            ApiResponse with customers list
        """
        params = {
            "page": page,
            "pageSize": page_size,
        }
        return self.get("/management/customers", params=params)
