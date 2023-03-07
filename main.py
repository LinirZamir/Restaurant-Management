import sys
import pandas as pd
from PyQt5.QtWidgets import QDialogButtonBox,  QTabWidget, QSystemTrayIcon, QDialog, QApplication, QSpinBox, QMenuBar, QMenu, QAction, QMessageBox, QFileDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QFont, QIcon, QIntValidator, QDoubleValidator
from PyQt5.QtCore import Qt, QTimer, QSettings
import sqlite3
import csv
from datetime import datetime
import numpy as np

import matplotlib.pyplot as plt

from sklearn.linear_model import LinearRegression
from stock_used import StockUsedDialog
class InventoryManagementSystem(QWidget):

    def __init__(self):
        super().__init__()
        self.font = QFont()
        self.font.setPointSize(12)


        self.setWindowTitle("Inventory Management System")
        self.setGeometry(100, 100, 700, 400)
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("icon.png"))
        self.tray_icon.show()

        # Check item quantities every minute
        self.check_quantities_timer = QTimer(self)
        self.check_quantities_timer.timeout.connect(self.check_quantities)
        self.check_quantities_timer.start(6 * 1000)

        # Sorting
        self.sort_order = Qt.AscendingOrder

        # Load settings
        self.load_settings()

        self.setup_ui()
        
    def setup_ui(self):
        # Create widgets

        # Create tab widget
        self.tabs = QTabWidget()
        self.tabs.setGeometry(100, 100, 700, 400)

        # Create tabs
        self.orders_tab = QWidget()
        self.inventory_tab = QWidget()
        self.suppliers_tab = QWidget()
        self.reports_tab = QWidget()

        # Add tabs to the tab widget
        self.tabs.addTab(self.orders_tab, "Orders")
        self.tabs.addTab(self.inventory_tab, "Inventory")
        self.tabs.addTab(self.suppliers_tab, "Suppliers")
        self.tabs.addTab(self.reports_tab, "Reports")

        # Create navigation bar
        self.nav_bar = QHBoxLayout()
        self.add_item_button = QPushButton("Add Item")
        add_icon = QIcon("icons/add_icon.png")
        self.add_item_button.setIcon(add_icon)
        self.add_item_button.setFont(self.font)

        self.edit_item_button = QPushButton("Edit Item")
        edit_icon = QIcon("icons/edit_icon.png")
        self.edit_item_button.setIcon(edit_icon)
        self.edit_item_button.setFont(self.font)

        self.delete_item_button = QPushButton("Delete Item")
        delete_icon = QIcon("icons/delete_icon.png")
        self.delete_item_button.setIcon(delete_icon)
        self.delete_item_button.setFont(self.font)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.setFont(self.font)

        # Add widgets to navigation bar
        self.nav_bar.addWidget(self.add_item_button)
        self.nav_bar.addWidget(self.edit_item_button)
        self.nav_bar.addWidget(self.delete_item_button)
        self.nav_bar.addStretch()
        self.nav_bar.addWidget(self.search_bar)

        # Create main layout and add widgets
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

        # Set up the inventory tab
        self.item_list = QTableWidget()
        self.item_list.setColumnCount(5)
        self.item_list.setHorizontalHeaderLabels(["Item Name", "Description", "Quantity", "Price", "Modified"])
        self.item_list.setColumnWidth(4, 200)  # Set the width of the "Modified" column to 200 pixels

        self.item_list.setEditTriggers(QTableWidget.NoEditTriggers)
        self.item_list.setSelectionBehavior(QTableWidget.SelectRows)
        self.item_list.setFont(self.font)

        # Add the item list to the inventory tab
        inventory_layout = QVBoxLayout()
        inventory_layout.addLayout(self.nav_bar)
        inventory_layout.addWidget(self.item_list)
        self.inventory_tab.setLayout(inventory_layout)

        # Populate item list
        self.populate_item_list()

        # Add item button functionality
        self.add_item_button.clicked.connect(self.add_item)
        # Edit item button functionality
        self.edit_item_button.clicked.connect(self.edit_item)
        # Delete item button functionality
        self.delete_item_button.clicked.connect(self.delete_item)
        # Search bar functionality
        self.search_bar.textChanged.connect(self.search_items)

        # Create a menu bar
        menu_bar = QMenuBar()

        # Add a file menu to the menu bar
        file_menu = QMenu("File", self)
        menu_bar.addMenu(file_menu)

        # Add an export action to the file menu
        export_action = QAction("Export to CSV", self)
        export_action.triggered.connect(self.export_items)
        file_menu.addAction(export_action)

        # Add an import action to the file menu
        import_action = QAction("Import", self)
        import_action.triggered.connect(self.import_items)
        file_menu.addAction(import_action)

        # Add a settings menu to the menu bar
        settings_menu = QMenu("Settings", self)
        menu_bar.addMenu(settings_menu)

        # Add a minimum quantity threshold action to the settings menu
        min_qty_action = QAction("Minimum Quantity Threshold", self)
        min_qty_action.triggered.connect(self.set_min_qty_threshold)
        settings_menu.addAction(min_qty_action)

        # Add a stock use action to the settings menu
        sales_report_action = QAction("Stock Used", self)
        sales_report_action.triggered.connect(self.generate_sales_report)
        settings_menu.addAction(sales_report_action)
        # Add a help menu to the menu bar
        help_menu = QMenu("Help", self)
        menu_bar.addMenu(help_menu)

        # Add an about action to the help menu
        about_action = QAction("About", self)
        about_action.triggered.connect(self.about)
        help_menu.addAction(about_action)

        # Add a close action to the file menu
        close_action = QAction("Close", self)
        close_action.triggered.connect(self.close)
        file_menu.addAction(close_action)
        
        # Graphs
        self.show_chart_button = QPushButton("Show Chart")
        self.nav_bar.addWidget(self.show_chart_button)
        self.show_chart_button.clicked.connect(self.generate_bar_chart)
        self.show_chart_button.setFont(self.font)

        self.item_list.horizontalHeader().sectionClicked.connect(self.sort_table)

        # Set the menu bar to the main layout
        main_layout.setMenuBar(menu_bar)

    def sort_table(self, column):
        self.item_list.sortItems(column, self.sort_order)
        if self.sort_order == Qt.AscendingOrder:
            self.sort_order = Qt.DescendingOrder
        else:
            self.sort_order = Qt.AscendingOrder

    def populate_item_list(self):
        # Connect to the database and retrieve the item data
        conn = sqlite3.connect('inventory.db')
        c = conn.cursor()
        c.execute("SELECT * FROM items")
        items = c.fetchall()
        conn.close()

        # Populate the item list with the data
        self.item_list.setRowCount(len(items))
        for row, item in enumerate(items):
            for column, value in enumerate(item):
                if column == 4:  # Check if the column is the 'Modified' column
                    # Format the time string without milliseconds
                    value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S.%f').strftime('%Y-%m-%d %H:%M:%S')
                self.item_list.setItem(row, column, QTableWidgetItem(str(value)))


    def check_quantities(self):
        conn = sqlite3.connect('inventory.db')
        c = conn.cursor()

        # Get the sales data for each item
        c.execute("SELECT item_name, quantity_sold, time_sold FROM sales")
        sales_data = c.fetchall()

        c.execute("SELECT name, quantity FROM items")
        current_data = c.fetchall()
        # Convert the sales data to a DataFrame and calculate the daily sales
        sales_df = pd.DataFrame(sales_data, columns=['item_name', 'quantity_sold', 'time_sold'])
        sales_df['date'] = pd.to_datetime(sales_df['time_sold'], format='%Y-%m-%d %H:%M:%S').dt.date
        daily_sales = sales_df.groupby(['item_name', 'date'])['quantity_sold'].sum().reset_index()

        # Calculate the moving average of daily sales
        window_size = 1 # Change this to adjust the window size for the moving average
        daily_sales['moving_avg'] = daily_sales.groupby('item_name')['quantity_sold'].rolling(window_size).mean().reset_index(0, drop=True)

        daily_sales.dropna(subset=['moving_avg'], inplace=True)

        # Drop any rows with NaN values
        daily_sales.dropna(inplace=True)

        # Calculate the trend in sales over time for each item
        items = daily_sales['item_name'].unique()
        for item in items:
            item_sales = daily_sales[daily_sales['item_name'] == item]
            if item_sales.empty:
                print(f"No sales data for {item}")
                continue

            lin_reg = LinearRegression()
            item_sales['day_index'] = (item_sales['date'] - item_sales['date'].min()).dt.days
            lin_reg.fit(item_sales[['day_index']], item_sales['moving_avg'])
            item_sales['trend'] = lin_reg.predict(item_sales[['day_index']])

            # Calculate the residual of each data point from the trend line
            item_sales['residual'] = item_sales['moving_avg'] - item_sales['trend']

            # Calculate the standard deviation of the residuals
            std_dev = item_sales['residual'].std()
            
            # Calculate the rolling mean and standard deviation of the residuals for each item
            rolling_mean = item_sales.groupby('item_name')['residual'].rolling(window_size).mean().reset_index(0, drop=True)
            rolling_std = item_sales.groupby('item_name')['residual'].rolling(window_size).std().reset_index(0, drop=True)

            # Get the current mean and standard deviation of the residuals for the item
            current_mean = rolling_mean.iloc[-1]
            current_std = rolling_std.iloc[-1]
            new_threshold = current_mean + (current_std * 2) # Change this to adjust the number of standard deviations

            # Check if the standard deviation is higher than the threshold and notify if needed
            if std_dev > new_threshold: 
                message = f"{item} is experiencing high demand"
                self.tray_icon.showMessage("High Demand Item", message, QSystemTrayIcon.Warning, 5000)

        # Check if the quantity of the item in inventory is low and notify if needed
        for item in current_data:
            c.execute("SELECT quantity FROM items WHERE name = ?", (item[0],))
            quantity_data = c.fetchone()
            if quantity_data is not None:
                quantity = quantity_data[0]
                if quantity < self.min_qty_threshold:  # Change this to adjust the threshold for low inventory
                    message = f"{item[0]} is running low in inventory"
                    self.tray_icon.showMessage("Low Inventory Item", message, QSystemTrayIcon.Warning, 5000)
            else:
                print(f"No inventory data for {item[0]}")

            # Close the database connection
        conn.close()

                
    def add_item(self):
        # Create a new window for adding an item
        add_item_window = QWidget()
        add_item_window.setWindowTitle("Add Item")
        add_item_window.setGeometry(100, 100, 400, 300)

        # Create widgets for the add item window
        name_label = QLabel("Item Name:")
        name_label.setFont(self.font)
        name_input = QLineEdit()
        name_input.setFont(self.font)
        desc_label = QLabel("Description:")
        desc_label.setFont(self.font)
        desc_input = QLineEdit()
        desc_input.setFont(self.font)
        qty_label = QLabel("Quantity:")
        qty_label.setFont(self.font)
        qty_input = QLineEdit()
        qty_input.setFont(self.font)
        qty_validator = QIntValidator()
        qty_input.setValidator(qty_validator)
        price_label = QLabel("Price:")
        price_label.setFont(self.font)
        price_input = QLineEdit()
        price_input.setFont(self.font)
        price_validator = QDoubleValidator()
        price_input.setValidator(price_validator)
        save_button = QPushButton("Save")
        save_button.setFont(self.font)
        cancel_button = QPushButton("Cancel")
        cancel_button.setFont(self.font)

        
        # Add widgets to the add item window
        layout = QVBoxLayout()
        layout.addWidget(name_label)
        layout.addWidget(name_input)
        layout.addWidget(desc_label)
        layout.addWidget(desc_input)
        layout.addWidget(qty_label)
        layout.addWidget(qty_input)
        layout.addWidget(price_label)
        layout.addWidget(price_input)
        layout.addWidget(save_button)
        layout.addWidget(cancel_button)
        add_item_window.setLayout(layout)

        # Show the add item window
        add_item_window.show()

        # Save button functionality
        def save_item():
            # Get the values from the input fields
            name = name_input.text()
            desc = desc_input.text()
            qty = int(qty_input.text())
            price = float(price_input.text())

            # Add the new item to the database
            conn = sqlite3.connect('inventory.db')
            c = conn.cursor()
            current_time = datetime.now()
            c.execute("INSERT INTO items VALUES (?, ?, ?, ?, ?)", (name, desc, qty, price, current_time))
            conn.commit()
            conn.close()

            # Add the new item to the item list
            row = self.item_list.rowCount()
            self.item_list.setRowCount(row + 1)
            self.item_list.setItem(row, 0, QTableWidgetItem(name))
            self.item_list.setItem(row, 1, QTableWidgetItem(desc))
            self.item_list.setItem(row, 2, QTableWidgetItem(str(qty)))
            self.item_list.setItem(row, 3, QTableWidgetItem(str(price)))
            value = datetime.strptime(str(current_time), '%Y-%m-%d %H:%M:%S.%f').strftime('%Y-%m-%d %H:%M:%S')
            self.item_list.setItem(row, 4, QTableWidgetItem(str(value)))

            # Close the add item window
            add_item_window.close()

        # Connect the save button to the save_item function
        save_button.clicked.connect(save_item)

        # Cancel button functionality
        cancel_button.clicked.connect(add_item_window.close)

    def edit_item(self):
        # Get the selected item from the item list
        selected_items = self.item_list.selectedItems()
        if len(selected_items) == 0:
            return
        selected_row = selected_items[0].row()
        name = self.item_list.item(selected_row, 0).text()
        desc = self.item_list.item(selected_row, 1).text()
        qty = int(self.item_list.item(selected_row, 2).text())
        price = float(self.item_list.item(selected_row, 3).text())

        # Create a new window for editing the item
        edit_item_window = QWidget()
        edit_item_window.setWindowTitle("Edit Item")
        edit_item_window.setGeometry(100, 100, 400, 300)

        
        # Create widgets for the add item window
        name_label = QLabel("Item Name:")
        name_label.setFont(self.font)
        name_input = QLineEdit(name)
        name_input.setFont(self.font)
        desc_label = QLabel("Description:")
        desc_label.setFont(self.font)
        desc_input = QLineEdit(desc)
        desc_input.setFont(self.font)
        qty_label = QLabel("Quantity:")
        qty_label.setFont(self.font)
        qty_input = QLineEdit(str(qty))
        qty_input.setFont(self.font)
        qty_validator = QIntValidator()
        qty_input.setValidator(qty_validator)
        price_label = QLabel("Price:")
        price_label.setFont(self.font)
        price_input = QLineEdit(str(price))
        price_input.setFont(self.font)
        price_validator = QDoubleValidator()
        price_input.setValidator(price_validator)
        save_button = QPushButton("Save")
        save_button.setFont(self.font)
        cancel_button = QPushButton("Cancel")
        cancel_button.setFont(self.font)


        # Add widgets to the edit item window
        layout = QVBoxLayout()
        layout.addWidget(name_label)
        layout.addWidget(name_input)
        layout.addWidget(desc_label)
        layout.addWidget(desc_input)
        layout.addWidget(qty_label)
        layout.addWidget(qty_input)
        layout.addWidget(price_label)
        layout.addWidget(price_input)
        layout.addWidget(save_button)
        layout.addWidget(cancel_button)
        edit_item_window.setLayout(layout)

        # Show the edit item window
        edit_item_window.show()

        # Save button functionality
        def save_item():
            # Get the values from the input fields
            new_name = name_input.text()
            new_desc = desc_input.text()
            new_qty = int(qty_input.text())
            new_price = float(price_input.text())
            current_time = datetime.now()

            # Update the selected item in the database
            conn = sqlite3.connect('inventory.db')
            c = conn.cursor()
            c.execute("UPDATE items SET name=?, description=?, quantity=?, price=?, time=? WHERE name=? AND description=? AND quantity=? AND price=?",
                    (new_name, new_desc, new_qty, new_price, current_time, name, desc, qty, price))
            conn.commit()

            # Calculate the quantity difference between the original quantity and the new quantity
            qty_diff = qty - new_qty

            # If the quantity difference is positive, insert a new row into the sales table
            if qty_diff > 0:
                c.execute("INSERT INTO sales (item_name, quantity_sold, time_sold) VALUES (?, ?, ?)",
                        (new_name, qty_diff, current_time))
                conn.commit()

            conn.close()

            # Update the selected item in the item list
            self.item_list.setItem(selected_row, 0, QTableWidgetItem(new_name))
            self.item_list.setItem(selected_row, 1, QTableWidgetItem(new_desc))
            self.item_list.setItem(selected_row, 2, QTableWidgetItem(str(new_qty)))
            self.item_list.setItem(selected_row, 3, QTableWidgetItem(str(new_price)))
            value = datetime.strptime(str(current_time), '%Y-%m-%d %H:%M:%S.%f').strftime('%Y-%m-%d %H:%M:%S')
            self.item_list.setItem(selected_row, 4, QTableWidgetItem(str(value)))

            # Close the edit item window
            edit_item_window.close()

        # Connect the save button to the save_item function
        save_button.clicked.connect(save_item)

        # Cancel button functionality
        cancel_button.clicked.connect(edit_item_window.close)


    def delete_item(self):
        # Get the selected item from the item list
        selected_items = self.item_list.selectedItems()
        if len(selected_items) == 0:
            return
        selected_row = selected_items[0].row()
        name = self.item_list.item(selected_row, 0).text()
        desc = self.item_list.item(selected_row, 1).text()
        qty = int(self.item_list.item(selected_row, 2).text())
        price = float(self.item_list.item(selected_row, 3).text())

        # Show a confirmation message box
        result = QMessageBox.question(self, "Delete Item", "Are you sure you want to delete this item?", QMessageBox.Yes | QMessageBox.No)
        if result == QMessageBox.Yes:
            # Delete the selected item from the database
            conn = sqlite3.connect('inventory.db')
            c = conn.cursor()
            c.execute("DELETE FROM items WHERE name=? AND description=? AND quantity=? AND price=?", (name, desc, qty, price))
            conn.commit()
            conn.close()

            # Delete the selected item from the item list
            self.item_list.removeRow(selected_row)
    
    def search_items(self, search_text):
        # Filter the item list based on the search text
        for row in range(self.item_list.rowCount()):
            name = self.item_list.item(row, 0).text()
            desc = self.item_list.item(row, 1).text()
            if search_text.lower() in name.lower() or search_text.lower() in desc.lower():
                self.item_list.setRowHidden(row, False)
            else:
                self.item_list.setRowHidden(row, True)


    def export_items(self):
        # Get the file path for the CSV file
        file_path, _ = QFileDialog.getSaveFileName(self, "Export to CSV", "", "CSV Files (*.csv)")
        if not file_path:
            return
        
        # Export the inventory data to the CSV file
        with open(file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Name', 'Description', 'Quantity', 'Price', 'Time'])
            for row in range(self.item_list.rowCount()):
                name = self.item_list.item(row, 0).text()
                desc = self.item_list.item(row, 1).text()
                qty = self.item_list.item(row, 2).text()
                price = self.item_list.item(row, 3).text()
                time = self.item_list.item(row, 4).text()
                writer.writerow([name, desc, qty, price, time])

    def import_items(self):
        # Get the file path for the CSV file
        file_path, _ = QFileDialog.getOpenFileName(self, "Import from CSV", "", "CSV Files (*.csv)")
        # Check if the file path is empty (i.e. the user pressed "cancel")
        if not file_path:
            return
        
        # Import the inventory data from the CSV file
        with open(file_path, mode='r') as file:
            reader = csv.reader(file)
            next(reader) # Skip the header row
            for row in reader:
                name = row[0]
                desc = row[1]
                qty = int(row[2])
                price = float(row[3])
                time = row[4]
                self.add_item_to_table(name, desc, qty, price, time)

    def about(self):
        # Show a message box with information about the program
        QMessageBox.about(self, "About Inventory Manager", "This program allows you to manage your inventory.\n")


    def generate_bar_chart(self):
        conn = sqlite3.connect("inventory.db")
        c = conn.cursor()

        # Retrieve data from the database
        c.execute("SELECT name, quantity FROM items")
        data = c.fetchall()

        # Create a bar chart showing the quantity of each item in the inventory
        items = [d[0] for d in data]
        quantities = [d[1] for d in data]
        y_pos = np.arange(len(items))
        plt.bar(y_pos, quantities, align='center', alpha=0.5)
        plt.xticks(y_pos, items)
        plt.ylabel('Quantity')
        plt.title('Inventory Report')

        # Show the chart
        plt.show()


    def set_min_qty_threshold(self):
        # Create a new dialog for setting the minimum quantity threshold
        dialog = QDialog(self)
        dialog.setWindowTitle("Set Minimum Quantity Threshold")
        dialog.setGeometry(100, 100, 400, 150)

        # Create widgets for the dialog
        label = QLabel("Enter the new minimum quantity threshold:")
        input = QSpinBox()
        input.setRange(0, 9999)
        input.setValue(self.min_qty_threshold)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        # Add widgets to the dialog
        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(input)
        layout.addWidget(button_box)
        dialog.setLayout(layout)

        # Show the dialog and update the minimum quantity threshold if the user clicks "Ok"
        if dialog.exec_() == QDialog.Accepted:
            self.min_qty_threshold = input.value()
            message = f"Minimum quantity threshold updated to {self.min_qty_threshold}"
            QMessageBox.information(self, "Information", message)
            # Save the new minimum quantity threshold to the settings file
            settings = QSettings("MyCompany", "InventoryManagementSystem")
            settings.setValue("min_qty_threshold", self.min_qty_threshold)


    def load_settings(self):
        settings = QSettings("MyCompany", "InventoryManagementSystem")

        # Load the minimum quantity threshold setting
        self.min_qty_threshold = settings.value("min_qty_threshold", 10, type=int)

        # Load the window size setting
        self.window_size = settings.value("window_size", 7, type=int)


    def generate_sales_report(self):
        # Get the start and end dates from the user
        sales_report_dialog = StockUsedDialog(self)
        if sales_report_dialog.exec_() == QDialog.Accepted:
            start_date, end_date = sales_report_dialog.get_date_range()

            # Fetch the sales data from the database
            conn = sqlite3.connect("inventory.db")
            c = conn.cursor()
            c.execute("SELECT item_name, SUM(quantity_sold) FROM sales WHERE time_sold BETWEEN ? AND ? GROUP BY item_name", (start_date, end_date))
            sales_data = c.fetchall()
            # Close the database connection
            conn.close()

            # Create a new dialog for displaying the stock used
            dialog = QDialog(self)
            dialog.setWindowTitle("Sales Report")
            dialog.setGeometry(100, 100, 400, 400)

            # Create a table widget for the stock used
            table = QTableWidget()
            table.setColumnCount(2)
            table.setHorizontalHeaderLabels(["Item Name", "Total Quantity Used"])
            
            # Set the number of rows for the table
            table.setRowCount(len(sales_data))

            # Add the sales data to the table widget
            for row, data in enumerate(sales_data):
                name, quantity = data
                table.setItem(row, 0, QTableWidgetItem(name))
                table.setItem(row, 1, QTableWidgetItem(str(quantity)))

            # Add the table widget to the dialog
            layout = QVBoxLayout()
            layout.addWidget(table)
            dialog.setLayout(layout)

            # Show the dialog
            dialog.exec_()
        else:
            return

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = InventoryManagementSystem()
    window.show()
    sys.exit(app.exec_())
