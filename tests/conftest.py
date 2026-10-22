import pytest
from anki.collection import Collection
from anki.lang import set_lang

from addon.api import Service

set_lang("en")


@pytest.fixture
def service(tmp_path):
    col = Collection(str(tmp_path / "collection.anki2"))
    svc = Service(col, tmp_path / "user_files" / "transfers")
    yield svc
    col.close()


@pytest.fixture
def basic(service):
    return service.col.models.by_name("Basic")["id"]


@pytest.fixture
def note(service, basic):
    return service.execute(
        "add_notes",
        {
            "notes": [
                {
                    "deck_id": 1,
                    "notetype_id": basic,
                    "fields": {"Front": "Welcher Nerv innerviert das Zwerchfell?", "Back": "N. phrenicus (C3–C5)"},
                    "tags": ["Medizin::Anatomie", "prüfen"],
                }
            ]
        },
    )[0]


@pytest.fixture(scope="session")
def qt_app():
    pytest.importorskip("aqt")
    from aqt.qt import QApplication

    app = QApplication.instance() or QApplication([])
    yield app
