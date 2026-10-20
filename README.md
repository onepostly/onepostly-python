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

Every resource is its own API class built on a shared `Configuration` and `ApiClient`. Create an API key in the dashboard; it is sent as `Authorization: Bearer op_…`.

```python
import asyncio
import os

from onepostly import ApiClient, Configuration
from onepostly.api.accounts_api import AccountsApi
from onepostly.api.posts_api import PostsApi


async def main() -> None:
    configuration = Configuration(access_token=os.environ["ONEPOSTLY_API_KEY"])
    async with ApiClient(configuration) as api_client:
        accounts = await AccountsApi(api_client).list_accounts()

        created = await PostsApi(api_client).create_post(
            create_post_body={
                "text": "Hello from Onepostly.",
                "accounts": [{"accountId": accounts.data[0].id}],
            },
        )
        # One post per account, all sharing created.group_id.
        for post in created.data:
            print(post.id, post.platform, post.status)  # "publishing"


asyncio.run(main())
```

Methods are `async` and return deserialized pydantic models. The `…with_http_info()` variants return an `ApiResponse` with `status_code`, `headers`, and `raw_data` alongside `data`.

Pass plain dicts anywhere a model is expected. Pydantic validates them, and the API's field names (`accountId`, `scheduledFor`) work as keys.

The examples below run inside the same `async with ApiClient(configuration) as api_client:` block.

### Scheduling

```python
posts = PostsApi(api_client)

await posts.create_post(
    create_post_body={
        "text": "Join our product webinar next week.",
        "scheduledFor": "2027-03-15T09:00:00",  # local time in `timezone`
        "timezone": "America/New_York",
        "accounts": [{"accountId": "acc_…"}],
    },
)
# 201 Created, status "scheduled"

await posts.update_post("pst_…", update_post_body={"scheduledFor": "2027-03-16T09:00:00"})
await posts.delete_post("pst_…")  # cancels a scheduled post
```

### Media

Create a media item, upload the file to its `upload_url`, then use its id in a post:

```python
import httpx

from onepostly.api.media_api import MediaApi

with open("launch.mp4", "rb") as f:
    content = f.read()

item = await MediaApi(api_client).create_media(
    create_media_body={"filename": "launch.mp4", "contentType": "video/mp4", "size": len(content)},
)

httpx.put(item.upload_url, content=content, headers={"Content-Type": "video/mp4"})

await posts.create_post(
    create_post_body={
        "text": "Launch day",
        "media": [{"id": item.id}],
        "accounts": [{"accountId": "acc_…"}],
    },
)
```

The upload URL needs no API key and accepts exactly the declared type and size.

### Analytics

```python
from onepostly.api.analytics_api import AnalyticsApi

analytics = AnalyticsApi(api_client)

result = await analytics.get_post_analytics("pst_…")
print(result.status, result.metrics)

timeline = await analytics.get_post_analytics_timeline(
    "pst_…",
    since="2027-03-01T00:00:00Z",
    until="2027-03-29T00:00:00Z",  # exclusive
)
```

### Error handling

Every non-2xx response raises an `ApiException` subclass with the HTTP `status`, `reason`, and the raw response `body` attached. Subclasses map to status families (`UnauthorizedException`, `ForbiddenException`, `NotFoundException`, `ConflictException`, `ServiceException`, …). The body has a stable `code` to build logic on, and a `requestId` to share with support:

```python
from onepostly import ApiException

try:
    await posts.create_post(create_post_body={...})
except ApiException as error:
    print(error.status, error.body)
    # 400 {"error": "Invalid request: …", "code": "VALIDATION_ERROR", "param": "accounts.0.accountId", "requestId": "req_…"}
```

