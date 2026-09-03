# Error-contract tests: the SDK's public error surface must behave exactly as
# documented in the README (ApiException carrying status + raw body, with
# status-family subclasses from the generated exceptions module). These are
# hand-written behavior contracts, not regenerated from the spec.
import json

import httpx
import pytest

from onepostly import ApiClient, Configuration
from onepostly.api.posts_api import PostsApi
from onepostly.exceptions import (
    ApiException,
    BadRequestException,
    ForbiddenException,
    NotFoundException,
    ServiceException,
    UnauthorizedException,
)


def _client(status: int, body: dict) -> ApiClient:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, json=body, headers={"content-type": "application/json"})

    config = Configuration(host="https://api.onepostly.com")
    config.api_key["ApiKeyHeader"] = "op_test"
    api_client = ApiClient(configuration=config)
    api_client.rest_client.pool_manager = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return api_client


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "expected_exception"),
    [
        (400, BadRequestException),
        (401, UnauthorizedException),
        (403, ForbiddenException),
        (404, NotFoundException),
        (500, ServiceException),
    ],
)
async def test_status_families_map_to_dedicated_exceptions(status, expected_exception):
    api_client = _client(status, {"error": {"code": "X", "message": "boom"}})
    posts = PostsApi(api_client)

    with pytest.raises(expected_exception) as exc_info:
        await posts.get_post(id="p1")

    error = exc_info.value
    assert isinstance(error, ApiException)
    assert error.status == status


@pytest.mark.asyncio
async def test_error_body_is_preserved_for_callers():
    body = {"error": {"code": "INSUFFICIENT_WALLET", "message": "Wallet balance too low"}}
    api_client = _client(402, body)
    posts = PostsApi(api_client)

    with pytest.raises(ApiException) as exc_info:
        await posts.create_post(
            create_post_body={
                "text": "Hello",
                "mediaKind": "text",
                "destinations": [{"accountId": "c1"}],
            }
        )

    error = exc_info.value
    assert error.status == 402
    assert json.loads(error.body) == body
