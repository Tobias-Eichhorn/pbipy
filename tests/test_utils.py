from pathlib import Path
import pytest
import requests
import responses
from requests.exceptions import HTTPError
from responses import matchers

from pbipy import utils
from pbipy.groups import Group
from pbipy.reports import Report

# TODO: Tests for request_mixin.delete()
# TODO: Tests for request_mixin.get()


def test_to_snake_case():
    assert (utils.to_snake_case("FluffyWuffy")) == "fluffy_wuffy"
    assert (utils.to_snake_case("webURL")) == "web_url"
    assert utils.to_snake_case("AyeBeeCee") == "aye_bee_cee"


def test_to_camel_case():
    assert (
        utils.to_camel_case("dataset_user_access_right")
    ) == "datasetUserAccessRight"
    assert (utils.to_camel_case("identifier")) == "identifier"
    assert (utils.to_camel_case("principal_type")) == "principalType"


def test_remove_no_values():
    test_d = {
        "queries": [
            {
                "query": "EVALUATE VALUES(MyTable)",
            },
        ],
        "serializerSettings": {"includeNulls": None},
        "impersonatedUserName": "someuser@mycompany.com",
    }

    expected_d = {
        "queries": [
            {
                "query": "EVALUATE VALUES(MyTable)",
            },
        ],
        "impersonatedUserName": "someuser@mycompany.com",
    }

    assert utils.remove_no_values(test_d) == expected_d


def test_file_path_from_components():
    expected_path = Path("sample_report.pbix")

    path = utils.file_path_from_components(
        file_name="sample_report",
        extension="pbix",
    )

    assert path == expected_path
    assert isinstance(path, Path)


def test_file_path_from_components_path_object():
    expected_path = Path("C:\sample_dir\sample_report.pbix")

    directory = Path("C:\sample_dir")
    path = utils.file_path_from_components(
        file_name="sample_report",
        directory=directory,
        extension="pbix",
    )

    assert path == expected_path
    assert isinstance(path, Path)


def test_file_path_from_components_str_directory():
    expected_path = Path("C:\sample_dir\sample_report.pbix")

    path = utils.file_path_from_components(
        file_name="sample_report",
        directory="C:\sample_dir",
        extension="pbix",
    )

    assert path == expected_path
    assert isinstance(path, Path)


def test_file_path_from_components_dot_ext():
    expected_path = Path("C:\sample_dir\sample_report.pbix")

    path = utils.file_path_from_components(
        file_name="sample_report",
        directory="C:\sample_dir",
        extension=".pbix",
    )

    assert path == expected_path
    assert isinstance(path, Path)


def test_to_identifier():
    assert utils.to_identifier("$type") == "type"
    assert utils.to_identifier("pbi:mashup") == "pbi_mashup"
    assert utils.to_identifier("ppdf:outputFileFormat") == "ppdf_outputFileFormat"


@pytest.fixture
def request_mixin():
    return utils.RequestsMixin()


@pytest.fixture
def session():
    return requests.Session()


# TODO: Add test for post_raw()


@responses.activate
def test_request_mixin_post(request_mixin, session):
    json_params = {
        "identifier": "john@contoso.com",
        "principalType": "User",
        "datasetUserAccessRight": "Read",
    }

    responses.post(
        "https://api.powerbi.com/v1.0/myorg/datasets/cfafbeb1-8037-4d0c-896e-a46fb27ff229/users",
        match=[matchers.json_params_matcher(json_params)],
    )

    resource = "https://api.powerbi.com/v1.0/myorg/datasets/cfafbeb1-8037-4d0c-896e-a46fb27ff229/users"
    payload = {
        "identifier": "john@contoso.com",
        "principalType": "User",
        "datasetUserAccessRight": "Read",
    }

    request_mixin.post(resource, session, payload)


