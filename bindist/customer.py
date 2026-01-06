"""Customer API client for end-users."""

import hashlib
from typing import Any

from .base import BaseClient, ApiResponse


class CustomerClient(BaseClient):
    """
    Client for customer API endpoints.

    Use this client for end-user operations like listing applications,
    versions, and downloading files.
    """

    def list_applications(
        self,
        search: str | None = None,
        tags: list[str] | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> ApiResponse:
        """
        List available applications.

        Args:
            search: Search term to filter applications
            tags: List of tags to filter by
            page: Page number
            page_size: Items per page

        Returns:
            ApiResponse with applications list
        """
        params: dict[str, Any] = {
            "page": page,
            "pageSize": page_size,
        }
        if search:
            params["search"] = search
        if tags:
            params["tags"] = ",".join(tags)

        return self.get("/applications", params=params)

    def get_application(self, application_id: str) -> ApiResponse:
        """
        Get application details.

        Args:
            application_id: Application ID

        Returns:
            ApiResponse with application details
        """
        return self.get(f"/applications/{application_id}")

    def list_versions(
        self,
        application_id: str,
        changelog: str | None = None,
        test_channel: bool = False,
    ) -> ApiResponse:
        """
        List versions for an application.

        Args:
            application_id: Application ID
            changelog: Search term for release notes
            test_channel: If True, include disabled versions

        Returns:
            ApiResponse with versions list
        """
        params = {}
        if changelog:
            params["changelog"] = changelog

        headers = {}
        if test_channel:
            headers["X-Channel"] = "Test"

        return self.get(
            f"/applications/{application_id}/versions",
            params=params if params else None,
            headers=headers if headers else None,
        )

    def list_version_files(
        self,
        application_id: str,
        version: str,
    ) -> ApiResponse:
        """
        List files in a version.

        Args:
            application_id: Application ID
            version: Version string

        Returns:
            ApiResponse with files list
        """
        return self.get(f"/applications/{application_id}/versions/{version}/files")

    def get_download_url(
        self,
        application_id: str,
        version: str,
        file_id: str | None = None,
        test_channel: bool = False,
    ) -> ApiResponse:
        """
        Get pre-signed download URL.

        Args:
            application_id: Application ID
            version: Version string
            file_id: Optional file ID for multi-file versions
            test_channel: If True, allow downloading disabled versions

        Returns:
            ApiResponse with download URL and file metadata
        """
        params = {
            "applicationId": application_id,
            "version": version,
        }
        if file_id:
            params["fileId"] = file_id

        headers = {}
        if test_channel:
            headers["X-Channel"] = "Test"

        return self.get(
            "/downloads/url",
            params=params,
            headers=headers if headers else None,
        )

    def download_file(
        self,
        application_id: str,
        version: str,
        file_id: str | None = None,
        test_channel: bool = False,
        verify_checksum: bool = True,
    ) -> tuple[bytes, dict[str, Any]]:
        """
        Download a file and optionally verify checksum.

        Args:
            application_id: Application ID
            version: Version string
            file_id: Optional file ID for multi-file versions
            test_channel: If True, allow downloading disabled versions
            verify_checksum: If True, verify SHA256 checksum

        Returns:
            Tuple of (file_content, metadata_dict)

        Raises:
            ValueError: If checksum verification fails
            Exception: If download URL request fails
        """
        url_response = self.get_download_url(
            application_id=application_id,
            version=version,
            file_id=file_id,
            test_channel=test_channel,
        )

        if not url_response.success or url_response.data is None:
            raise Exception(f"Failed to get download URL: {url_response.error}")

        data = url_response.data
        download_url: str = data["url"]
        expected_checksum: str | None = data.get("checksum")
        metadata: dict[str, Any] = {
            "fileName": data.get("fileName"),
            "fileSize": data.get("fileSize"),
            "checksum": expected_checksum,
            "expiresAt": data.get("expiresAt"),
        }

        content = self.download(download_url)

        if verify_checksum and expected_checksum:
            actual_checksum = hashlib.sha256(content).hexdigest()
            if actual_checksum != expected_checksum:
                raise ValueError(
                    f"Checksum mismatch: expected {expected_checksum}, "
                    f"got {actual_checksum}"
                )

        return content, metadata

    def create_share_link(
        self,
        application_id: str,
        version: str,
        file_id: str | None = None,
        expires_minutes: int = 30,
    ) -> ApiResponse:
        """
        Create a public share link for a file.

        Args:
            application_id: Application ID
            version: Version string
            file_id: Optional file ID for multi-file versions
            expires_minutes: Link expiration time (5-1440 minutes)

        Returns:
            ApiResponse with share link details
        """
        payload = {
            "applicationId": application_id,
            "version": version,
            "expiresMinutes": expires_minutes,
        }
        if file_id:
            payload["fileId"] = file_id

        return self.post("/downloads/share", json=payload)

    def get_stats(self, application_id: str) -> ApiResponse:
        """
        Get download statistics for an application.

        Args:
            application_id: Application ID

        Returns:
            ApiResponse with statistics
        """
        return self.get(f"/applications/{application_id}/stats")
