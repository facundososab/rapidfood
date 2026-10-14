"""Product image upload from the panel (file input -> client upload)."""
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client

from panel.services.mock_client import MockRapidfoodClient
from panel.views import products as products_views


class RecordingClient(MockRapidfoodClient):
    def __init__(self):
        super().__init__()
        self.uploads = []

    def upload_product_image(self, product_id, file_data, filename):
        self.uploads.append((product_id, filename, len(file_data)))
        return super().upload_product_image(product_id, file_data, filename)


def _client() -> Client:
    client = Client()
    session = client.session
    session["supabase_access_token"] = "test-token"
    session.save()
    # Signed-cookie sessions are written as a cookie only on a response; push the
    # freshly signed value onto the cookie jar before the request.
    client.cookies[settings.SESSION_COOKIE_NAME] = session.session_key
    return client


def test_creating_a_product_uploads_the_selected_image(monkeypatch):
    client = RecordingClient()
    monkeypatch.setattr(products_views, "get_client", lambda: client)
    category_id = client.list_categories()[0].id

    upload = SimpleUploadedFile(
        "foto.png", b"\x89PNG\r\n\x1a\n-fake-bytes", content_type="image/png"
    )
    response = _client().post(
        "/productos/guardar/",
        {
            "name": "Burger con foto",
            "description": "rica",
            "category_id": category_id,
            "single_price": "1000",
            "image": upload,
        },
    )

    assert response.status_code in (301, 302)
    assert len(client.uploads) == 1
    _, filename, size = client.uploads[0]
    assert filename == "foto.png"
    assert size > 0


def test_saving_without_an_image_does_not_upload(monkeypatch):
    client = RecordingClient()
    monkeypatch.setattr(products_views, "get_client", lambda: client)
    category_id = client.list_categories()[0].id

    response = _client().post(
        "/productos/guardar/",
        {
            "name": "Sin foto",
            "description": "",
            "category_id": category_id,
            "single_price": "500",
        },
    )

    assert response.status_code in (301, 302)
    assert client.uploads == []
