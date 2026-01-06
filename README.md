# BinDist Python API Client

Python client library for the BinDist API.

## Requirements

- Python 3.10+
- `requests` library

## Installation

```bash
pip install requests
```

Then copy the `bindist` package to your project, or install from source:

```bash
pip install -e .
```

## Usage

### Customer Client

Use `CustomerClient` for end-user operations like listing applications and downloading files.

```python
from bindist import CustomerClient

client = CustomerClient("https://api.bindist.com", "your-api-key")

# List applications
apps = client.list_applications()
if apps.success:
    for app in apps.data['applications']:
        print(f"{app['name']} ({app['applicationId']})")

# List applications with filters
apps = client.list_applications(
    search="myapp",
    tags=["windows", "desktop"],
    page=1,
    page_size=10,
)

# Get application details
app = client.get_application("myapp")
if app.success:
    print(f"Name: {app.data['name']}")
    print(f"Description: {app.data['description']}")

# List versions
versions = client.list_versions("myapp")
if versions.success:
    for ver in versions.data['versions']:
        print(f"{ver['version']} - {ver['fileSize']} bytes")

# List versions including disabled (test channel)
versions = client.list_versions("myapp", test_channel=True)

# List files in a version
files = client.list_version_files("myapp", "1.0.0")
if files.success:
    for f in files.data['files']:
        print(f"{f['fileName']} ({f['fileType']}) - {f['fileSize']} bytes")

# Get download URL
download = client.get_download_url("myapp", "1.0.0")
if download.success:
    print(f"URL: {download.data['url']}")
    print(f"Expires: {download.data['expiresAt']}")

# Download file with checksum verification
content, metadata = client.download_file("myapp", "1.0.0")
with open(metadata['fileName'], 'wb') as f:
    f.write(content)
print(f"Downloaded {metadata['fileName']} ({metadata['fileSize']} bytes)")

# Download specific file from multi-file version
content, metadata = client.download_file("myapp", "1.0.0", file_id="file-uuid")

# Create a share link
share = client.create_share_link("myapp", "1.0.0", expires_minutes=60)
if share.success:
    print(f"Share URL: {share.data['shareUrl']}")

# Get download statistics
stats = client.get_stats("myapp")
if stats.success:
    print(f"Total downloads: {stats.data['totalDownloads']}")
```

### Admin Client

Use `AdminClient` for administrative operations like creating applications and uploading files.

```python
from bindist import AdminClient

admin = AdminClient("https://api.bindist.com", "admin-api-key")

# Create a customer
customer = admin.create_customer(
    name="Acme Corp",
    tier="Premium",
    notes="Enterprise customer",
)
if customer.success:
    print(f"Customer ID: {customer.data['customerId']}")
    print(f"API Key: {customer.data['apiKey']}")

# Create an application
app = admin.create_application(
    application_id="myapp",
    name="My Application",
    customer_ids=["customer-1", "customer-2"],
    description="A great application",
    tags=["windows", "desktop"],
)

# Upload a small file (< 10MB)
with open("app.exe", "rb") as f:
    content = f.read()

result = admin.upload_small_file(
    application_id="myapp",
    version="1.0.0",
    file_name="app.exe",
    file_content=content,
    release_notes="Initial release",
)

# Upload a large file (>= 10MB)
with open("large-app.exe", "rb") as f:
    content = f.read()

result = admin.upload_large_file(
    application_id="myapp",
    version="2.0.0",
    file_name="large-app.exe",
    file_content=content,
    release_notes="Major update",
)

# Update version metadata
admin.update_version(
    application_id="myapp",
    version="1.0.0",
    is_enabled=True,  # Enable for production
    release_notes="Updated release notes",
)

# Update customer
admin.update_customer(
    customer_id="customer-1",
    name="New Name",
    is_active=True,
)

# Delete an application (soft delete)
admin.delete_application("myapp")

# List activity (uploads and downloads)
activity = admin.list_activity(activity_type="download", page=1)
if activity.success:
    for item in activity.data['activities']:
        print(f"{item['type']}: {item['applicationId']} v{item['version']}")

# List customers
customers = admin.list_customers()
if customers.success:
    for c in customers.data['customers']:
        print(f"{c['name']} ({c['customerId']})")
```

## API Response

All API methods return an `ApiResponse` object:

```python
@dataclass
class ApiResponse:
    success: bool           # Whether the request succeeded
    status_code: int        # HTTP status code
    data: dict | None       # Response data (if successful)
    error: dict | None      # Error details (if failed)
    meta: dict | None       # Response metadata
    raw: dict               # Raw response body
```

### Error Handling

```python
response = client.list_applications()

if response.success:
    # Process response.data
    apps = response.data['applications']
else:
    # Handle error
    print(f"Error: {response.error.get('message')}")
    print(f"Code: {response.error.get('code')}")
    print(f"Status: {response.status_code}")
```

### Download with Checksum Verification

The `download_file` method automatically verifies SHA256 checksums:

```python
try:
    content, metadata = client.download_file("myapp", "1.0.0")
except ValueError as e:
    print(f"Checksum verification failed: {e}")
except Exception as e:
    print(f"Download failed: {e}")
```

To skip checksum verification:

```python
content, metadata = client.download_file("myapp", "1.0.0", verify_checksum=False)
```

## License

MIT License - see [LICENSE](LICENSE) for details.
