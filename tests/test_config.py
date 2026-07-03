from bill_agent.config import Config


def test_accounts_from_ini(tmp_path, monkeypatch):
    ini = tmp_path / "accounts.ini"
    ini.write_text(
        "[gmail]\n"
        "host = imap.gmail.com\n"
        "user = a@b.sk\n"
        "password = x\n"
        "\n"
        "[proton]\n"
        "host = 127.0.0.1\n"
        "port = 1143\n"
        "user = c@proton.me\n"
        "password = y\n"
        "security = starttls\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("ACCOUNTS_FILE", str(ini))
    accounts = Config().accounts()
    assert [a.name for a in accounts] == ["gmail", "proton"]
    assert accounts[0].port == 993 and accounts[0].security == "ssl"
    assert accounts[1].port == 1143 and accounts[1].security == "starttls"


def test_fallback_to_env(tmp_path, monkeypatch):
    monkeypatch.setenv("ACCOUNTS_FILE", str(tmp_path / "missing.ini"))
    monkeypatch.setenv("IMAP_HOST", "imap.webhouse.sk")
    monkeypatch.setenv("IMAP_USER", "info@firma.sk")
    monkeypatch.setenv("IMAP_PASSWORD", "tajne")
    accounts = Config().accounts()
    assert len(accounts) == 1
    assert accounts[0].host == "imap.webhouse.sk"
    assert accounts[0].name == "info@firma.sk"
