"""Offline setup guide and copyable AI client configuration inside Anki."""

from pathlib import Path
from aqt import mw
from aqt.qt import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QTextBrowser,
    QTextCursor,
    QVBoxLayout,
    QWidget,
)
from .bridge import check_connection, connection_error
from .connection import configuration_text, python_candidates, codex_configuration, tunnel_configuration


class SetupDialog(QDialog):
    def __init__(self, runtime, parent=None, *, start_tab=0):
        super().__init__(parent)
        self.runtime = runtime
        self.setWindowTitle("Anki MCP – Einrichtung & Hilfe")
        self.resize(900, 700)
        self.setMinimumSize(600, 450)
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        help_page = QWidget()
        help_layout = QVBoxLayout(help_page)
        self.sections = QComboBox()
        self.sections.setAccessibleName("Schnellzugriff auf die Einrichtungsanleitung")
        for label, heading in [
            ("Start und Installation", "Anki MCP einrichten"),
            ("KI verbinden: Claude Desktop auf Windows", "Claude Desktop auf Windows"),
            ("KI verbinden: Claude Desktop auf macOS", "Claude Desktop auf macOS"),
            ("KI verbinden: Codex oder Cursor", "Codex, Cursor und andere lokale MCP-Clients"),
            ("ChatGPT: Secure MCP Tunnel einrichten", "ChatGPT im Browser oder als App"),
            ("Verbindung testen", "5. Verbindung prüfen"),
            ("Fehler beheben", "Fehler beheben"),
        ]:
            self.sections.addItem(label, heading)
        help_layout.addWidget(self.sections)
        self.help_browser = QTextBrowser()
        self.help_browser.setOpenExternalLinks(True)
        self.help_browser.setMarkdown((Path(__file__).with_name("setup_help.md")).read_text(encoding="utf-8"))
        help_layout.addWidget(self.help_browser, 1)
        self.sections.currentIndexChanged.connect(self.jump_to_section)
        self.tabs.addTab(help_page, "Einrichtung: Windows und Mac")
        connection = QWidget()
        form_layout = QVBoxLayout(connection)
        self.status = QLabel(self.status_text())
        self.status.setWordWrap(True)
        form_layout.addWidget(self.status)
        form = QFormLayout()
        self.method = QComboBox()
        self.method.addItem("stdio – z. B. Claude Desktop", "stdio")
        self.method.addItem("Streamable HTTP – Client mit Header-Unterstützung", "http")
        self.method.addItem("Codex – lokale stdio-Verbindung (TOML)", "codex")
        self.method.addItem("ChatGPT – Secure MCP Tunnel (YAML; zusätzliche Einrichtung)", "chatgpt")
        form.addRow("KI / Verbindungsart:", self.method)
        candidates = python_candidates()
        self.python_path = QLineEdit(candidates[0] if candidates else "")
        self.python_path.setPlaceholderText("Absoluter Pfad zu Python 3.10 oder neuer")
        self.python_path.setAccessibleName("Python-Interpreter für die stdio-Verbindung")
        python_row = QHBoxLayout()
        python_row.addWidget(self.python_path)
        self.browse = QPushButton("Auswählen…")
        self.browse.clicked.connect(self.choose_python)
        python_row.addWidget(self.browse)
        form.addRow("Python für stdio:", python_row)
        self.tunnel_id = QLineEdit()
        self.tunnel_id.setPlaceholderText("Tunnel-ID aus OpenAI Platform; keine API-Schlüssel hier eintragen")
        form.addRow("ChatGPT-Tunnel-ID:", self.tunnel_id)
        form_layout.addLayout(form)
        self.note = QLabel(
            "Konfiguration in die MCP-Einstellungen deines KI-Clients übernehmen. Bestehende Server-Einträge beibehalten. "
            "HTTP enthält einen Zugangstoken; nur lokal speichern. Der Python-Pfad wird hier nicht auf seine Version geprüft."
        )
        self.note.setWordWrap(True)
        form_layout.addWidget(self.note)
        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setAccessibleName("MCP-Konfiguration zum Kopieren")
        form_layout.addWidget(self.preview, 1)
        buttons = QHBoxLayout()
        self.copy = QPushButton("Konfiguration kopieren")
        self.copy.clicked.connect(self.copy_configuration)
        buttons.addWidget(self.copy)
        self.check = QPushButton("Verbindung prüfen")
        self.check.clicked.connect(self.check_server)
        buttons.addWidget(self.check)
        form_layout.addLayout(buttons)
        self.result = QLabel("Prüft Anki und sein geöffnetes Profil, ohne Karten zu ändern. Anschließend auch aus der KI heraus testen.")
        self.result.setWordWrap(True)
        form_layout.addWidget(self.result)
        self.tabs.addTab(connection, "Verbindung")
        self.usage_browser = QTextBrowser()
        self.usage_browser.setMarkdown(Path(__file__).with_name("usage_help.md").read_text(encoding="utf-8"))
        self.tabs.addTab(self.usage_browser, "KI-Funktionen")
        close = QPushButton("Schließen")
        close.clicked.connect(self.accept)
        layout.addWidget(close)
        self.method.currentIndexChanged.connect(self.refresh_configuration)
        self.python_path.textChanged.connect(self.refresh_configuration)
        self.tunnel_id.textChanged.connect(self.refresh_configuration)
        self.refresh_configuration()
        self.tabs.setCurrentIndex(start_tab)

    def jump_to_section(self, *_args):
        cursor = self.help_browser.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self.help_browser.setTextCursor(cursor)
        self.help_browser.find(self.sections.currentData())

    def status_text(self):
        if self.runtime.server:
            mode = "Nur Lesen" if self.runtime.config.get("read_only", False) else "Lesen und Schreiben"
            return f"Anki MCP läuft auf 127.0.0.1:{self.runtime.server.server_port} · {mode}. Anki mit geöffnetem Profil laufen lassen."
        return "Anki MCP ist gestoppt. " + (self.runtime.error or "Profil öffnen und Add-on-Konfiguration prüfen.")

    def choose_python(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Python 3.10 oder neuer auswählen", self.python_path.text())
        if filename:
            self.python_path.setText(filename)

    def refresh_configuration(self, *_args):
        kind = self.method.currentData()
        stdio = kind in ("stdio", "codex")
        self.tunnel_id.setEnabled(kind == "chatgpt")
        self.python_path.setEnabled(stdio)
        self.browse.setEnabled(stdio)
        active = self.runtime.server is not None
        self.copy.setEnabled(active and (not stdio or bool(self.python_path.text().strip())))
        self.check.setEnabled(active)
        if not active:
            self.preview.setPlainText("Zuerst ein Anki-Profil öffnen und den Server starten. Die Anleitung ist auch offline verfügbar.")
            return
        if kind == "codex":
            self.preview.setPlainText(
                codex_configuration(self.runtime.root, self.runtime.server.server_port, self.python_path.text().strip())
            )
            self.note.setText(
                "Diesen TOML-Abschnitt in Codex config.toml ergänzen. Bestehende Einträge beibehalten. "
                "Codex muss lokal laufen; der Python-Pfad muss zu Python 3.10+ gehören."
            )
            return
        if kind == "chatgpt":
            self.preview.setPlainText(
                tunnel_configuration(self.runtime.server.server_port, self.runtime.config["token"], self.tunnel_id.text().strip())
            )
            self.note.setText(
                "Zusätzlicher OpenAI-Tunnel und Kontoberechtigungen erforderlich. YAML lokal als anki-tunnel.yaml speichern; "
                "enthält deinen Anki-Token. Der Test unten prüft nur Anki, nicht ChatGPT oder den Tunnel. Anleitung zuerst lesen."
            )
            self.copy.setEnabled(bool(self.tunnel_id.text().strip()))
            return
        self.note.setText(
            "Konfiguration in die MCP-Einstellungen des KI-Clients übernehmen. Bestehende Einträge beibehalten. "
            "HTTP enthält einen Zugangstoken. Der Python-Pfad wird nicht auf seine Version geprüft."
        )
        text = configuration_text(
            self.method.currentData(),
            self.runtime.root,
            self.runtime.server.server_port,
            self.runtime.config["token"],
            self.python_path.text().strip(),
        )
        self.preview.setPlainText(text)

    def copy_configuration(self):
        QApplication.clipboard().setText(self.preview.toPlainText())
        if self.method.currentData() == "chatgpt":
            self.result.setText(
                "Tunnel-Konfiguration kopiert. Lokal als anki-tunnel.yaml speichern und den Schritten in der ChatGPT-Anleitung folgen."
            )
        else:
            self.result.setText("Konfiguration kopiert. Im KI-Client ergänzen und den Client anschließend vollständig neu starten.")

    def check_server(self):
        if not self.runtime.server:
            self.result.setText(self.status_text())
            return
        self.check.setEnabled(False)
        self.result.setText("Verbindung wird geprüft…")
        # Capture the profile generation so a stale result is never shown as a new profile's status.
        generation = self.runtime.generation
        url = f"http://127.0.0.1:{self.runtime.server.server_port}/mcp"
        token = self.runtime.config["token"]

        def finished(future):
            # The callback retains the dialog while the check is in flight.
            self.check.setEnabled(self.runtime.server is not None)
            if generation != self.runtime.generation:
                self.result.setText("Profil wurde gewechselt. Verbindung für das aktuelle Profil erneut prüfen.")
                return
            try:
                report = future.result()
                mode = "Nur Lesen" if report["read_only"] else "Lesen und Schreiben"
                self.result.setText(
                    f"Verbindung erfolgreich: {report['tool_count']} MCP-Werkzeuge, "
                    f"{report['notes']} Notizen und {report['cards']} Karten. {mode}. "
                    "Jetzt die KI bitten: Lies meine Decknamen und ändere nichts."
                )
            except Exception as exc:
                self.result.setText(connection_error(exc))

        mw.taskman.run_in_background(lambda: check_connection(url, token), on_done=finished, uses_collection=False)
