# icons.py

from functools import lru_cache
from pathlib import Path

from PyQt6.QtCore import QByteArray, QRectF, Qt
from PyQt6.QtGui import QGuiApplication, QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer

from theme import theme

# Only the icons listed in scripts/update_icons.py live here.
ICON_DIR = Path(__file__).parent / "icons" / "lucide"

@lru_cache(maxsize=None)
def _svg(name: str) -> bytes:
    path = ICON_DIR / f"{name}.svg"
    if not path.exists():
        raise FileNotFoundError(f"No Lucide icon named {name!r}. Add it to scripts/update_icons.py and run it.")
    return path.read_bytes()

@lru_cache(maxsize=None)
def pixmap(name: str, color: str, size: int = 18) -> QPixmap:
    # Lucide draws with currentColor, so we swap in the color we want before rendering.
    data = _svg(name).replace(b"currentColor", color.encode())
    renderer = QSvgRenderer(QByteArray(data))
    # Render at the screen's pixel ratio (at least 2x) so icons stay sharp.
    screen = QGuiApplication.primaryScreen()
    ratio = max(2.0, screen.devicePixelRatio() if screen is not None else 1.0)
    image = QPixmap(int(size * ratio), int(size * ratio))
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter, QRectF(0, 0, image.width(), image.height()))
    painter.end()
    image.setDevicePixelRatio(ratio)
    return image

def icon(name: str, color: str = "text", checked: str | None = None, size: int = 18) -> QIcon:
    """Make a Lucide icon in a theme color.

    :param color: A theme token (like "muted") or a hex color.
    :param checked: The color for checkable buttons when they're checked.
    """
    def resolve(token: str) -> str:
        return theme.colors.get(token, token)
    result = QIcon()
    result.addPixmap(pixmap(name, resolve(color), size), QIcon.Mode.Normal, QIcon.State.Off)
    result.addPixmap(pixmap(name, resolve(checked or color), size), QIcon.Mode.Normal, QIcon.State.On)
    result.addPixmap(pixmap(name, resolve("border"), size), QIcon.Mode.Disabled, QIcon.State.Off)
    return result

def bind_icon(target, name: str, color: str = "text", checked: str | None = None, size: int = 18):
    """Set an icon on a widget or action and redo it whenever the theme changes."""
    def update():
        try:
            target.setIcon(icon(name, color, checked, size))
        except RuntimeError:
            # The widget was deleted, so stop updating it.
            theme.changed.disconnect(update)
    update()
    theme.changed.connect(update)

__all__ = ["icon", "pixmap", "bind_icon"]
