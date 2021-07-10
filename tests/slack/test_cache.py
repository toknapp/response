import pytest

from response.core.models import ExternalUser
from response.slack.cache import (
    get_user_profile,
    get_user_profile_by_email,
    update_user_cache,
)
from tests.slack.slack_payloads import (
    users_list_new,
    users_list_page_1,
    users_list_page_2,
    users_list_response,
)


@pytest.mark.django_db
def test_update_cache_from_empty(mock_slack):
    mock_slack.get_paginated_users.return_value = users_list_response

    update_user_cache()

    assert len(ExternalUser.objects.all()) == 2
    cache_user1 = ExternalUser.objects.get(external_id="W012A3CDE")
    assert cache_user1.display_name == "spengler"
    assert cache_user1.full_name == "Egon Spengler"
    assert cache_user1.email == "spengler@ghostbusters.example.com"
    assert cache_user1.deleted
    cache_user2 = ExternalUser.objects.get(external_id="U12345678")
    assert cache_user2.display_name == "Glinda the Fairly Good"
    assert cache_user2.full_name == "Glinda Southgood"
    assert cache_user2.email == "glenda@south.oz.coven"
    assert not cache_user2.deleted


@pytest.mark.django_db
def test_update_cache_excludes_bots(mock_slack):
    mock_slack.get_paginated_users.return_value = users_list_response

    update_user_cache(True)

    assert len(ExternalUser.objects.all()) == 1


@pytest.mark.django_db
def test_update_cache_from_populated(mock_slack):
    mock_slack.get_paginated_users.return_value = users_list_response

    update_user_cache()
    assert len(ExternalUser.objects.all()) == 2

    update_user_cache()
    assert len(ExternalUser.objects.all()) == 2


@pytest.mark.django_db
def test_update_cache_new_user(mock_slack):
    mock_slack.get_paginated_users.side_effect = [users_list_response, users_list_new]

    update_user_cache()
    assert len(ExternalUser.objects.all()) == 2

    update_user_cache()
    assert len(ExternalUser.objects.all()) == 3


@pytest.mark.django_db
def test_update_cache_pagination(mock_slack):
    def get_page(limit=0, cursor=None):
        if not cursor:
            return users_list_page_1
        elif cursor == "page2":
            return users_list_page_2

    mock_slack.get_paginated_users.side_effect = get_page
    update_user_cache()

    users = [user.display_name for user in ExternalUser.objects.all()]

    assert users == ["spengler", "Glinda the Fairly Good"]


@pytest.mark.django_db
def test_get_user_profile_not_in_cache(mock_slack):
    mock_slack.get_user_profile.return_value = {
        "id": "U12345678",
        "name": "spengler",
        "fullname": "Egon Spengler",
        "email": "spengler@ghostbusters.example.com",
        "deleted": True,
    }

    # check cache is empty at start
    assert len(ExternalUser.objects.all()) == 0

    # request a user from cache
    user = get_user_profile("U12345678")

    # check we get back the user from slack
    mock_slack.get_user_profile.assert_called()
    assert user["id"] == "U12345678"

    # check user is now in cache
    assert len(ExternalUser.objects.all()) == 1

    # and that it has the right details populated
    cache_user = ExternalUser.objects.get(external_id="U12345678")
    assert cache_user.display_name == "spengler"
    assert cache_user.full_name == "Egon Spengler"
    assert cache_user.email == "spengler@ghostbusters.example.com"
    assert cache_user.deleted


@pytest.mark.django_db
def test_get_user_profile_in_cache(mock_slack):
    # create cache entry for user
    slack_user = ExternalUser(
        external_id="U12345678",
        display_name="spengler",
        full_name="Egon Spengler",
        email="spengler@ghostbusters.example.com",
        deleted=True,
    )
    slack_user.save()
    assert len(ExternalUser.objects.all()) == 1

    # request a user from cache
    user = get_user_profile("U12345678")

    # check we get back the user from cache (i.e. not call to Slack API)
    mock_slack.get_user_profile.assert_not_called()
    assert user["id"] == "U12345678"
    assert user["name"] == "spengler"
    assert user["fullname"] == "Egon Spengler"
    assert user["email"] == "spengler@ghostbusters.example.com"
    assert user["deleted"]

    # check cache is unchanged
    assert len(ExternalUser.objects.all()) == 1


@pytest.mark.django_db
def test_get_user_profile_by_email_not_in_cache(mock_slack):
    mock_slack.get_user_profile_by_email.return_value = {
        "id": "U12345678",
        "name": "spengler",
        "fullname": "Egon Spengler",
        "email": "spengler@ghostbusters.example.com",
        "deleted": True,
    }

    # check cache is empty at start
    assert len(ExternalUser.objects.all()) == 0

    # request a user from cache
    user = get_user_profile_by_email("spengler@ghostbusters.example.com")

    # check we get back the user from slack
    mock_slack.get_user_profile_by_email.assert_called()
    assert user["id"] == "U12345678"

    # check user is now in cache
    assert len(ExternalUser.objects.all()) == 1

    # and that it has the right details populated
    cache_user = ExternalUser.objects.get(email="spengler@ghostbusters.example.com")
    assert cache_user.display_name == "spengler"
    assert cache_user.full_name == "Egon Spengler"
    assert cache_user.email == "spengler@ghostbusters.example.com"
    assert cache_user.deleted


@pytest.mark.django_db
def test_get_user_profile_by_email_in_cache(mock_slack):
    # create cache entry for user
    slack_user = ExternalUser(
        external_id="U12345678",
        display_name="spengler",
        full_name="Egon Spengler",
        email="spengler@ghostbusters.example.com",
        deleted=True,
    )
    slack_user.save()
    assert len(ExternalUser.objects.all()) == 1

    # request a user from cache
    user = get_user_profile_by_email("spengler@ghostbusters.example.com")

    # check we get back the user from cache (i.e. not call to Slack API)
    mock_slack.get_user_profile_by_email.assert_not_called()
    assert user["id"] == "U12345678"
    assert user["name"] == "spengler"
    assert user["fullname"] == "Egon Spengler"
    assert user["email"] == "spengler@ghostbusters.example.com"
    assert user["deleted"]

    # check cache is unchanged
    assert len(ExternalUser.objects.all()) == 1
