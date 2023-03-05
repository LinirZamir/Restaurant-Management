import sys
import pandas as pd
from PyQt5.QtWidgets import QSystemTrayIcon, QApplication, QMenuBar, QMenu, QAction, QMessageBox, QFileDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt, QEvent, QTimer
import sqlite3
import csv
from datetime import datetime

import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA

class InventoryManagementSystem(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Inventory Management System")
        self.setGeometry(100, 100, 600, 400)
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("icon.png"))
        self.tray_icon.show()

        # Check item quantities every minute
        self.check_quantities_timer = QTimer(self)
        self.check_quantities_timer.timeout.connect(self.check_quantities)
        self.check_quantities_timer.start(6 * 1000)

        self.setup_ui()
    
    def setup_ui(self):
        # Create widgets
        self.nav_bar = QHBoxLayout()
        self.add_item_button = QPushButton("Add Item")
        self.edit_item_button = QPushButton("Edit Item")
        self.delete_item_button = QPushButton("Delete Item")
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.item_list = QTableWidget()
        self.item_list.setColumnCount(5)
        self.item_list.setHorizontalHeaderLabels(["Item Name", "Description", "Quantity", "Price", "Modified"])
        self.item_list.setEditTriggers(QTableWidget.NoEditTriggers)
        self.item_list.setSelectionBehavior(QTableWidget.SelectRows)

        # Add widgets to layout
        self.nav_bar.addWidget(self.add_item_button)
        self.nav_bar.addWidget(self.edit_item_button)
        self.nav_bar.addWidget(self.delete_item_button)
        self.nav_bar.addStretch()
        self.nav_bar.addWidget(self.search_bar)

        # Create main layout and add widgets
        main_layout = QVBoxLayout()
        main_layout.addLayout(self.nav_bar)
        main_layout.addWidget(self.item_list)
        self.setLayout(main_layout)

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

        # Set the menu bar to the main layout
        main_layout.setMenuBar(menu_bar)

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
                self.item_list.setItem(row, column, QTableWidgetItem(str(value)))


    def check_quantities(self):
        # Use ARIMA model to predict the future quantity of each item
        conn = sqlite3.connect("inventory.db")
        c = conn.cursor()
        c.execute("SELECT name, quantity, time FROM items")
        items = c.fetchall()
        conn.close()

        for name, quantity, time in items:
            sales_data = []
            for item in items:
                if item[0] == name and item[2] != time:
                    sales_data.append([item[2], item[1]])
            sales_data = pd.DataFrame(sales_data, columns=['time', 'quantity'])
            sales_data = sales_data.set_index('time')

            if len(sales_data) < 2:
                continue

            model = ARIMA(sales_data['quantity'], order=(1,1,1))
            model_fit = model.fit(disp=0)
            future_quantity = model_fit.forecast(steps=1)
            
            if future_quantity[0][0] < 10:
                message = f"{name} quantity is low ({quantity})"
                self.tray_icon.showMessage("Low Quantity Item", message, QSystemTrayIcon.Warning, 5000)
                
    def add_item(self):
        # Create a new window for adding an item
        add_item_window = QWidget()
        add_item_window.setWindowTitle("Add Item")
        add_item_window.setGeometry(100, 100, 400, 300)

        # Create widgets for the add item window
        name_label = QLabel("Item Name:")
        name_input = QLineEdit()
        desc_label = QLabel("Description:")
        desc_input = QLineEdit()
        qty_label = QLabel("Quantity:")
        qty_input = QLineEdit()
        price_label = QLabel("Price:")
        price_input = QLineEdit()
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")

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
            self.item_list.setItem(row, 4, QTableWidgetItem(str(current_time)))

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

        # Create widgets for the edit item window
        name_label = QLabel("Item Name:")
        name_input = QLineEdit(name)
        desc_label = QLabel("Description:")
        desc_input = QLineEdit(desc)
        qty_label = QLabel("Quantity:")
        qty_input = QLineEdit(str(qty))
        price_label = QLabel("Price:")
        price_input = QLineEdit(str(price))
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")

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
            c.execute("UPDATE items SET name=?, description=?, quantity=?, price=? WHERE name=? AND description=? AND quantity=? AND price=? AND time=?",
                    (new_name, new_desc, new_qty, new_price, name, desc, qty, price, current_time))
            conn.commit()
            conn.close()

            # Update the selected item in the item list
            self.item_list.setItem(selected_row, 0, QTableWidgetItem(new_name))
            self.item_list.setItem(selected_row, 1, QTableWidgetItem(new_desc))
            self.item_list.setItem(selected_row, 2, QTableWidgetItem(str(new_qty)))
            self.item_list.setItem(selected_row, 3, QTableWidgetItem(str(new_price)))
            self.item_list.setItem(selected_row, 4, QTableWidgetItem(str(current_time)))

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

        # Import the inventory data from the CSV file
        with open(file_path, mode='r') as file:
            reader = csv.reader(file)
            next(reader) # Skip the header row
            for row in reader:
                name = row[0]
                desc = row[1]
                qty = int(row[2])
                price = float(row[3])
                time = int(row[4])
                self.add_item_to_table(name, desc, qty, price, time)

    def about(self):
        # Show a message box with information about the program
        QMessageBox.about(self, "About Inventory Manager", "This program allows you to manage your inventory.\n")


    def generate_bar_chart(self):
        # Get the names and quantities of each item in the inventory
        names = [self.item_list.item(row, 0).text() for row in range(self.item_list.rowCount())]
        quantities = [int(self.item_list.item(row, 2).text()) for row in range(self.item_list.rowCount())]

        # Create a new figure and axis for the chart
        fig, ax = plt.subplots()

        # Plot the data as a bar chart
        ax.bar(names, quantities)

        # Set the chart title and axis labels
        ax.set_title('Inventory Quantities')
        ax.set_xlabel('Item Name')
        ax.set_ylabel('Quantity')

        # Show the chart
        plt.show()                    


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = InventoryManagementSystem()
    window.show()
    sys.exit(app.exec_())
