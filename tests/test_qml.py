import shutil
import subprocess

import pytest


def test_qmllint(widget_root):
    qmllint = shutil.which("qmllint")
    if not qmllint:
        pytest.skip("qmllint is not installed")
    files = [
        widget_root / "contents/ui/main.qml",
        widget_root / "contents/ui/configGeneral.qml",
        widget_root / "contents/config/config.qml",
    ]
    result = subprocess.run([qmllint, *map(str, files)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr or result.stdout


@pytest.mark.parametrize("height,countdown", [(40, "1h 5m"), (60, "6h 25m"), (80, "167h 59m")])
def test_taskbar_width_fits_text(widget_root, height, countdown, monkeypatch):
    import json

    pytest.importorskip("PySide6.QtGui")
    pytest.importorskip("PySide6.QtQml")
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlComponent, QQmlEngine

    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = QGuiApplication.instance() or QGuiApplication([])
    source = (widget_root / "contents/ui/main.qml").read_text()
    sizing = source.split("readonly property real iconSize:", 1)[1].split("Layout.minimumWidth:", 1)[0]
    panel = source.split("// ── Horizontal panel: claudeai mode text", 1)[1].split(
        "// ── Horizontal panel: API mode text", 1
    )[0]
    panel = panel[panel.index("Column {"):].replace("Kirigami.Theme.disabledTextColor", '"gray"')
    qml = '''import QtQuick
Item {
    id: root
    property bool apiMode: false
    property bool loading: false
    property string errorMsg: ""
    property real sessionPct: 89
    property real weeklyPct: 22
    property string sessionResetsIn: COUNTDOWN
    property string weeklyResetsIn: COUNTDOWN
    property var theme: ({s: "orange", w: "yellow"})
    property real measuredWidth: compact.width
    property real textExtent: Math.max(probePercent.implicitWidth, probeReset.implicitWidth)
    property real iconExtent: compactCanvas.x + compactCanvas.width
    Text { id: probePercent; text: "89%"; font.pixelSize: Math.round(HEIGHT * .32); font.bold: true }
    Text { id: probeReset; text: COUNTDOWN; font.pixelSize: Math.round(HEIGHT * .22) }
    Item {
        id: compact
        property bool vertical: false
        property real h: HEIGHT
        readonly property real iconSize: SIZING
        width: totalW
        height: h
        Item { id: compactCanvas; x: Math.round((compact.h - width) / 2); width: compact.iconSize }
        PANEL
    }
}'''.replace("COUNTDOWN", json.dumps(countdown)).replace("HEIGHT", str(height)).replace("SIZING", sizing).replace("PANEL", panel)
    engine = QQmlEngine()
    component = QQmlComponent(engine)
    component.setData(qml.encode(), QUrl())
    obj = component.create()
    assert obj is not None, [error.toString() for error in component.errors()]
    app.processEvents()
    right_gap = obj.property("measuredWidth") - obj.property("iconExtent") - round(height * .15) - obj.property("textExtent")
    assert round(height * .08) <= right_gap < round(height * .08) + 1
