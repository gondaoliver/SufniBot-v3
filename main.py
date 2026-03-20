import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QStackedWidget, QFrame
)
from PyQt5.QtCore import QTimer, Qt, pyqtSlot, QPoint
from PyQt5.QtGui import QImage, QPixmap, QFont, QCursor
import PyQt5.QtCore as QtCore
import cv2
from movement import fw, bw, right, left, stop
from servo import moveAngle, setAngle
import pyzbar.pyzbar as pyzbar


class CameraWidget(QWidget):
    """A widget that shows a live camera feed with zoom and pan support."""

    ZOOM_MIN = 1.0
    ZOOM_MAX = 8.0
    ZOOM_STEP = 0.25
    PAN_STEP = 0.05  # fraction of frame per keypress

    def __init__(self, camera_index: int, servos, parent=None):
        self.servos = servos
        super().__init__(parent)
        self.camera_index = camera_index
        self.cap = None
        self._is_running = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.scanned_codes = set()

        # ── Zoom / pan state ──────────────────────────────────────────────────
        self._zoom = 1.0        # current zoom level (1.0 = no zoom)
        self._pan_x = 0.5       # crop centre X as fraction of frame width  [0..1]
        self._pan_y = 0.5       # crop centre Y as fraction of frame height [0..1]
        self._drag_start = None  # QPoint where LMB was pressed
        self._drag_pan_start = None  # (_pan_x, _pan_y) at drag start

        self._build_ui()

    # ─────────────────────────────────────────────────────────────────────────
    # UI construction
    # ─────────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        hbox = QHBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        # ── Title bar ─────────────────────────────────────────────────────────
        title = QLabel(f"📷  Camera {self.camera_index + 1}  (index {self.camera_index})")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet("color: #e0e0e0; margin-bottom: 8px;")
        layout.addWidget(title)

        # ── Camera preview ─────────────────────────────────────────────────────
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setText("Camera inactive")
        self.video_label.setFont(QFont("Segoe UI", 12))
        self.video_label.setStyleSheet(
            "background-color: #1a1a2e; border: 2px solid #4a4a8a;"
            "border-radius: 8px; color: #888;"
        )
        # Enable mouse events for click-and-drag pan
        self.video_label.setMouseTracking(True)
        self.video_label.mousePressEvent   = self._on_mouse_press
        self.video_label.mouseMoveEvent    = self._on_mouse_move
        self.video_label.mouseReleaseEvent = self._on_mouse_release
        self.video_label.wheelEvent        = self._on_wheel
        layout.addWidget(self.video_label)

        # ── Status / zoom row ──────────────────────────────────────────────────
        status_row = QHBoxLayout()

        self.status_label = QLabel("⏸  Stopped")
        self.status_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.status_label.setStyleSheet("color: #888; margin-top: 6px;")
        status_row.addWidget(self.status_label)

        status_row.addStretch()

        self.zoom_label = QLabel(self._zoom_text())
        self.zoom_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.zoom_label.setFont(QFont("Segoe UI", 11))
        self.zoom_label.setStyleSheet("color: #a0c4ff; margin-top: 6px;")
        status_row.addWidget(self.zoom_label)

        layout.addLayout(status_row)

        # ── Zoom buttons ───────────────────────────────────────────────────────
        zoom_btn_row = QHBoxLayout()
        zoom_btn_row.setSpacing(6)

        btn_zoom_in  = QPushButton("🔍+  Zoom In  (+)")
        btn_zoom_out = QPushButton("🔍−  Zoom Out  (−)")
        btn_reset    = QPushButton("⟳  Reset View  (R)")

        for btn in (btn_zoom_in, btn_zoom_out, btn_reset):
            btn.setFixedHeight(32)
            btn.setFont(QFont("Segoe UI", 10))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2a2a5a;
                    color: #c0c0f0;
                    border: 1px solid #4a4a8a;
                    border-radius: 5px;
                    padding: 0 14px;
                }
                QPushButton:hover  { background-color: #3a3a7a; color: #ffffff; }
                QPushButton:pressed { background-color: #4a4a8a; }
            """)

        btn_zoom_in .clicked.connect(lambda: self._zoom_by(+self.ZOOM_STEP))
        btn_zoom_out.clicked.connect(lambda: self._zoom_by(-self.ZOOM_STEP))
        btn_reset   .clicked.connect(self.reset_view)

        zoom_btn_row.addWidget(btn_zoom_in)
        zoom_btn_row.addWidget(btn_zoom_out)
        zoom_btn_row.addWidget(btn_reset)
        zoom_btn_row.addStretch()
        layout.addLayout(zoom_btn_row)

        # ── Bottom info row ────────────────────────────────────────────────────
        self.control_label = QLabel(
            "Forward W\nBackward S\nLeft A\nRight D"
        )
        self.control_label.setAlignment(Qt.AlignCenter)
        self.control_label.setFont(QFont("Segoe UI", 12))
        self.control_label.setStyleSheet("margin-top: 16px; margin-bottom: 16px;")
        hbox.addWidget(self.control_label)

        self.servo_label = QLabel(
            f"Base: {self.servos['base']}\n"
            f"Neck: {self.servos['neck']}\n"
            f"Gripper: {self.servos['gripper']}\n"
            f"Tail: {self.servos['tail']}"
        )
        self.servo_label.setAlignment(Qt.AlignCenter)
        self.servo_label.setFont(QFont("Segoe UI", 12))
        self.servo_label.setStyleSheet("margin-top: 16px; margin-bottom: 16px;")
        hbox.addWidget(self.servo_label)

        layout.addLayout(hbox)

    # ─────────────────────────────────────────────────────────────────────────
    # Camera lifecycle
    # ─────────────────────────────────────────────────────────────────────────

    def start_camera(self):
        if self._is_running:
            return
        self.cap = cv2.VideoCapture(self.camera_index)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        if self.cap.isOpened():
            self._is_running = True
            self.timer.start(30)
            self.status_label.setText("🟢  Active")
            self.status_label.setStyleSheet("color: #4ade80; margin-top: 6px;")
        else:
            self.cap.release()
            self.cap = None
            self.video_label.setText(f"⚠  Camera {self.camera_index} not available")
            self.status_label.setText("🔴  Unavailable")
            self.status_label.setStyleSheet("color: #f87171; margin-top: 6px;")

    def stop_camera(self):
        self._is_running = False
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
        if not self._is_running or self.cap is None or not self.cap.isOpened():
            return
        self.cap.grab()
        ret, frame = self.cap.retrieve()
        if not ret or frame is None:
            return

        # QR / barcode decoding (on full frame before crop)
        decoded_objects = pyzbar.decode(frame)
        for obj in decoded_objects:
            data = obj.data.decode("utf-8")
            if data not in self.scanned_codes:
                self.scanned_codes.add(data)
                with open("codes.txt", "a") as f:
                    f.write(data + "\n")
                print("Scanned:", data)
            cv2.putText(frame, data, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 3)

        # ── Apply zoom + pan crop ─────────────────────────────────────────────
        frame = self._apply_zoom_pan(frame)

        # Display frame
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        qt_image = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
        self.video_label.setPixmap(
            QPixmap.fromImage(qt_image).scaled(
                self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        )

    def closeEvent(self, event):
        self.stop_camera()
        super().closeEvent(event)

    # ─────────────────────────────────────────────────────────────────────────
    # Zoom / Pan helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _zoom_text(self) -> str:
        return f"🔍 {self._zoom:.2f}×"

    def _apply_zoom_pan(self, frame):
        """Return a cropped sub-region of *frame* according to current zoom/pan."""
        if self._zoom <= 1.0:
            return frame

        fh, fw = frame.shape[:2]

        # Size of the crop window in pixels
        crop_w = int(fw / self._zoom)
        crop_h = int(fh / self._zoom)

        # Top-left corner of the crop, clamped so we never go out of bounds
        x0 = int(self._pan_x * fw - crop_w / 2)
        y0 = int(self._pan_y * fh - crop_h / 2)
        x0 = max(0, min(x0, fw - crop_w))
        y0 = max(0, min(y0, fh - crop_h))

        return frame[y0:y0 + crop_h, x0:x0 + crop_w]

    def _clamp_pan(self):
        """Keep _pan_x/_pan_y in the range that keeps the crop inside the frame."""
        if self._zoom <= 1.0:
            self._pan_x = 0.5
            self._pan_y = 0.5
            return
        half = 0.5 / self._zoom          # half-crop as fraction
        self._pan_x = max(half, min(1.0 - half, self._pan_x))
        self._pan_y = max(half, min(1.0 - half, self._pan_y))

    def _zoom_by(self, delta: float):
        self._zoom = round(max(self.ZOOM_MIN, min(self.ZOOM_MAX, self._zoom + delta)), 4)
        self._clamp_pan()
        self.zoom_label.setText(self._zoom_text())

    def zoom_in(self):
        self._zoom_by(+self.ZOOM_STEP)

    def zoom_out(self):
        self._zoom_by(-self.ZOOM_STEP)

    def reset_view(self):
        self._zoom = 1.0
        self._pan_x = 0.5
        self._pan_y = 0.5
        self.zoom_label.setText(self._zoom_text())

    def pan(self, dx: float, dy: float):
        """Shift the view by (dx, dy) expressed as fractions of the full frame."""
        self._pan_x += dx
        self._pan_y += dy
        self._clamp_pan()

    # ─────────────────────────────────────────────────────────────────────────
    # Mouse events (drag-to-pan + scroll-to-zoom)
    # ─────────────────────────────────────────────────────────────────────────

    def _on_mouse_press(self, event):
        if event.button() == Qt.LeftButton and self._zoom > 1.0:
            self._drag_start = event.pos()
            self._drag_pan_start = (self._pan_x, self._pan_y)
            self.video_label.setCursor(QCursor(Qt.ClosedHandCursor))

    def _on_mouse_move(self, event):
        if self._drag_start is None:
            return
        if not (event.buttons() & Qt.LeftButton):
            self._drag_start = None
            return

        delta = event.pos() - self._drag_start
        lw = self.video_label.width()
        lh = self.video_label.height()

        # Drag RIGHT → pan LEFT (divide by zoom so faster zoom = more sensitive drag)
        dx = -(delta.x() / lw) / self._zoom
        dy = -(delta.y() / lh) / self._zoom

        self._pan_x = self._drag_pan_start[0] + dx
        self._pan_y = self._drag_pan_start[1] + dy
        self._clamp_pan()

    def _on_mouse_release(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_start = None
            self._drag_pan_start = None
            cursor = Qt.OpenHandCursor if self._zoom > 1.0 else Qt.ArrowCursor
            self.video_label.setCursor(QCursor(cursor))

    def _on_wheel(self, event):
        delta = event.angleDelta().y()
        if delta > 0:
            self._zoom_by(+self.ZOOM_STEP)
        elif delta < 0:
            self._zoom_by(-self.ZOOM_STEP)


class MainWindow(QMainWindow):
    CAMERA_INVERTED = {
        0: False,
        1: True,
        2: False,
    }
    CAMERA_INDICES = [0, 2, 3]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SufniBot v3 | Gondaaa")
        self.setMinimumSize(1000, 850)
        self.setStyleSheet("background-color: #0f0f1a; color: #e0e0e0;")
        self.installEventFilter(self)

        self.servos = {"base": 90, "neck": 90, "gripper": 90, "tail": 90}
        self.current_tab = 0

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Tab bar ────────────────────────────────────────────────────────────
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

        # ── Stacked pages ──────────────────────────────────────────────────────
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background-color: #0f0f1a;")
        main_layout.addWidget(self.stack)

        self.camera_widgets = []
        for i, cam_idx in enumerate(self.CAMERA_INDICES):
            cam = CameraWidget(camera_index=cam_idx, servos=self.servos)
            self.camera_widgets.append(cam)
            self.stack.addWidget(cam)

        self.switch_page(0)

    # ── Helpers ────────────────────────────────────────────────────────────────

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

    def update_servo_labels(self):
        text = (
            f"Base: {self.servos['base']}\n"
            f"Neck: {self.servos['neck']}\n"
            f"Gripper: {self.servos['gripper']}\n"
            f"Tail: {self.servos['tail']}"
        )
        for cam in self.camera_widgets:
            cam.servo_label.setText(text)

    def switch_page(self, index: int):
        current = self.stack.currentIndex()
        if current != index:
            self.camera_widgets[current].stop_camera()
        self.current_tab = index
        self.stack.setCurrentIndex(index)
        self.camera_widgets[index].start_camera()
        for i, btn in enumerate(self.tab_buttons):
            btn.setChecked(i == index)

    def closeEvent(self, event):
        for cam in self.camera_widgets:
            cam.stop_camera()
        super().closeEvent(event)

    # ── Key bindings ───────────────────────────────────────────────────────────

    def _active_cam(self) -> CameraWidget:
        return self.camera_widgets[self.current_tab]

    def eventFilter(self, source, event):
            if event.type() == QtCore.QEvent.KeyPress:
                inverted = self.CAMERA_INVERTED.get(self.current_tab, False)
                cam = self._active_cam()
    
                # ── Movement ──────────────────────────────────────────────────────
                if event.key() == Qt.Key_W:
                    bw() if inverted else fw()
    
                elif event.key() == Qt.Key_S:
                    fw() if inverted else bw()
    
                elif event.key() == Qt.Key_A:
                    left()
    
                elif event.key() == Qt.Key_D:
                    right()
    
                # ── Camera pan (arrow keys) ───────────────────────────────────────
                elif event.key() == Qt.Key_Left:
                    cam.pan(-cam.PAN_STEP, 0)
    
                elif event.key() == Qt.Key_Right:
                    cam.pan(+cam.PAN_STEP, 0)
    
                elif event.key() == Qt.Key_Up:
                    cam.pan(0, -cam.PAN_STEP)
    
                elif event.key() == Qt.Key_Down:
                    cam.pan(0, +cam.PAN_STEP)
    
                # ── Camera zoom (+ / −) ───────────────────────────────────────────
                elif event.key() in (Qt.Key_Plus, Qt.Key_Equal):
                    cam.zoom_in()
    
                elif event.key() == Qt.Key_Minus:
                    cam.zoom_out()
    
                # ── Reset view ────────────────────────────────────────────────────
                elif event.key() == Qt.Key_R:
                    cam.reset_view()
    
                # ── Servos ────────────────────────────────────────────────────────
                elif event.key() == Qt.Key_I:
                    self.servos["base"] = moveAngle(self.servos["base"], "positive", "base")
                    self.update_servo_labels()
    
                elif event.key() == Qt.Key_K:
                    self.servos["base"] = moveAngle(self.servos["base"], "negative", "base")
                    self.update_servo_labels()
    
                elif event.key() == Qt.Key_O:
                    self.servos["neck"] = moveAngle(self.servos["neck"], "positive", "neck")
                    self.update_servo_labels()
    
                elif event.key() == Qt.Key_L:
                    self.servos["neck"] = moveAngle(self.servos["neck"], "negative", "neck")
                    self.update_servo_labels()
    
                elif event.key() == Qt.Key_N:
                    self.servos["gripper"] = moveAngle(self.servos["gripper"], "positive", "gripper")
                    self.update_servo_labels()
    
                elif event.key() == Qt.Key_M:
                    self.servos["gripper"] = moveAngle(self.servos["gripper"], "negative", "gripper")
                    self.update_servo_labels()
    
                elif event.key() == Qt.Key_U:
                    self.servos["tail"] = moveAngle(self.servos["tail"], "positive", "tail")
                    self.update_servo_labels()
    
                elif event.key() == Qt.Key_J:
                    self.servos["tail"] = moveAngle(self.servos["tail"], "negative", "tail")
                    self.update_servo_labels()
    
                elif event.key() == Qt.Key_0:
                    for name in self.servos:
                        self.servos[name] = setAngle(name, 0)
                    self.update_servo_labels()
    
                elif event.key() == Qt.Key_1:
                    self.servos["base"] = setAngle("base", 150)
                    self.servos["neck"] = setAngle("neck", 180)
                    self.update_servo_labels()
    
                elif event.key() == Qt.Key_3:
                    self.servos["tail"] = setAngle("tail", 180)
                    self.update_servo_labels()
    
                elif event.key() == Qt.Key_4:
                    self.servos["tail"] = setAngle("tail", 0)
                    self.update_servo_labels()
    
            elif event.type() == QtCore.QEvent.KeyRelease:
                if event.key() in (Qt.Key_W, Qt.Key_S, Qt.Key_A, Qt.Key_D):
                    stop()
    
            return super().eventFilter(source, event)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()