@responses.activate
def test_request_mixin_post_raises(request_mixin, session):
    json_params = {
        "identifier": "john@contoso.com",
        "principalType": "User",
        "datasetUserAccessRight": "Read",
    }

    responses.post(
        "https://api.powerbi.com/v1.0/myorg/datasets/cfafbeb1-8037-4d0c-896e-a46fb27ff229/users",
        match=[matchers.json_params_matcher(json_params)],
        body="{}",
        status=400,
    )

    resource = "https://api.powerbi.com/v1.0/myorg/datasets/cfafbeb1-8037-4d0c-896e-a46fb27ff229/users"
    payload = {
        "identifier": "john@contoso.com",
        "principalType": "User",
        "datasetUserAccessRight": "Read",
    }

    with pytest.raises(HTTPError):
        request_mixin.post(resource, session, payload)


@pytest.fixture
def response_body_single_object():
    return """
    {
        "id": "f089354e-8366-4e18-aea3-4cb4a3a50b48",
        "description": "The finance app",
        "name": "Finance",
        "publishedBy": "Bill",
        "lastUpdate": "2019-01-13T09:46:53.094+02:00"
    }
    """


@pytest.fixture
def response_body_multiple_objects():
    return """
    {
        "value": [
            {
            "id": "f089354e-8366-4e18-aea3-4cb4a3a50b48",
            "isReadOnly": false,
            "isOnDedicatedCapacity": false,
            "name": "sample group"
            },
            {
            "id": "3d9b93c6-7b6d-4801-a491-1738910904fd",
            "isReadOnly": false,
            "isOnDedicatedCapacity": false,
            "name": "marketing group"
            },
            {
            "id": "a2f89923-421a-464e-bf4c-25eab39bb09f",
            "isReadOnly": false,
            "isOnDedicatedCapacity": false,
            "name": "contoso",
            "dataflowStorageId": "d692ae06-708c-485e-9987-06ff0fbdbb1f"
            }
        ]
    }
    """


@responses.activate
def test_request_mixin_get_raw_single_object(
    request_mixin,
    session,
    response_body_single_object,
):
    responses.get(
        "https://api.powerbi.com/v1.0/myorg/apps/f089354e-8366-4e18-aea3-4cb4a3a50b48",
        body=response_body_single_object,
    )

    resource = (
        "https://api.powerbi.com/v1.0/myorg/apps/f089354e-8366-4e18-aea3-4cb4a3a50b48"
    )
    raw = request_mixin.get_raw(resource, session)

    assert "id" in raw
    assert "description" in raw
    assert "name" in raw
    assert "publishedBy" in raw
    assert "lastUpdate" in raw


@responses.activate
def test_request_mixin_get_raw_single_object(
    request_mixin,
    session,
    response_body_multiple_objects,
):
    responses.get(
        "https://api.powerbi.com/v1.0/myorg/apps/f089354e-8366-4e18-aea3-4cb4a3a50b48",
        body=response_body_multiple_objects,
    )

    resource = (
        "https://api.powerbi.com/v1.0/myorg/apps/f089354e-8366-4e18-aea3-4cb4a3a50b48"
    )
    raw = request_mixin.get_raw(resource, session)

    assert isinstance(raw, list)


@responses.activate
def test_request_mixin_get_raw_raises(
    request_mixin,
    session,
):
    responses.get(
        "https://api.powerbi.com/v1.0/myorg/apps/f089354e-8366-4e18-aea3-4cb4a3a50b48",
        body="{}",
        status=404,
    )

    resource = (
        "https://api.powerbi.com/v1.0/myorg/apps/f089354e-8366-4e18-aea3-4cb4a3a50b48"
    )

    with pytest.raises(HTTPError):
        request_mixin.get_raw(resource, session)


