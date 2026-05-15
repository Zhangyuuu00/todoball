import sys
import uuid
import time
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize, QPoint, QPropertyAnimation, QEasingCurve
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QListWidget, QLabel,
    QListWidgetItem, QAbstractItemView, QMenu
)
from PyQt6.QtGui import QGuiApplication, QCursor, QColor


class TaskItemWidget(QWidget):
    """任务项组件"""
    star_clicked = pyqtSignal()
    delete_triggered = pyqtSignal()
    check_toggled = pyqtSignal()
    text_changed = pyqtSignal(str)

    def __init__(self, text, is_done=False, parent=None):
        super().__init__(parent)

        self.delete_bg = QWidget(self)
        self.delete_bg.setStyleSheet("background-color: #ff7675; border-radius: 4px;")

        self.del_label = QLabel("松开删除", self.delete_bg)
        self.del_label.setStyleSheet("color: white; font-weight: bold; font-size: 11px;")

        self.content_container = QWidget(self)
        self.content_container.setStyleSheet("background: white; border-radius: 4px;")

        self.main_layout = QHBoxLayout(self.content_container)
        self.main_layout.setContentsMargins(5, 0, 5, 0)
        self.main_layout.setSpacing(5)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.check_btn = QPushButton()
        self.check_btn.setFixedSize(22, 22)
        self.check_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.check_btn.clicked.connect(self.check_toggled.emit)

        self.label = QLabel(text)
        self.label.setTextFormat(Qt.TextFormat.RichText)
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.label.setStyleSheet(
            "border: none; background: transparent; color: #2c3e50; font-size: 13px; padding: 5px 0;"
        )

        self.edit_field = QLineEdit(text)
        self.edit_field.setVisible(False)
        self.edit_field.setStyleSheet("""
            QLineEdit {
                border: 1px solid #74b9ff;
                border-radius: 4px;
                background: #f1f2f6;
                color: #2d3436;
                font-size: 13px;
                padding: 2px;
            }
        """)
        self.edit_field.returnPressed.connect(self.finish_editing)
        self.edit_field.focusOutEvent = self._handle_focus_out

        self.right_container = QWidget()
        self.right_container.setFixedWidth(45)

        self.right_layout = QHBoxLayout(self.right_container)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setSpacing(2)
        self.right_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.star_btn = QPushButton("★")
        self.star_btn.setFixedSize(18, 18)
        self.star_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.star_btn.setStyleSheet(
            "QPushButton { border: none; background: transparent; font-size: 14px; color: #b2bec3; }"
        )
        self.star_btn.clicked.connect(self.star_clicked.emit)

        self.slider_handle = QLabel("〈")
        self.slider_handle.setFixedSize(20, 18)
        self.slider_handle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.slider_handle.setCursor(Qt.CursorShape.SizeHorCursor)
        self.slider_handle.setStyleSheet("color: #dfe6e9; font-weight: bold; font-size: 14px;")

        self.right_layout.addWidget(self.star_btn)
        self.right_layout.addWidget(self.slider_handle)

        self.main_layout.addWidget(self.check_btn, 0)
        self.main_layout.addWidget(self.label, 1)
        self.main_layout.addWidget(self.edit_field, 1)
        self.main_layout.addWidget(self.right_container, 0)

        self.is_dragging_delete = False
        self.current_offset = 0

    def mouseDoubleClickEvent(self, event):
        if not self.label.isVisible():
            return

        self.label.setVisible(False)
        self.edit_field.setText(self.label.text())
        self.edit_field.setVisible(True)
        self.edit_field.setFocus()
        self.edit_field.selectAll()

    def _handle_focus_out(self, event):
        QLineEdit.focusOutEvent(self.edit_field, event)
        self.finish_editing()

    def finish_editing(self):
        if self.edit_field.isVisible():
            new_text = self.edit_field.text().strip()

            if new_text:
                self.text_changed.emit(new_text)

            self.edit_field.setVisible(False)
            self.label.setVisible(True)

    def resizeEvent(self, event):
        self.delete_bg.resize(self.size())
        self.content_container.resize(self.size())

        self.del_label.move(
            self.width() - 60,
            (self.height() - self.del_label.height()) // 2
        )

        super().resizeEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if event.pos().x() > self.width() - 35:
                self.is_dragging_delete = True
                self.start_x = event.globalPosition().x()
                event.accept()
            else:
                super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_dragging_delete:
            delta_x = event.globalPosition().x() - self.start_x

            self.current_offset = min(0, max(-self.width(), delta_x))

            self.content_container.move(int(self.current_offset), 0)

            opacity = min(1.0, abs(self.current_offset) / (self.width() / 1.5))

            self.del_label.setStyleSheet(
                f"color: rgba(255, 255, 255, {int(opacity * 255)}); font-weight: bold;"
            )

            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.is_dragging_delete:
            self.is_dragging_delete = False

            if abs(self.current_offset) > self.width() / 2:
                self.delete_triggered.emit()
            else:
                self.anim = QPropertyAnimation(self.content_container, b"pos")
                self.anim.setDuration(200)
                self.anim.setStartValue(self.content_container.pos())
                self.anim.setEndValue(QPoint(0, 0))
                self.anim.setEasingCurve(QEasingCurve.Type.OutQuad)
                self.anim.start()

            self.current_offset = 0
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def update_style(self, display_text, is_done, number=None, is_starred=False):
        if is_done:
            check_style = (
                "border: 2px solid #2ecc71; "
                "border-radius: 11px; "
                "background: #2ecc71; "
                "color: white; "
                "font-size: 14px; "
                "font-weight: bold;"
            )

            self.check_btn.setText("✓")

        else:
            num_color = "#f1c40f" if is_starred else "#a29bfe"

            check_style = (
                f"border: 2px solid {num_color}; "
                f"border-radius: 11px; "
                f"background: transparent; "
                f"color: {num_color}; "
                f"font-size: 10px; "
                f"font-weight: bold;"
            )

            self.check_btn.setText(str(number) if number else "")

        self.check_btn.setStyleSheet(f"QPushButton {{ {check_style} }}")

        self.label.setText(display_text)

        color = '#95a5a6' if is_done else '#2c3e50'

        self.label.setStyleSheet(
            f"border: none; color: {color}; background: transparent; padding: 0px; margin: 0px;"
        )

        star_color = "#f1c40f" if is_starred else "#b2bec3"

        self.star_btn.setStyleSheet(
            f"QPushButton {{ border: none; background: transparent; font-size: 14px; color: {star_color}; }}"
        )

        self.star_btn.setVisible(not is_done)


