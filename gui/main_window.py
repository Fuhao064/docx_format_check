# -*- coding: utf-8 -*-
"""
Scriptor 主窗口
基于 PyQt6 的图形界面
"""

import sys
import os
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QLabel, QFileDialog, QMessageBox,
    QSplitter, QTextEdit, QGroupBox, QComboBox, QCheckBox,
    QListWidget, QListWidgetItem, QProgressBar, QStatusBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QFont, QTextCursor, QTextCharFormat, QColor


# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class DocumentProcessorThread(QThread):
    """文档处理线程"""
    progress_updated = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str, dict)
    log_updated = pyqtSignal(str)

    def __init__(self, file_path: str, mode: str, options: dict):
        super().__init__()
        self.file_path = file_path
        self.mode = mode
        self.options = options

    def run(self):
        try:
            self.progress_updated.emit(10, "正在加载文档...")
            self.log_updated.emit(f"开始处理: {self.file_path}")

            # 模拟处理过程（实际会调用后端模块）
            import time
            time.sleep(0.5)

            self.progress_updated.emit(30, "正在分析格式...")
            self.log_updated.emit("格式分析中...")
            time.sleep(0.5)

            self.progress_updated.emit(50, "正在检查标点符号...")
            self.log_updated.emit("标点符号检查中...")
            time.sleep(0.5)

            self.progress_updated.emit(70, "正在生成报告...")
            self.log_updated.emit("生成报告中...")
            time.sleep(0.5)

            self.progress_updated.emit(100, "完成!")
            self.log_updated.emit("处理完成!")

            self.finished.emit(
                True,
                "文档处理完成",
                {"issues": 5, "fixed": 3, "report": "模拟报告"}
            )
        except Exception as e:
            self.log_updated.emit(f"错误: {str(e)}")
            self.finished.emit(False, str(e), {})


