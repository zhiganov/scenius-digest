from lib import config


def test_public_communities_always_visible():
    groups = {"7": {"name": "Pub", "visibility": "public"}, "9": {"name": "NoVis"}}
    assert set(config.visible_groups(groups, set())) == {"7", "9"}


def test_private_hidden_without_membership():
    groups = {"7": {"name": "Priv", "visibility": "private"}}
    assert config.visible_groups(groups, set()) == {}


def test_private_visible_with_membership():
    groups = {"7": {"name": "Priv", "visibility": "private"}, "8": {"name": "Pub", "visibility": "public"}}
    assert set(config.visible_groups(groups, {"7"})) == {"7", "8"}


def test_member_ids_matched_as_strings():
    groups = {"7": {"visibility": "private"}}
    assert set(config.visible_groups(groups, {"7"})) == {"7"}
    assert config.visible_groups(groups, {"999"}) == {}


def test_none_member_ids_treated_as_empty():
    groups = {"7": {"visibility": "private"}, "8": {"visibility": "public"}}
    assert set(config.visible_groups(groups)) == {"8"}