class TaskPopup(QWidget):
    def __init__(self, parent):
        super().__init__()

        self.parent_ball = parent

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setFixedSize(280, 420)

        self.layout = QVBoxLayout(self)

        self.bg_widget = QWidget()

        self.bg_widget.setStyleSheet("""
            QWidget {
                background: rgba(255, 255, 255, 252);
                border-radius: 16px;
                border: 1px solid rgba(0, 0, 0, 0.05);
            }
        """)

        inner_layout = QVBoxLayout(self.bg_widget)

        self.completion_tip = QLabel("已完成！", self.bg_widget)

        self.completion_tip.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.completion_tip.setStyleSheet("""
            background: rgba(46, 204, 113, 230);
            color: white;
            font-weight: bold;
            border-radius: 8px;
            padding: 5px 15px;
        """)

        self.completion_tip.hide()

        header_layout = QHBoxLayout()

        tip_label = QLabel("勾选完成 | 双击编辑内容 | 右滑删除")

        tip_label.setStyleSheet(
            "color: #b2bec3; font-size: 10px; border: none; margin-left: 5px;"
        )

        self.clear_all_btn = QPushButton("清除全部")

        self.clear_all_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                color: #ff7675;
                font-size: 10px;
                font-weight: bold;
            }
        """)

        self.clear_all_btn.clicked.connect(self.clear_all_tasks)

        header_layout.addWidget(tip_label)
        header_layout.addStretch()
        header_layout.addWidget(self.clear_all_btn)

        inner_layout.addLayout(header_layout)

        input_area = QHBoxLayout()

        self.input_field = QLineEdit()

        self.input_field.setPlaceholderText("记录新任务...")

        self.input_field.setStyleSheet("""
            QLineEdit {
                color: #2d3436;
                padding: 8px;
                border: 1px solid #f1f2f6;
                border-radius: 8px;
                background: #fdfdfd;
            }
        """)

        self.add_btn = QPushButton("+")

        self.add_btn.setFixedWidth(40)

        self.add_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #74b9ff,
                    stop:1 #a29bfe
                );
                color: white;
                font-weight: bold;
                border-radius: 8px;
                font-size: 16px;
            }
        """)

        input_area.addWidget(self.input_field)
        input_area.addWidget(self.add_btn)

        self.task_list = QListWidget()

        self.task_list.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.task_list.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
                outline: none;
            }

            QListWidget::item {
                border-bottom: 1px solid #fbfbfb;
            }
        """)

        inner_layout.addLayout(input_area)
        inner_layout.addWidget(self.task_list)

        self.layout.addWidget(self.bg_widget)

        self.add_btn.clicked.connect(self.add_task)
        self.input_field.returnPressed.connect(self.add_task)

    def show_completion_tip(self):
        self.completion_tip.raise_()

        self.completion_tip.adjustSize()

        self.completion_tip.move(
            (self.bg_widget.width() - self.completion_tip.width()) // 2,
            (self.bg_widget.height() - self.completion_tip.height()) // 2
        )

        self.completion_tip.show()

        QTimer.singleShot(2000, self.completion_tip.hide)

    def create_widget_for_item(self, item, text):
        widget = TaskItemWidget(text)

        widget.star_clicked.connect(lambda: self.toggle_star_task(item))
        widget.delete_triggered.connect(lambda: self.delete_task(item))
        widget.check_toggled.connect(lambda: self.strike_task(item))
        widget.text_changed.connect(
            lambda new_text: self.update_task_text(item, new_text)
        )

        self.task_list.setItemWidget(item, widget)

        self.update_item_height(item, widget)

        return widget

    def update_task_text(self, item, new_text):
        item.setData(Qt.ItemDataRole.UserRole, new_text)
        self.refresh_numbers()

    def update_item_height(self, item, widget):
        widget.setFixedWidth(240)

        widget.label.setFixedWidth(160)

        widget.label.adjustSize()

        new_height = max(45, widget.label.height() + 20)

        item.setSizeHint(QSize(240, new_height))

        widget.setFixedHeight(new_height)

    def add_task(self):
        text = self.input_field.text().strip()

        if text:
            item = QListWidgetItem()

            item.setData(Qt.ItemDataRole.UserRole, text)
            item.setData(Qt.ItemDataRole.UserRole + 3, False)
            item.setData(Qt.ItemDataRole.UserRole + 4, time.time())
            item.setData(Qt.ItemDataRole.UserRole + 5, False)

            self.task_list.addItem(item)

            self.create_widget_for_item(item, text)

            self.input_field.clear()

            self.fix_order_and_widgets()

    def toggle_star_task(self, item):
        is_starred = not item.data(Qt.ItemDataRole.UserRole + 3)

        item.setData(Qt.ItemDataRole.UserRole + 3, is_starred)

        self.fix_order_and_widgets()

    def strike_task(self, item):
        if not item.data(Qt.ItemDataRole.UserRole + 5):
            self.show_completion_tip()

        is_done = not item.data(Qt.ItemDataRole.UserRole + 5)

        item.setData(Qt.ItemDataRole.UserRole + 5, is_done)

        self.fix_order_and_widgets()

    def delete_task(self, item):
        row = self.task_list.row(item)

        if row != -1:
            self.task_list.takeItem(row)

        self.refresh_numbers()

    def clear_all_tasks(self):
        self.task_list.clear()

    def fix_order_and_widgets(self):
        self.task_list.blockSignals(True)

        active_items = []
        done_items = []

        for i in range(self.task_list.count()):
            it = self.task_list.takeItem(0)

            if it.data(Qt.ItemDataRole.UserRole) == "SEPARATOR":
                continue

            if it.data(Qt.ItemDataRole.UserRole + 5):
                done_items.append(it)
            else:
                active_items.append(it)

        active_items.sort(
            key=lambda it: (
                0 if it.data(Qt.ItemDataRole.UserRole + 3) else 1,
                it.data(Qt.ItemDataRole.UserRole + 4)
            )
        )

        done_items.sort(
            key=lambda it: it.data(Qt.ItemDataRole.UserRole + 4)
        )

        for it in active_items:
            self.task_list.addItem(it)

            self.create_widget_for_item(
                it,
                it.data(Qt.ItemDataRole.UserRole)
            )

        if done_items:
            sep = QListWidgetItem("已完成")

            sep.setData(Qt.ItemDataRole.UserRole, "SEPARATOR")

            sep.setFlags(Qt.ItemFlag.NoItemFlags)

            sep.setSizeHint(QSize(240, 30))

            sep.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            sep.setForeground(QColor("#b2bec3"))

            font = sep.font()
            font.setPointSize(9)
            font.setBold(True)

            sep.setFont(font)

            self.task_list.addItem(sep)

        for it in done_items:
            self.task_list.addItem(it)

            self.create_widget_for_item(
                it,
                it.data(Qt.ItemDataRole.UserRole)
            )

        self.refresh_numbers()

        self.task_list.blockSignals(False)

    def refresh_numbers(self):
        active_count = 1

        for i in range(self.task_list.count()):
            item = self.task_list.item(i)

            if not item:
                continue

            if item.data(Qt.ItemDataRole.UserRole) == "SEPARATOR":
                continue

            is_done = item.data(Qt.ItemDataRole.UserRole + 5)

            text = item.data(Qt.ItemDataRole.UserRole)

            is_starred = item.data(Qt.ItemDataRole.UserRole + 3)

            widget = self.task_list.itemWidget(item)

            if not widget:
                widget = self.create_widget_for_item(item, text)

            widget.update_style(
                text,
                is_done,
                number=active_count if not is_done else None,
                is_starred=is_starred
            )

            if not is_done:
                active_count += 1

            self.update_item_height(item, widget)


class TodoBall(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setFixedSize(80, 80)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(0, 0, 0, 0)

        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.ball_label = QLabel("TASKS")

        self.ball_label.setFixedSize(64, 64)

        self.ball_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.ball_label.setStyleSheet("""
            QLabel {
                background: qradialgradient(
                    cx:0.5, cy:0.5,
                    radius:0.5,
                    fx:0.5, fy:0.5,
                    stop:0.0 rgba(116, 185, 255, 255),
                    stop:1.0 rgba(255, 255, 255, 100)
                );
                color: #FFFFFF;
                border-radius: 32px;
                font-weight: 800;
                font-size: 10px;
            }
        """)

        layout.addWidget(self.ball_label)

        self.popup = TaskPopup(self)

        self.out_time = 0

        self.checker_timer = QTimer()

        self.checker_timer.timeout.connect(self.guard_logic)

        self.checker_timer.start(100)

    def guard_logic(self):
        if not self.popup.isVisible():
            return

        mouse_pos = QCursor.pos()

        is_editing = False

        for i in range(self.popup.task_list.count()):
            item = self.popup.task_list.item(i)

            widget = self.popup.task_list.itemWidget(item)

            if isinstance(widget, TaskItemWidget) and widget.edit_field.isVisible():
                is_editing = True
                break

        if (
            self.geometry().contains(mouse_pos)
            or self.popup.geometry().contains(mouse_pos)
            or self.popup.input_field.hasFocus()
            or is_editing
        ):
            self.out_time = 0
            return

        if self.out_time == 0:
            self.out_time = time.time()

        if time.time() - self.out_time >= 1.0:
            self.popup.hide()
            self.out_time = 0

    def enterEvent(self, event):
        self.out_time = 0

        if not self.popup.isVisible():
            self.update_popup_position()
            self.popup.show()

    def update_popup_position(self):
        screen = (
            QGuiApplication.screenAt(self.geometry().center())
            or QGuiApplication.primaryScreen()
        )

        geo = screen.availableGeometry()

        ball = self.geometry()

        tx = max(
            geo.left(),
            min(
                ball.x() + (ball.width() - self.popup.width()) // 2,
                geo.right() - self.popup.width()
            )
        )

        ty = ball.y() + ball.height() + 5

        if ty + self.popup.height() > geo.bottom():
            ty = ball.y() - self.popup.height() - 5

        self.popup.move(tx, ty)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = (
                event.globalPosition().toPoint()
                - self.frameGeometry().topLeft()
            )

    def mouseMoveEvent(self, event):
        if hasattr(self, 'drag_pos'):
            curr = event.globalPosition().toPoint()

            screen = (
                QGuiApplication.screenAt(curr)
                or QGuiApplication.primaryScreen()
            )

            geo = screen.availableGeometry()

            new_x = curr.x() - self.drag_pos.x()
            new_y = curr.y() - self.drag_pos.y()

            limited_x = max(
                geo.left(),
                min(new_x, geo.right() - self.width())
            )

            limited_y = max(
                geo.top(),
                min(new_y, geo.bottom() - self.height())
            )

            self.move(limited_x, limited_y)

            if self.popup.isVisible():
                self.update_popup_position()

    # ==========================
    # 新增：右键菜单退出功能
    # ==========================
    def contextMenuEvent(self, event):
        menu = QMenu(self)

        menu.setStyleSheet("""
            QMenu {
                background: white;
                border: 1px solid #dfe6e9;
                border-radius: 8px;
                padding: 5px;
            }

            QMenu::item {
                padding: 8px 20px;
                border-radius: 4px;
            }

            QMenu::item:selected {
                background: #74b9ff;
                color: white;
            }
        """)

        exit_action = menu.addAction("退出")

        action = menu.exec(event.globalPos())

        if action == exit_action:
            QApplication.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    todo = TodoBall()

    todo.show()

    sys.exit(app.exec())