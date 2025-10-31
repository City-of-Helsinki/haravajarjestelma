def get(api_client, url, status_code=200):
    return _execute_request(api_client, "get", url, status_code)


def post(api_client, url, data=None, status_code=201):
    return _execute_request(api_client, "post", url, status_code, data)


def put(api_client, url, data=None, status_code=200):
    return _execute_request(api_client, "put", url, status_code, data)


def patch(api_client, url, data=None, status_code=200):
    return _execute_request(api_client, "patch", url, status_code, data)


def delete(api_client, url, status_code=204):
    return _execute_request(api_client, "delete", url, status_code)


def _execute_request(api_client, method, url, status_code, data=None):
    response = getattr(api_client, method)(url, data=data)
    response_data = getattr(response, "data", None)
    assert response.status_code == status_code, (
        f"Expected status code {status_code} but got {response.status_code} with data {response_data}"
    )
    return response_data


def check_translated_field_data_matches_object(data, obj, field_name):
    translations = obj.translations.exclude(**{field_name: ""})
    if translations:
        assert len(data[field_name]) == translations.count()
        for translation in translations:
            assert data[field_name][translation.language_code] == translation.name
    else:
        assert data[field_name] is None


def assert_objects_in_results(objects, results):
    object_ids = [o.id for o in objects]
    result_ids = [r["id"] for r in results]
    assert object_ids == result_ids, (
        f"Expected {object_ids} does not match results {result_ids}"
    )