@responses.activate
def test_request_mixin_put(request_mixin, session):
    json_params = {
        "identifier": "john@contoso.com",
        "principalType": "User",
        "datasetUserAccessRight": "Read",
    }

    responses.put(
        "https://api.powerbi.com/v1.0/myorg/datasets/cfafbeb1-8037-4d0c-896e-a46fb27ff229/users",
        match=[matchers.json_params_matcher(json_params)],
    )

    resource = "https://api.powerbi.com/v1.0/myorg/datasets/cfafbeb1-8037-4d0c-896e-a46fb27ff229/users"
    payload = {
        "identifier": "john@contoso.com",
        "principalType": "User",
        "datasetUserAccessRight": "Read",
    }

    request_mixin.put(resource, session, payload)


@responses.activate
def test_request_mixin_put_raises(request_mixin, session):
    json_params = {
        "identifier": "john@contoso.com",
        "principalType": "User",
        "datasetUserAccessRight": "Read",
    }

    responses.put(
        "https://api.powerbi.com/v1.0/myorg/datasets/cfafbeb1-8037-4d0c-896e-a46fb27ff229/users",
        match=[matchers.json_params_matcher(json_params)],
        body="{}",
        status=400,
    )

    resource = "https://api.powerbi.com/v1.0/myorg/datasets/cfafbeb1-8037-4d0c-896e-a46fb27ff229/users"
    payload = {
        "identifier": "john@contoso.com",
        "principalType": "User",
        "datasetUserAccessRight": "Read",
    }

    with pytest.raises(HTTPError):
        request_mixin.put(resource, session, payload)


@responses.activate
def test_request_mixin_patch(request_mixin, session):
    json_params = {
        "targetStorageMode": "PremiumFiles",
    }

    responses.patch(
        "https://api.powerbi.com/v1.0/myorg/datasets/cfafbeb1-8037-4d0c-896e-a46fb27ff229",
        match=[
            matchers.json_params_matcher(json_params),
        ],
    )

    resource = "https://api.powerbi.com/v1.0/myorg/datasets/cfafbeb1-8037-4d0c-896e-a46fb27ff229"
    payload = {
        "targetStorageMode": "PremiumFiles",
    }

    request_mixin.patch(resource, session, payload)


@responses.activate
def test_request_mixin_patch_raises(request_mixin, session):
    json_params = {
        "targetStorageMode": "PremiumFiles",
    }

    responses.patch(
        "https://api.powerbi.com/v1.0/myorg/datasets/cfafbeb1-8037-4d0c-896e-a46fb27ff229",
        match=[
            matchers.json_params_matcher(json_params),
        ],
        body="{}",
        status=400,
    )

    resource = "https://api.powerbi.com/v1.0/myorg/datasets/cfafbeb1-8037-4d0c-896e-a46fb27ff229"
    payload = {
        "targetStorageMode": "PremiumFiles",
    }

    with pytest.raises(HTTPError):
        request_mixin.patch(resource, session, payload)


def test_build_url():
    path_format = "/reports/{}/datasources"

    id = "cfafbeb1-8037-4d0c-896e-a46fb27ff228"

    path = utils.build_path(path_format, id)
    expected_path = "/reports/cfafbeb1-8037-4d0c-896e-a46fb27ff228/datasources"

    assert expected_path == path


def test_build_url_with_obj():
    path_format = "/reports/{}/datasources"

    id = Report(
        id="cfafbeb1-8037-4d0c-896e-a46fb27ff228",
        session=requests.Session(),
    )

    path = utils.build_path(path_format, id)
    expected_path = "/reports/cfafbeb1-8037-4d0c-896e-a46fb27ff228/datasources"

    assert expected_path == path


def test_build_url_with_multiple_obj():
    path_format = "/groups/{}/reports/{}/datasources"

    report = Report(
        id="cfafbeb1-8037-4d0c-896e-a46fb27ff229",
        session=requests.Session(),
    )

    group = Group(
        id="f089354e-8366-4e18-aea3-4cb4a3a50b48",
        session=requests.Session(),
    )

    path = utils.build_path(path_format, group, report)
    expected_path = "/groups/f089354e-8366-4e18-aea3-4cb4a3a50b48/reports/cfafbeb1-8037-4d0c-896e-a46fb27ff229/datasources"

    assert expected_path == path
