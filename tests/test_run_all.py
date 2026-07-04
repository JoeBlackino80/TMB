import os
import subprocess
import sys


def test_run_all_iterates_clients(tmp_path):
    # dvaja klienti s prázdnou konfiguráciou — príkaz `list` nepotrebuje prihlásenie
    for name in ("firma-a", "firma-b"):
        d = tmp_path / "clients" / name
        d.mkdir(parents=True)
        (d / ".env").write_text("DB_PATH=bill_agent.db\n")
    # adresár bez .env sa preskočí
    (tmp_path / "clients" / "nie-klient").mkdir()

    result = subprocess.run(
        [sys.executable, "-m", "bill_agent", "run-all", "list",
         "--clients-dir", str(tmp_path / "clients")],
        capture_output=True, text=True,
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    )
    assert result.returncode == 0, result.stderr
    assert "firma-a" in result.stdout and "firma-b" in result.stdout
    assert "nie-klient" not in result.stdout
    assert result.stdout.count("Nezaplatené platby (0)") == 2
    # každý klient má vlastnú databázu vo svojom adresári
    assert (tmp_path / "clients" / "firma-a" / "bill_agent.db").exists()


def test_run_all_missing_dir(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "bill_agent", "run-all",
         "--clients-dir", str(tmp_path / "nic")],
        capture_output=True, text=True,
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    )
    assert result.returncode != 0
    assert "neexistuje" in result.stderr
