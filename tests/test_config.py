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


def test_manual_events_url_derived_from_ca_config_url(monkeypatch):
    monkeypatch.setattr(config, "CA_CONFIG_URL", "https://ca.example.com/api/config")
    assert config.manual_events_url() == "https://ca.example.com/api/events/manual"


def test_manual_events_url_none_when_ca_config_url_unset(monkeypatch):
    monkeypatch.setattr(config, "CA_CONFIG_URL", None)
    assert config.manual_events_url() is None


def test_event_source_keeps_community_admin_visibility(monkeypatch):
    # A private Community Admin community that also has an event source must stay
    # private: the event source adds feeds, it does not replace the community.
    monkeypatch.setattr(config, "fetch_config", lambda: {
        "pxxi": {"name": "Private group", "visibility": "private", "city": None},
    })
    monkeypatch.setattr(config, "EVENT_SOURCES", {
        "pxxi": {"name": "Calendar name", "city": None, "event_apis": [{"type": "luma", "url": "u"}]},
    })
    merged = config.get_all_event_groups()
    assert merged["pxxi"]["visibility"] == "private"
    assert merged["pxxi"]["name"] == "Private group"
    assert merged["pxxi"]["event_apis"] == [{"type": "luma", "url": "u"}]
    assert config.visible_groups(merged, set()) == {}
    assert set(config.visible_groups(merged, {"pxxi"})) == {"pxxi"}


def test_event_source_without_community_admin_entry_is_unchanged(monkeypatch):
    monkeypatch.setattr(config, "fetch_config", lambda: {})
    monkeypatch.setattr(config, "EVENT_SOURCES", {
        "metagov": {"name": "Metagov", "city": None, "event_apis": [{"type": "luma"}]},
    })
    assert config.get_all_event_groups() == {
        "metagov": {"name": "Metagov", "city": None, "event_apis": [{"type": "luma"}]},
    }


def test_event_source_fills_fields_community_admin_leaves_empty(monkeypatch):
    monkeypatch.setattr(config, "fetch_config", lambda: {
        "x": {"name": "X", "visibility": "public", "city": None},
    })
    monkeypatch.setattr(config, "EVENT_SOURCES", {"x": {"city": "london", "event_apis": []}})
    assert config.get_all_event_groups()["x"]["city"] == "london"


def test_pxxi_luma_source_stays_private_without_community_admin_config(monkeypatch):
    monkeypatch.setattr(config, "fetch_config", lambda: {})

    groups = config.get_all_event_groups()
    pxxi = groups["philanthropic-xxi"]

    assert pxxi["visibility"] == "private"
    assert pxxi["event_apis"] == [{
        "type": "luma",
        "url": "https://luma.com/philanthropic",
        "api_id": "cal-1e5i1ZDFMdNw7z9",
    }]
    assert "philanthropic-xxi" not in config.visible_groups(groups, set())
    assert "philanthropic-xxi" in config.visible_groups(groups, {"philanthropic-xxi"})