class MainWindow(QMainWindow):
    """Scriptor 主窗口"""

    def __init__(self):
        super().__init__()
        self.current_file: Optional[str] = None
        self.processor_thread: Optional[DocumentProcessorThread] = None

        self.init_ui()
        self.init_style()

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("Scriptor - 智能文档格式检查")
        self.setMinimumSize(1200, 800)

        # 主部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)

        # 工具栏区域
        toolbar_layout = self.create_toolbar()
        main_layout.addLayout(toolbar_layout)

        # 分割窗口
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧 - 文档处理面板
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)

        # 右侧 - 结果显示面板
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)

        splitter.setSizes([500, 700])
        main_layout.addWidget(splitter)

        # 底部日志面板
        log_panel = self.create_log_panel()
        main_layout.addWidget(log_panel)

        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

    def init_style(self):
        """初始化样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f7fa;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ccd0d5;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #1890ff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #40a9ff;
            }
            QPushButton:pressed {
                background-color: #096dd9;
            }
            QPushButton:disabled {
                background-color: #d9d9d9;
            }
            QTextEdit, QListWidget {
                border: 1px solid #d9d9d9;
                border-radius: 4px;
                background-color: white;
            }
        """)

    def create_toolbar(self) -> QHBoxLayout:
        """创建工具栏"""
        layout = QHBoxLayout()

        # 模式选择
        mode_label = QLabel("处理模式:")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "学术论文模式",
            "公文标准模式 (GB/T 9704-2012)",
            "标点符号修复模式",
            "自定义模式"
        ])
        self.mode_combo.setCurrentIndex(1)  # 默认公文模式

        # 打开文件按钮
        self.open_btn = QPushButton("打开文档")
        self.open_btn.clicked.connect(self.open_document)

        # 保存按钮
        self.save_btn = QPushButton("保存结果")
        self.save_btn.clicked.connect(self.save_document)
        self.save_btn.setEnabled(False)

        layout.addWidget(mode_label)
        layout.addWidget(self.mode_combo)
        layout.addSpacing(20)
        layout.addWidget(self.open_btn)
        layout.addWidget(self.save_btn)
        layout.addStretch()

        return layout

    def create_left_panel(self) -> QWidget:
        """创建左侧面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # 文件信息组
        file_group = QGroupBox("文件信息")
        file_layout = QVBoxLayout()
        self.file_label = QLabel("未选择文件")
        self.file_label.setWordWrap(True)
        file_layout.addWidget(self.file_label)
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # 处理选项组
        options_group = QGroupBox("处理选项")
        options_layout = QVBoxLayout()

        self.check_format_cb = QCheckBox("检查格式问题")
        self.check_format_cb.setChecked(True)
        self.fix_punctuation_cb = QCheckBox("修复标点符号")
        self.fix_punctuation_cb.setChecked(True)
        self.auto_fix_cb = QCheckBox("自动修复问题")
        self.auto_fix_cb.setChecked(False)
        self.preview_cb = QCheckBox("修复前预览")
        self.preview_cb.setChecked(True)

        options_layout.addWidget(self.check_format_cb)
        options_layout.addWidget(self.fix_punctuation_cb)
        options_layout.addWidget(self.auto_fix_cb)
        options_layout.addWidget(self.preview_cb)
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # 处理按钮
        self.process_btn = QPushButton("开始处理")
        self.process_btn.clicked.connect(self.start_processing)
        self.process_btn.setEnabled(False)
        self.process_btn.setMinimumHeight(40)
        layout.addWidget(self.process_btn)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # 问题列表
        issues_group = QGroupBox("检测到的问题")
        issues_layout = QVBoxLayout()
        self.issues_list = QListWidget()
        issues_layout.addWidget(self.issues_list)
        issues_group.setLayout(issues_layout)
        layout.addWidget(issues_group)

        return panel

    def create_right_panel(self) -> QWidget:
        """创建右侧面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # 标签页
        self.tab_widget = QTabWidget()

        # 预览标签页
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setFont(QFont("Microsoft YaHei", 10))
        self.tab_widget.addTab(self.preview_text, "文档预览")

        # 差异对比标签页
        self.diff_text = QTextEdit()
        self.diff_text.setReadOnly(True)
        self.diff_text.setFont(QFont("Consolas", 9))
        self.tab_widget.addTab(self.diff_text, "差异对比")

        # 报告标签页
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        self.report_text.setFont(QFont("Microsoft YaHei", 9))
        self.tab_widget.addTab(self.report_text, "分析报告")

        layout.addWidget(self.tab_widget)
        return panel

    def create_log_panel(self) -> QGroupBox:
        """创建日志面板"""
        group = QGroupBox("处理日志")
        layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_text)

        group.setLayout(layout)
        return group

    def open_document(self):
        """打开文档"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择 Word 文档",
            "",
            "Word 文档 (*.docx);;所有文件 (*.*)"
        )

        if file_path:
            self.current_file = file_path
            self.file_label.setText(os.path.basename(file_path))
            self.process_btn.setEnabled(True)
            self.save_btn.setEnabled(False)
            self.log_message(f"已打开文件: {file_path}")
            self.status_bar.showMessage(f"已加载: {os.path.basename(file_path)}")

            # 预览文档
            self.preview_text.setPlainText(f"文档已加载: {file_path}\n\n(此处显示文档内容预览)")

    def save_document(self):
        """保存文档"""
        if not self.current_file:
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存处理后的文档",
            os.path.splitext(self.current_file)[0] + "_fixed.docx",
            "Word 文档 (*.docx);;所有文件 (*.*)"
        )

        if save_path:
            self.log_message(f"已保存到: {save_path}")
            QMessageBox.information(self, "成功", "文档已保存!")

    def start_processing(self):
        """开始处理文档"""
        if not self.current_file:
            return

        options = {
            "check_format": self.check_format_cb.isChecked(),
            "fix_punctuation": self.fix_punctuation_cb.isChecked(),
            "auto_fix": self.auto_fix_cb.isChecked(),
            "preview": self.preview_cb.isChecked(),
            "mode": self.mode_combo.currentText()
        }

        self.process_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.issues_list.clear()

        self.processor_thread = DocumentProcessorThread(
            self.current_file,
            self.mode_combo.currentText(),
            options
        )
        self.processor_thread.progress_updated.connect(self.on_progress_updated)
        self.processor_thread.finished.connect(self.on_processing_finished)
        self.processor_thread.log_updated.connect(self.log_message)
        self.processor_thread.start()

    def on_progress_updated(self, value: int, message: str):
        """进度更新"""
        self.progress_bar.setValue(value)
        self.status_bar.showMessage(message)

    def on_processing_finished(self, success: bool, message: str, result: dict):
        """处理完成"""
        self.process_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.save_btn.setEnabled(success)

        if success:
            # 添加示例问题
            sample_issues = [
                "标题字体应为 方正小标宋简体",
                "正文字号应为 16磅 (三号)",
                "第 5 行: 半角逗号应改为全角",
                "第 12 行: 半角句号应改为全角",
                "行距应设为 29磅"
            ]
            for issue in sample_issues:
                QListWidgetItem(issue, self.issues_list)

            # 更新预览
            self.report_text.setPlainText(
                "=== 格式分析报告 ===\n\n"
                f"标准: GB/T 9704-2012\n"
                f"检测问题: {len(sample_issues)} 个\n"
                f"可自动修复: 3 个\n\n"
                "详细问题见左侧列表。"
            )

            self.diff_text.setPlainText(
                "--- 原文 ---\n"
                "+++ 修改后 ---\n\n"
                "- 这是一段有错误的文字,使用了半角标点。\n"
                "+ 这是一段有错误的文字，使用了半角标点。\n"
            )

            QMessageBox.information(self, "完成", message)
            self.status_bar.showMessage("处理完成")
        else:
            QMessageBox.critical(self, "错误", f"处理失败: {message}")
            self.status_bar.showMessage("处理失败")

    def log_message(self, message: str):
        """添加日志消息"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

        # 滚动到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("Scriptor")
    app.setOrganizationName("Scriptor")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
