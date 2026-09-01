<p align="center">
  <a href="https://onepostly.com">
    <img src="https://cdn.onepostly.com/banner.png" alt="Onepostly — One API for all social media" width="640">
  </a>
</p>

<p align="center">
  <a href="https://pypi.org/project/onepostly/"><img src="https://img.shields.io/pypi/v/onepostly.svg" alt="PyPI version"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0-blue.svg" alt="License"></a>
</p>

<p align="center">
  Official Python SDK for the <a href="https://onepostly.com">Onepostly API</a> — publish, schedule, and read results<br>
  across all supported social platforms with one request shape. See the <a href="https://onepostly.com/docs">docs</a> for the current platform list.
</p>

<p align="center">
  Python 3.10+.
</p>

## Installation

```sh
pip install onepostly
```

## Usage

Every resource is its own API class built on a shared `Configuration` and `ApiClient`:

```python
import os
from onepostly import ApiClient, Configuration
from onepostly.api.posts_api import PostsApi

configuration = Configuration(
    api_key={"ApiKeyHeader": os.environ["ONEPOSTLY_API_KEY"]},  # sent as the `x-api-key` header
)

with ApiClient(configuration) as api_client:
    posts = PostsApi(api_client)

    response = await posts.create_post(
        create_post_body={
            "text": "Hello from Onepostly",
            "mediaKind": "text",
            "destinations": [{"connectionId": "…"}],
        }
    )
    print(response.post.id, response.post.status)  # "queued"
```

Methods are `async` and return deserialized pydantic models (`PostResponse`, `ListPosts200Response`, …). The `…with_http_info()` variants return an `ApiResponse` with `status_code`, `headers`, and `raw_data` alongside `data`.

Pass plain dicts anywhere a model is expected — pydantic validates and coerces them (alias names like `connectionId` and `mediaKind` are accepted on both keys and fields).

### Scheduling

```python
await posts.create_post(
    create_post_body={
        "text": "Tomorrow morning",
        "scheduledFor": "2026-09-01T09:00:00",  # timezone-naive local time
        "timezone": "Europe/Istanbul",
        "destinations": [{"connectionId": "…"}],
    }
)
# 201 Created, status "scheduled"
```

### Media

```python
from onepostly.api.media_api import MediaApi

media_api = MediaApi(api_client)

with open("photo.jpg", "rb") as f:
    upload = await media_api.upload_media(file=f)
media_url = upload.media.url

await posts.create_post(
    create_post_body={
        "text": "With an image",
        "mediaKind": "image",
        "mediaUrls": [media_url],
        "destinations": [{"connectionId": "…"}],
    }
)
```

### Insights

```python
from onepostly.api.insights_api import InsightsApi

insights_api = InsightsApi(api_client)

post_insights = await insights_api.get_post_insights(id=post_id)
for destination in post_insights.insights.destinations or []:
    print(destination.platform, destination.metrics)

timeline = await insights_api.get_post_insights_timeline(
    id=post_id,
    var_from="2026-08-01",  # inclusive, YYYY-MM-DD (`from` is a Python keyword)
    to="2026-08-28",        # inclusive, YYYY-MM-DD
)
```

### Error handling

Every non-2xx response raises an `ApiException` subclass with the HTTP `status`, `reason`, and the raw response `body` attached. Subclasses map to status families (`UnauthorizedException`, `ForbiddenException`, `NotFoundException`, `ConflictException`, `ServiceException`, …):

```python
from onepostly import ApiException

try:
    await posts.create_post(create_post_body={/* … */})
except ApiException as error:
    print(error.status, error.body)
    # 402 {"error": {"code": "INSUFFICIENT_WALLET", "message": "…"}}
```

## API reference

All methods take named keyword arguments.

<!-- BEGIN GENERATED API REFERENCE -->

### ConnectionsApi