See [Errors](https://onepostly.com/docs/error-handling) for every code.

## API reference

Methods take their parameters by name; path parameters can also go first, in path order.

<!-- BEGIN GENERATED API REFERENCE -->

### AccountsApi

| Method | Description |
| --- | --- |
| `accounts.list_accounts()` | List accounts |
| `accounts.create_account()` | Connect a Bluesky account |
| `accounts.get_account()` | Get account |
| `accounts.delete_account()` | Disconnect account |
| `accounts.update_account()` | Update account |
| `accounts.reconnect_account()` | Reconnect account |
| `accounts.get_account_stats()` | Get account stats |
| `accounts.list_account_reviews()` | List Page reviews |
| `accounts.get_messenger_profile()` | Get Messenger profile |
| `accounts.set_messenger_profile()` | Set Messenger profile |
| `accounts.list_account_boards()` | List Pinterest boards |
| `accounts.create_account_board()` | Create Pinterest board |
| `accounts.get_creator_info()` | Get TikTok creator info |
| `accounts.get_account_settings()` | Get account settings |
| `accounts.update_account_settings()` | Update account settings |
| `accounts.list_account_media()` | List account media |
| `accounts.search_account_audio()` | Search Instagram audio |

### ConnectApi

| Method | Description |
| --- | --- |
| `connect.create_connect_session()` | Create connect session |
| `connect.list_connect_candidates()` | List candidates |
| `connect.select_connect_candidate()` | Select candidate |

### ProfilesApi

| Method | Description |
| --- | --- |
| `profiles.list_profiles()` | List profiles |
| `profiles.create_profile()` | Create profile |
| `profiles.delete_profile()` | Delete profile |
| `profiles.update_profile()` | Rename profile |

### MediaApi

| Method | Description |
| --- | --- |
| `media.list_media()` | List media |
| `media.create_media()` | Create media |
| `media.get_media()` | Get media |
| `media.delete_media()` | Delete media |

### PostsApi

| Method | Description |
| --- | --- |
| `posts.list_posts()` | List posts |
| `posts.create_post()` | Create post |
| `posts.get_post()` | Get post |
| `posts.delete_post()` | Delete post |
| `posts.update_post()` | Update post |
| `posts.sync_account_posts()` | Sync account posts |

### AnalyticsApi

| Method | Description |
| --- | --- |
| `analytics.get_post_analytics()` | Get post analytics |
| `analytics.get_post_analytics_timeline()` | Get post analytics timeline |
| `analytics.get_account_analytics()` | Get account analytics |

### CommentsApi

| Method | Description |
| --- | --- |
| `comments.list_comments()` | List comments |
| `comments.create_comment()` | Comment on a post |
| `comments.reply_to_comment()` | Reply to a comment |
| `comments.delete_comment()` | Delete comment |
| `comments.hide_comment()` | Hide comment |
| `comments.unhide_comment()` | Unhide comment |
| `comments.like_comment()` | Like comment |
| `comments.unlike_comment()` | Unlike comment |
| `comments.send_private_reply()` | Send private reply |

### EngagementApi

| Method | Description |
| --- | --- |
| `engagement.like_post()` | Like a post |
| `engagement.unlike_post()` | Remove a like |
| `engagement.bookmark_post()` | Bookmark a post |
| `engagement.unbookmark_post()` | Remove a bookmark |
| `engagement.repost_post()` | Repost a post |
| `engagement.unrepost_post()` | Undo a repost |
| `engagement.list_reposters()` | List reposters |

### InboxApi

| Method | Description |
| --- | --- |
| `inbox.list_conversations()` | List conversations |
| `inbox.create_conversation()` | Create conversation |
| `inbox.get_conversation()` | Get conversation |
| `inbox.list_messages()` | List messages |
| `inbox.send_message()` | Send message |

### AutomationsApi

| Method | Description |
| --- | --- |
| `automations.list_automations()` | List automations |
| `automations.create_automation()` | Create automation |
| `automations.get_automation()` | Get automation |
| `automations.delete_automation()` | Delete automation |
| `automations.update_automation()` | Update automation |

### WebhooksApi

| Method | Description |
| --- | --- |
| `webhooks.list_webhook_event_types()` | List event types |
| `webhooks.list_webhooks()` | List webhooks |
| `webhooks.create_webhook()` | Create webhook |
| `webhooks.get_webhook()` | Get webhook |
| `webhooks.delete_webhook()` | Delete webhook |
| `webhooks.update_webhook()` | Update webhook |
| `webhooks.rotate_webhook_secret()` | Rotate signing secret |
| `webhooks.list_webhook_deliveries()` | List deliveries |
| `webhooks.get_webhook_delivery()` | Get delivery |
| `webhooks.retry_webhook_delivery()` | Retry delivery |
| `webhooks.test_webhook()` | Send test event |

### WalletApi

| Method | Description |
| --- | --- |
| `wallet.get_wallet_balance()` | Get wallet balance |
<!-- END GENERATED API REFERENCE -->

A JSON body goes in under its schema name, such as `create_post_body`. Every operation, with request and response examples in Python, is in the [API Reference](https://onepostly.com/docs/api-reference).

## Links

- [Documentation](https://onepostly.com/docs)
- [API Reference](https://onepostly.com/docs/api-reference)
- [Dashboard](https://app.onepostly.com)
- [OpenAPI spec](https://onepostly.com/openapi.json)

## License

Apache-2.0
