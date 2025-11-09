from scheduler import worker

def test_run_cycle(monkeypatch):
    monkeypatch.setattr(worker, "discover_new_books", lambda driver: 0)
    monkeypatch.setattr(worker, "detect_changes", lambda run_headless=True: [])
    monkeypatch.setattr(worker, "write_reports", lambda changes: "reports/test.json")

    worker.run_cycle()  # Should not raise
