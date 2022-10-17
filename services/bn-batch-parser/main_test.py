import base64
import json

import mock
import pytest

import main


@pytest.fixture
def client():
    '''Flask application fixture to use in tests.'''
    main.app.testing = True
    return main.app.test_client()


def test_empty_payload(client):
    r = client.post("/", json="")
    assert r.status_code == 400


def test_invalid_payload(client):
    r = client.post("/", json={"nomessage": "invalid"})
    assert r.status_code == 400


def test_invalid_mimetype(client):
    r = client.post("/", json="{ message: true }")
    assert r.status_code == 400


@mock.patch("processor.bn_batch", mock.MagicMock(return_value=204))
def test_minimally_valid_message(client):
    data_json = json.dumps({"name": True, "bucket": True})
    data = base64.b64encode(data_json.encode()).decode()

    r = client.post("/", json={"message": {"data": data}})
    assert r.status_code == 204 or 200
