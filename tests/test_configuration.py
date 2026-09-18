# Configuration tests: the shared Configuration is the single source of auth
# and base-path for every API class, so its resolution rules are a public
# contract (documented in the README quick start).
from onepostly import ApiClient, Configuration
from onepostly.api.posts_api import PostsApi
from onepostly.api.webhooks_api import WebhooksApi


def test_default_host_is_production():
    config = Configuration()
    assert config.host == "https://api.onepostly.com"


def test_host_override_for_tests_and_gateways():
    config = Configuration(host="http://127.0.0.1:8787")
    assert config.host == "http://127.0.0.1:8787"


def _auth_headers(config: Configuration) -> dict:
    """The headers a configured auth form puts on the wire."""
    return {
        setting["key"]: setting["value"]
        for setting in config.auth_settings().values()
    }


def test_api_key_is_kept_under_the_spec_security_scheme_name():
    config = Configuration(host="https://api.onepostly.com")
    config.api_key["ApiKey"] = "op_test"
    assert config.api_key["ApiKey"] == "op_test"
    assert config.get_api_key_with_prefix("ApiKey") == "op_test"


def test_api_key_resolves_to_the_x_api_key_header():
    config = Configuration(host="https://api.onepostly.com")
    config.api_key["ApiKey"] = "op_test"
    assert _auth_headers(config) == {"x-api-key": "op_test"}


def test_access_token_resolves_to_a_bearer_authorization_header():
    config = Configuration(host="https://api.onepostly.com", access_token="op_test")
    assert _auth_headers(config) == {"Authorization": "Bearer op_test"}


def test_one_configuration_safely_backs_multiple_api_classes():
    config = Configuration(host="https://api.onepostly.com")
    config.api_key["ApiKey"] = "op_shared"

    posts = PostsApi(ApiClient(configuration=config))
    webhooks = WebhooksApi(ApiClient(configuration=config))

    assert posts.api_client.configuration is config
    assert webhooks.api_client.configuration is config
