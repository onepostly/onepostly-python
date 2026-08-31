# onepostly

Official Python SDK for the [Onepostly API](https://onepostly.com/docs) — publish, schedule, and read results across all supported social platforms with one request shape. See the [docs](https://onepostly.com/docs) for the current platform list.

Python 3.10+.

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

| API class | Methods |
| --- | --- |
| `PostsApi` | `create_post` `list_posts` `get_post` `cancel_post` `delete_post_destination` |
| `MediaApi` | `upload_media` `list_media` `delete_media` |
| `ConnectionsApi` | `list_connections` `get_connection_stats` `list_connection_media` `get_tik_tok_creator_info` `list_pinterest_boards` `create_pinterest_board` `connect_bluesky` `start_o_auth` `list_facebook_pages` `select_facebook_page` |
| `InsightsApi` | `get_post_insights` `get_post_insights_timeline` |
| `CommentsApi` | `list_comments` `create_comment` `delete_comment` |
| `EngagementApi` | `list_retweeters` `retweet` `undo_retweet` `like` `unlike` `bookmark` `remove_bookmark` `quote` |
| `WebhooksApi` | `list_webhook_event_types` `list_webhooks` `create_webhook` `get_webhook` `update_webhook` `delete_webhook` `rotate_webhook_secret` `list_webhook_deliveries` `test_webhook` |

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

Full request/response reference: [onepostly.com/openapi.json](https://onepostly.com/openapi.json)
