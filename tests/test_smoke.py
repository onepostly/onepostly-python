# Offline smoke tests: the generated client must shape requests correctly.
# httpx.MockTransport stands in for the network (the generated REST layer
# builds its own AsyncClient, so we patch it after construction).
import json

import httpx
import pytest

from onepostly import ApiClient, Configuration
from onepostly.api.engagement_api import EngagementApi
from onepostly.api.media_api import MediaApi
from onepostly.api.posts_api import PostsApi


def _client(handler) -> ApiClient:
    config = Configuration(host="https://api.onepostly.com")
    config.api_key["ApiKeyHeader"] = "op_test"
    api_client = ApiClient(configuration=config)
    api_client.rest_client.pool_manager = httpx.AsyncClient(
        transport=httpx.MockTransport(handler)
    )
    return api_client


@pytest.mark.asyncio
async def test_create_post_sends_body_and_api_key():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["body"] = json.loads(request.content)
        seen["api_key"] = request.headers.get("x-api-key")
        return httpx.Response(
            202,
            json={
                "post": {
                    "id": "1699f415-7fb6-43f4-9d2a-c447491f32a8",
                    "text": "Hello",
                    "mediaUrls": [],
                    "mediaKind": "text",
                    "status": "queued",
                    "scheduledFor": None,
                    "timezone": None,
                    "destinations": [],
                    "createdAt": "2026-08-31T00:00:00Z",
                    "updatedAt": "2026-08-31T00:00:00Z",
                }
            },
        )

    api = PostsApi(_client(handler))
    response = await api.create_post(
        create_post_body={
            "text": "Hello",
            "mediaKind": "text",
            "destinations": [{"accountId": "c1"}],
        }
    )
    assert str(response.post.id) == "1699f415-7fb6-43f4-9d2a-c447491f32a8"
    assert seen["url"].endswith("/v1/posts")
    assert seen["api_key"] == "op_test"
    assert seen["body"]["destinations"] == [{"accountId": "c1"}]


@pytest.mark.asyncio
async def test_undo_retweet_sends_post_query():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["method"] = request.method
        return httpx.Response(
            200,
            json={
                "postId": "p1",
                "destinationId": "d1",
                "platform": "x",
                "retweeted": False,
            },
        )

    api = EngagementApi(_client(handler))
    await api.undo_retweet(post="p1")
    assert "/v1/retweets" in seen["url"]
    assert "post=p1" in seen["url"]
    assert seen["method"] == "DELETE"


@pytest.mark.asyncio
async def test_get_media_presigned_url_posts_filename_and_type():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["method"] = request.method
        seen["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "uploadUrl": "https://cdn.example.com/upload?sig=1",
                "publicUrl": "https://cdn.example.com/temp/a.png",
                "key": "temp/a.png",
                "expiresIn": 3600,
            },
        )

    api = MediaApi(_client(handler))
    response = await api.get_media_presigned_url(
        presign_media_body={"filename": "a.png", "contentType": "image/png"}
    )
    assert "/v1/media/presign" in seen["url"]
    assert seen["method"] == "POST"
    assert seen["body"] == {"filename": "a.png", "contentType": "image/png"}
    assert str(response.public_url) == "https://cdn.example.com/temp/a.png"
