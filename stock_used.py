from PyQt5.QtWidgets import QDialogButtonBox, QCalendarWidget, QDialog, QVBoxLayout,  QLabel

class StockUsedDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Stock Used")

        # Create widgets
        start_date_label = QLabel("Start date:")
        self.start_date_picker = QCalendarWidget()
        end_date_label = QLabel("End date:")
        self.end_date_picker = QCalendarWidget()
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        # Add widgets to layout
        layout = QVBoxLayout()
        layout.addWidget(start_date_label)
        layout.addWidget(self.start_date_picker)
        layout.addWidget(end_date_label)
        layout.addWidget(self.end_date_picker)
        layout.addWidget(button_box)
        self.setLayout(layout)

    def get_date_range(self):
        start_date = self.start_date_picker.selectedDate().toString("yyyy-MM-dd HH:MM:SS")
        end_date = self.end_date_picker.selectedDate().toString("yyyy-MM-dd HH:MM:SS")
        return start_date, end_date