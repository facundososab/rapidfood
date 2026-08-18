def test_canonical_conversation_packages_import_without_apps_layout():
    import importlib

    module = importlib.import_module("modules.conversation")
    assert module.__name__ == "modules.conversation"

    assert importlib.import_module("modules.conversation.domain")
    assert importlib.import_module("modules.conversation.application")
    assert importlib.import_module("modules.conversation.infrastructure")
    assert importlib.import_module("modules.conversation.configuration")


def test_django_settings_and_conversation_urls_are_canonical():
    import os

    from django.conf import settings
    from django.urls import resolve

    assert settings.ROOT_URLCONF == "config.urls"
    assert os.environ["DJANGO_SETTINGS_MODULE"] == "config.settings"

    match = resolve("/conversation/webhook/")
    assert match.url_name == "conversation-webhook"