| Method | Description |
| --- | --- |
| `connections.list_connections()` | List connections |
| `connections.get_connection_stats()` | Get connection account stats |
| `connections.list_connection_media()` | List creator media |
| `connections.get_tik_tok_creator_info()` | Get TikTok creator info |
| `connections.list_pinterest_boards()` | List Pinterest boards |
| `connections.create_pinterest_board()` | Create Pinterest board |
| `connections.connect_bluesky()` | Connect Bluesky via App Password |
| `connections.start_o_auth()` | Start OAuth connect |
| `connections.list_facebook_pages()` | List Facebook Pages for pending connect |
| `connections.select_facebook_page()` | Select Facebook Page and finish connect |

### MediaApi

| Method | Description |
| --- | --- |
| `media.list_media()` | List media |
| `media.upload_media()` | Upload media |
| `media.delete_media()` | Delete media |

### PostsApi

| Method | Description |
| --- | --- |
| `posts.list_posts()` | List posts |
| `posts.create_post()` | Create post |
| `posts.get_post()` | Get post |
| `posts.cancel_post()` | Cancel post |
| `posts.delete_post_destination()` | Remote-delete destination |

### InsightsApi

| Method | Description |
| --- | --- |
| `insights.get_post_insights()` | Get insights |
| `insights.get_post_insights_timeline()` | Get daily insights timeline |

### CommentsApi

| Method | Description |
| --- | --- |
| `comments.list_comments()` | List comments |
| `comments.create_comment()` | Create reply |
| `comments.delete_comment()` | Delete own comment |

### EngagementApi

| Method | Description |
| --- | --- |
| `engagement.list_retweeters()` | List retweeters |
| `engagement.retweet()` | Retweet |
| `engagement.undo_retweet()` | Undo retweet |
| `engagement.like()` | Like |
| `engagement.unlike()` | Unlike |
| `engagement.bookmark()` | Bookmark |
| `engagement.remove_bookmark()` | Remove bookmark |
| `engagement.quote()` | Quote tweet |

### WebhooksApi

| Method | Description |
| --- | --- |
| `webhooks.list_webhook_event_types()` | List webhook event types |
| `webhooks.list_webhooks()` | List webhooks |
| `webhooks.create_webhook()` | Create webhook |
| `webhooks.get_webhook()` | Get webhook |
| `webhooks.delete_webhook()` | Delete webhook |
| `webhooks.update_webhook()` | Update webhook |
| `webhooks.rotate_webhook_secret()` | Rotate webhook secret |
| `webhooks.list_webhook_deliveries()` | List webhook deliveries |
| `webhooks.test_webhook()` | Send test event |
<!-- END GENERATED API REFERENCE -->

Representative signatures:

```python
# PostsApi — id/destination-scoped actions take id / destination_id
await posts.create_post(create_post_body=…)            # → PostResponse
await posts.list_posts(limit=None, offset=None)        # → ListPosts200Response
await posts.get_post(id=…)                             # → PostResponse
await posts.cancel_post(id=…)                          # → PostResponse
await posts.delete_post_destination(id=…, destination_id=…)  # remote-delete

# EngagementApi — body-bearing actions take a body model or dict
await engagement.retweet(id=…, destination_id_body={"destinationId": "…"})
await engagement.undo_retweet(id=…, destination_id=…)
await engagement.like(id=…, destination_id_body={"destinationId": "…"})
await engagement.quote(id=…, quote_body={"destinationId": "…", "text": "…"})
await engagement.list_retweeters(id=…, destination_id=None, limit=None, cursor=None)

# CommentsApi
await comments.create_comment(id=…, create_comment_body={"destinationId": "…", "text": "…"})
await comments.list_comments(id=…, destination_id=None, limit=None, cursor=None)
await comments.delete_comment(id=…, comment_id=…, destination_id=…)

# WebhooksApi
await webhooks.create_webhook(create_webhook_body={"name": "…", "url": "…", "events": […]})
await webhooks.update_webhook(id=…, update_webhook_body={…})
await webhooks.rotate_webhook_secret(id=…)
await webhooks.test_webhook(id=…)
```

## Links

- [Documentation](https://onepostly.com/docs)
- [Dashboard](https://app.onepostly.com)
- [OpenAPI spec](https://onepostly.com/openapi.json)

## License

Apache-2.0
