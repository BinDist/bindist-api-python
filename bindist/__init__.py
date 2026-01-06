"""
BinDist Python Client Library

A Python client for the Binary Distribution System API (bindist.eu).

Example usage:
    from bindist import CustomerClient, AdminClient

    # Customer API
    client = CustomerClient("https://api.bindist.eu", "your-api-key")
    apps = client.list_applications()

    # Admin API
    admin = AdminClient("https://api.bindist.eu", "admin-api-key")
    admin.upload_small_file("my-app", "1.0.0", "app.exe", file_bytes)
"""

from .base import BaseClient, ApiResponse
from .customer import CustomerClient
from .admin import AdminClient

__version__ = "1.0.0"
__all__ = [
    "BaseClient",
    "ApiResponse",
    "CustomerClient",
    "AdminClient",
]
