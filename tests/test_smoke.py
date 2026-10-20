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


POST = {
    "id": "pst_1",
    "groupId": "grp_1",
    "accountId": "acc_1",
    "platform": "linkedin",
    "source": "onepostly",
    "status": "publishing",
    "text": "Hello",
    "mediaKind": "text",
    "media": [],
    "thread": [],
    "scheduledFor": None,
    "timezone": None,
    "options": {},
    "platformPostId": None,
    "url": None,
    "error": None,
    "publishedAt": None,
    "metrics": None,
    "createdAt": "2027-03-15T09:00:00Z",
    "updatedAt": "2027-03-15T09:00:00Z",
}

CREATED_POSTS = {"groupId": "grp_1", "data": [POST]}


def _client(handler, access_token: str | None = "op_test") -> ApiClient:
    config = Configuration(host="https://api.onepostly.com", access_token=access_token)
    api_client = ApiClient(configuration=config)
    api_client.rest_client.pool_manager = httpx.AsyncClient(
        transport=httpx.MockTransport(handler)
    )
    return api_client


@pytest.mark.asyncio
async def test_create_post_sends_body_and_bearer_authorization():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["method"] = request.method
        seen["body"] = json.loads(request.content)
        seen["authorization"] = request.headers.get("authorization")
        return httpx.Response(201, json=CREATED_POSTS)

    api = PostsApi(_client(handler))
    response = await api.create_post(
        create_post_body={
            "text": "Hello",
            "accounts": [{"accountId": "acc_1"}],
        }
    )
    assert response.group_id == "grp_1"
    assert response.data[0].id == "pst_1"
    assert seen["url"].endswith("/v1/posts")
    assert seen["method"] == "POST"
    assert seen["authorization"] == "Bearer op_test"
    assert seen["body"] == {"text": "Hello", "accounts": [{"accountId": "acc_1"}]}


@pytest.mark.asyncio
async def test_no_authorization_without_an_access_token():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["authorization"] = request.headers.get("authorization")
        return httpx.Response(200, json=POST)

    api = PostsApi(_client(handler, access_token=None))
    await api.get_post(id="pst_1")
    assert seen["authorization"] is None


@pytest.mark.asyncio
async def test_unrepost_post_puts_both_path_parameters_in_the_url():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["method"] = request.method
        return httpx.Response(
            200,
            json={
                "postId": "pst_1",
                "accountId": "acc_1",
                "platform": "threads",
                "reposted": False,
                "platformRepostId": None,
            },
        )

    api = EngagementApi(_client(handler))
    response = await api.unrepost_post(id="acc_1", post_id="pst_1")
    assert seen["url"].endswith("/v1/accounts/acc_1/reposts/pst_1")
    assert seen["method"] == "DELETE"
    assert response.reposted is False


@pytest.mark.asyncio
async def test_create_media_posts_the_file_details_and_returns_the_upload_url():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["method"] = request.method
        seen["body"] = json.loads(request.content)
        return httpx.Response(
            201,
            json={
                "id": "med_1",
                "url": "https://cdn.example.com/media/a.png",
                "contentType": "image/png",
                "sizeBytes": None,
                "filename": "a.png",
                "status": "pending",
                "createdAt": "2027-03-15T09:00:00Z",
                "uploadUrl": "https://uploads.example.com/temp/a.png?sig=1",
                "uploadExpiresIn": 3600,
            },
        )

    api = MediaApi(_client(handler))
    response = await api.create_media(
        create_media_body={"filename": "a.png", "contentType": "image/png", "size": 1024}
    )
    assert seen["url"].endswith("/v1/media")
    assert seen["method"] == "POST"
    assert seen["body"] == {"filename": "a.png", "contentType": "image/png", "size": 1024}
    assert response.id == "med_1"
    assert str(response.upload_url) == "https://uploads.example.com/temp/a.png?sig=1"
