#TODO
# Add real servo controls

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QStackedWidget, QFrame, QSlider
)
from PyQt5.QtCore import QTimer, Qt, pyqtSlot
from PyQt5.QtGui import QImage, QPixmap, QFont
import PyQt5.QtCore as QtCore
import cv2
#import movement
from servo import moveAngle

class CameraWidget(QWidget):
    """A widget that shows a live camera feed."""
    def __init__(self, camera_index: int, servos, parent=None):
        self.servos = servos
        super().__init__(parent)
        self.camera_index = camera_index
        self.cap = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        hbox = QHBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        # ── Title bar ────────────────────────────────────────────────────
        title = QLabel(f"📷  Camera {self.camera_index + 1}  (index {self.camera_index})")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet("color: #e0e0e0; margin-bottom: 8px;")
        layout.addWidget(title)

        # ── Camera preview ────────────────────────────────────────────────────
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setStyleSheet(
            "background-color: #1a1a2e; border: 2px solid #4a4a8a; border-radius: 8px;"
        )
        self.video_label.setText("Camera inactive")
        self.video_label.setFont(QFont("Segoe UI", 12))
        self.video_label.setStyleSheet(
            "background-color: #1a1a2e; border: 2px solid #4a4a8a;"
            "border-radius: 8px; color: #888;"
        )
        layout.addWidget(self.video_label)

        self.status_label = QLabel("⏸  Stopped")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #888; margin-top: 6px;")
        layout.addWidget(self.status_label)

        # ── Movement guide ────────────────────────────────────────────────────
        self.control_label = QLabel("Forward (W)\nBackwards (S)\nLeft(A)\nRight(D)")
        self.control_label.setAlignment(Qt.AlignCenter)
        self.control_label.setFont(QFont("Segoe UI", 12))
        self.control_label.setStyleSheet(
            "margin-top: 30px;"
            "margin-bottom: 30px;"
        )
        hbox.addWidget(self.control_label)

        # ── Servo infos ────────────────────────────────────────────────────
        self.servo_label = QLabel(f"Base: {self.servos['base']}\nNeck: {self.servos['neck']}\nGripper: {self.servos['gripper']}\nTail: {self.servos['tail']}")
        self.servo_label.setAlignment(Qt.AlignCenter)
        self.servo_label.setFont(QFont("Segoe UI", 12))
        self.servo_label.setStyleSheet(
            "margin-top: 30px;"
            "margin-bottom: 30px;"
        )
        hbox.addWidget(self.servo_label)
        layout.addLayout(hbox)

    # ── Camera ────────────────────────────────────────────────────
    def start_camera(self):
        if self.cap is not None:
            return  # already running
        self.cap = cv2.VideoCapture(self.camera_index)
        if self.cap.isOpened():
            self.timer.start(30)  # ~33 fps
            self.status_label.setText("🟢  Active")
            self.status_label.setStyleSheet("color: #4ade80; margin-top: 6px;")
        else:
            self.cap.release()
            self.cap = None
            self.video_label.setText(
                f"⚠  Camera {self.camera_index} not available"
            )
            self.status_label.setText("🔴  Unavailable")
            self.status_label.setStyleSheet("color: #f87171; margin-top: 6px;")

    def stop_camera(self):
        self.timer.stop()
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.video_label.setText("Camera inactive")
        self.video_label.setStyleSheet(
            "background-color: #1a1a2e; border: 2px solid #4a4a8a;"
            "border-radius: 8px; color: #888;"
        )
        self.status_label.setText("⏸  Stopped")
        self.status_label.setStyleSheet("color: #888; margin-top: 6px;")

    @pyqtSlot()
    def update_frame(self):
        if self.cap is None or not self.cap.isOpened():
            return
        ret, frame = self.cap.read()
        if not ret:
            return
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        self.video_label.setPixmap(
            pixmap.scaled(
                self.video_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )

    def closeEvent(self, event):
        self.stop_camera()
        super().closeEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SufniBot v3 | Gondaaa")
        self.setMinimumSize(1000, 850)
        self.setStyleSheet("background-color: #0f0f1a; color: #e0e0e0;")
        self.installEventFilter(self)

        self.servos = {"base": 90, "neck": 90, "gripper": 90, "tail": 90}

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Tab bar ──────────────────────────────────────────────────────────
        tab_bar = QFrame()
        tab_bar.setFixedHeight(54)
        tab_bar.setStyleSheet("background-color: #16213e; border-bottom: 2px solid #4a4a8a;")
        tab_layout = QHBoxLayout(tab_bar)
        tab_layout.setContentsMargins(10, 0, 10, 0)
        tab_layout.setSpacing(6)

        self.tab_buttons = []
        for i in range(3):
            btn = QPushButton(f"  Camera {i + 1}  ")
            btn.setCheckable(True)
            btn.setFixedHeight(38)
            btn.setFont(QFont("Segoe UI", 11))
            btn.setStyleSheet(self._tab_style())
            btn.clicked.connect(lambda checked, idx=i: self.switch_page(idx))
            tab_layout.addWidget(btn)
            self.tab_buttons.append(btn)

        tab_layout.addStretch()
        main_layout.addWidget(tab_bar)

        # ── Stacked pages ────────────────────────────────────────────────────
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background-color: #0f0f1a;")
        main_layout.addWidget(self.stack)

        self.camera_widgets = []
        for i in range(3):
            if i == 0:
                cam = CameraWidget(camera_index=0, servos=self.servos)
                self.camera_widgets.append(cam)
                self.stack.addWidget(cam)   
            elif i == 1:
                cam = CameraWidget(camera_index=2, servos=self.servos)
                self.camera_widgets.append(cam)
                self.stack.addWidget(cam)
            elif i == 2:
                cam = CameraWidget(camera_index=4, servos=self.servos)
                self.camera_widgets.append(cam)
                self.stack.addWidget(cam)

        # Activate first page
        self.switch_page(0)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _tab_style(self):
        return """
            QPushButton {
                background-color: transparent;
                color: #888;
                border: none;
                border-radius: 6px;
                padding: 4px 18px;
            }
            QPushButton:hover {
                background-color: #2a2a5a;
                color: #e0e0e0;
            }
            QPushButton:checked {
                background-color: #4a4a8a;
                color: #ffffff;
                font-weight: bold;
            }
        """

    # ── Label updater ────────────────────────────────────────────────────
    def update_servo_labels(self):
        text = f"Base: {self.servos['base']}\nNeck: {self.servos['neck']}\nGripper: {self.servos['gripper']}\nTail: {self.servos['tail']}"
        for cam in self.camera_widgets:
            cam.servo_label.setText(text)

    # ── Stop cam on page switch ────────────────────────────────────────────────────
    def switch_page(self, index: int):
        current = self.stack.currentIndex()
        if current != index:
            self.camera_widgets[current].stop_camera()

        self.stack.setCurrentIndex(index)
        self.camera_widgets[index].start_camera()

        for i, btn in enumerate(self.tab_buttons):
            btn.setChecked(i == index)

    def closeEvent(self, event):
        for cam in self.camera_widgets:
            cam.stop_camera()
        super().closeEvent(event)

    # ── Keybinds ────────────────────────────────────────────────────
    def eventFilter(self, source, event):
        if event.type() == QtCore.QEvent.KeyPress:
            if event.key() == Qt.Key_W:
                print("Forward")
                #fw()
            elif event.key() == Qt.Key_S:
                print("Backward")
                #bw()
            elif event.key() == Qt.Key_A:
                print("Left")
                #left()
            elif event.key() == Qt.Key_D:
                print("Right")
                #right()
            elif event.key() == Qt.Key_I:
                self.servos["base"] = moveAngle(self.servos["base"], "positive")
                self.update_servo_labels()
                print(f"Base: {self.servos["base"]}")
            elif event.key() == Qt.Key_K:
                self.servos["base"] = moveAngle(self.servos["base"], "negative")
                self.update_servo_labels()
                print(f"Base: {self.servos["base"]}")
        return super().eventFilter(source, event)

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()