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

VALIDATION_ERROR = {
    "error": "Invalid request: accounts must contain at least 1 item.",
    "code": "VALIDATION_ERROR",
    "param": "accounts",
    "requestId": "req_8f2a64c1d3b94e0f9a7c5e2b1d0f3a6c",
}


def _client(status: int, body: dict) -> ApiClient:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, json=body, headers={"content-type": "application/json"})

    config = Configuration(host="https://api.onepostly.com", access_token="op_test")
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
    api_client = _client(status, {"error": "boom", "code": "X"})
    posts = PostsApi(api_client)

    with pytest.raises(expected_exception) as exc_info:
        await posts.get_post(id="pst_1")

    error = exc_info.value
    assert isinstance(error, ApiException)
    assert error.status == status


@pytest.mark.asyncio
async def test_error_body_is_preserved_for_callers():
    api_client = _client(400, VALIDATION_ERROR)
    posts = PostsApi(api_client)

    with pytest.raises(ApiException) as exc_info:
        await posts.create_post(
            create_post_body={
                "text": "Hello",
                "accounts": [{"accountId": "acc_1"}],
            }
        )

    error = exc_info.value
    assert error.status == 400
    assert json.loads(error.body) == VALIDATION_ERROR
