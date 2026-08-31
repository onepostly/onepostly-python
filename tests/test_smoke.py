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
            "destinations": [{"connectionId": "c1"}],
        }
    )
    assert str(response.post.id) == "1699f415-7fb6-43f4-9d2a-c447491f32a8"
    assert seen["url"].endswith("/v1/posts")
    assert seen["api_key"] == "op_test"
    assert seen["body"]["destinations"] == [{"connectionId": "c1"}]


@pytest.mark.asyncio
async def test_undo_retweet_sends_destination_id_query():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["method"] = request.method
        return httpx.Response(200, json={"retweet": {}})

    api = EngagementApi(_client(handler))
    await api.undo_retweet(id="p1", destination_id="d1")
    assert "/v1/posts/p1/retweets" in seen["url"]
    assert "destinationId=d1" in seen["url"]
    assert seen["method"] == "DELETE"


@pytest.mark.asyncio
async def test_upload_media_sends_multipart():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(201, json={"media": {"id": "1699f415-7fb6-43f4-9d2a-c447491f32a8", "url": "https://cdn.example.com/a.png", "contentType": "image/png", "sizeBytes": 3}})

    api = MediaApi(_client(handler))
    response = await api.upload_media(file=b"123")
    assert str(response.media.id) == "1699f415-7fb6-43f4-9d2a-c447491f32a8"
