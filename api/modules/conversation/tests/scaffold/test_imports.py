def test_canonical_conversation_packages_import_without_apps_layout():
    import importlib

    module = importlib.import_module("api.modules.conversation")
    assert module.__name__ == "api.modules.conversation"

    assert importlib.import_module("api.modules.conversation.domain")
    assert importlib.import_module("api.modules.conversation.application")
    assert importlib.import_module("api.modules.conversation.infrastructure")
    assert importlib.import_module("api.modules.conversation.configuration")


def test_django_settings_and_conversation_urls_are_canonical():
    from django.conf import settings
    from django.urls import resolve

    assert settings.ROOT_URLCONF == "api.config.urls"
    assert settings.DJANGO_SETTINGS_MODULE == "api.config.settings"

    match = resolve("/conversation/webhook/")
    assert match.url_name == "conversation-webhook"
