"""Base HTTP client with authentication."""

import requests
from dataclasses import dataclass


@dataclass
class ApiResponse:
    """Wrapper for API responses."""

    success: bool
    status_code: int
    data: dict | None
    error: dict | None
    meta: dict | None
    raw: dict

    @classmethod
    def from_response(cls, response: requests.Response) -> 'ApiResponse':
        """Create ApiResponse from requests.Response."""
        try:
            json_data = response.json()
        except requests.exceptions.JSONDecodeError:
            json_data = {'success': False, 'error': {'message': response.text}}

        return cls(
            success=json_data.get('success', False),
            status_code=response.status_code,
            data=json_data.get('data'),
            error=json_data.get('error'),
            meta=json_data.get('meta'),
            raw=json_data,
        )


class BaseClient:
    """Base HTTP client with authentication support."""

    def __init__(self, base_url: str, api_key: str):
        """
        Initialize the base client.

        Args:
            base_url: API base URL (e.g., https://api.bindist.eu)
            api_key: API key in format {tenant_id}.{secret}
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        })

    def _url(self, path: str) -> str:
        """Build full URL from path."""
        return f"{self.base_url}/v1{path}"

    def get(
        self,
        path: str,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> ApiResponse:
        """Make GET request."""
        response = self.session.get(
            self._url(path),
            params=params,
            headers=headers,
        )
        return ApiResponse.from_response(response)

    def post(
        self,
        path: str,
        json: dict | None = None,
        headers: dict | None = None,
    ) -> ApiResponse:
        """Make POST request."""
        response = self.session.post(
            self._url(path),
            json=json,
            headers=headers,
        )
        return ApiResponse.from_response(response)

    def patch(
        self,
        path: str,
        json: dict | None = None,
        headers: dict | None = None,
    ) -> ApiResponse:
        """Make PATCH request."""
        response = self.session.patch(
            self._url(path),
            json=json,
            headers=headers,
        )
        return ApiResponse.from_response(response)

    def delete(
        self,
        path: str,
        headers: dict | None = None,
    ) -> ApiResponse:
        """Make DELETE request."""
        response = self.session.delete(
            self._url(path),
            headers=headers,
        )
        return ApiResponse.from_response(response)

    def put_binary(
        self,
        url: str,
        data: bytes,
        content_type: str = 'application/octet-stream',
    ) -> requests.Response:
        """
        Upload binary data to a URL (for S3 pre-signed uploads).

        Note: This doesn't use the session headers since it's for S3.
        """
        return requests.put(
            url,
            data=data,
            headers={'Content-Type': content_type},
        )

    def download(self, url: str) -> bytes:
        """
        Download file from URL (for S3 pre-signed downloads).

        Note: This doesn't use the session headers since it's for S3.
        """
        response = requests.get(url)
        response.raise_for_status()
        return response.content
