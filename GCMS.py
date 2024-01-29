import random
import tkinter as tk
from tkinter import messagebox
import json
import sqlite3
# Dealer Module


class DealerModule:
    def __init__(self, dealer_id, name, contact_info, address):
        self.dealer_id = dealer_id
        self.name = name
        self.contact_info = contact_info
        self.address = address
        self.order_list = []
        self.return_schedule = None  # Initialize return_schedule as None
        self.cylinder_inventory = []
        self.check_schedule = None

    def get_details(self):
        print(f"Dealer ID: {self.dealer_id}")
        print(f"Name: {self.name}")
        print(f"Contact Information: {self.contact_info}")
        print(f"Address: {self.address}")

    def update_contact_info(self, new_contact_info):
        self.contact_info = new_contact_info

    def view_available_cylinders(self):
        available_cylinders = [
            cylinder for cylinder in self.cylinder_inventory if cylinder.status == "Available"]
        if available_cylinders:
            print("Available Cylinders:")
            for cylinder in available_cylinders:
                cylinder.get_details()
        else:
            print("No available cylinders found.")

    def place_cylinder_order(self, cylinder_type, quantity):
        print(f"Placing an order for {quantity} {cylinder_type} cylinders...")
        available_cylinders = [cylinder for cylinder in self.cylinder_inventory if
                               cylinder.status == "Available" and cylinder.cylinder_type == cylinder_type]

        if available_cylinders:
            if len(available_cylinders) >= quantity:
                order = Order(len(self.order_list) + 1,
                              self.dealer_id, cylinder_type, quantity)
                order.confirm()
                self.order_list.append(order)

                for i in range(quantity):
                    available_cylinders[i].status = "Ordered"

                print(f"Order placed successfully. Order ID: {order.order_id}")
            else:
                print(f"Insufficient {cylinder_type} cylinders available.")
        else:
            print(f"No {cylinder_type} cylinders available for order.")
        order_info = {
            "order_id": order.order_id,
            "dealer_id": self.dealer_id,
            "cylinder_type": cylinder_type,
            "quantity": quantity,
            "status": order.status
        }
        self.save_order_info(order_info)
        #

    def save_order_info(self, order_info):
        conn = sqlite3.connect("gas_cylinder_management.db")
        c = conn.cursor()

        c.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY,
                dealer_id INTEGER,
                cylinder_type TEXT,
                quantity INTEGER,
                status TEXT
            )
        ''')

        c.execute('''
            INSERT INTO orders (dealer_id, cylinder_type, quantity, status)
            VALUES (?, ?, ?, ?)
        ''', (order_info["dealer_id"], order_info["cylinder_type"], order_info["quantity"], order_info["status"]))

        conn.commit()
        conn.close()
        #

    def load_orders(self):
        conn = sqlite3.connect("gas_cylinder_management.db")
        c = conn.cursor()

        c.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY,
                dealer_id INTEGER,
                cylinder_type TEXT,
                quantity INTEGER,
                status TEXT
            )
        ''')

        c.execute('''
            SELECT * FROM orders
        ''')

        orders = []
        for row in c.fetchall():
            order = {
                "order_id": row[0],
                "dealer_id": row[1],
                "cylinder_type": row[2],
                "quantity": row[3],
                "status": row[4]
            }
            orders.append(order)

        conn.close()
        return orders

    def view_order_status(self):
        print("Viewing order status...")
        if not self.order_list:
            print("No orders placed yet.")
        else:
            print("Order Status:")
            for order in self.order_list:
                order.view_details()

    def cancel_order(self, order_id):
        for order in self.order_list:
            if order.order_id == order_id:
                if order.status == "Confirmed":
                    order.cancel()
                    print(f"Order {order_id} has been cancelled.")
                    # Update the order status in secondary storage
                    self.update_order_status(order_id, "Cancelled")
                else:
                    print(
                        f"Order {order_id} cannot be cancelled as it is {order.status}.")
                return
        print(f"Order {order_id} not found in the order list.")

    def update_order_status(self, order_id, new_status):
        # Read existing orders from the file
        orders = []
        with open("order_history.json", "r") as file:
            for line in file:
                order_data = json.loads(line)
                orders.append(order_data)

        # Update the status of the specified order
        for order in orders:
            if order["order_id"] == order_id:
                order["status"] = new_status

        # Write the updated orders back to the file
        with open("order_history.json", "w") as file:
            for order in orders:
                json.dump(order, file)
                file.write("\n")

    def schedule_return(self, cylinders, return_date):
        print("Scheduling cylinder return...")

        if not self.return_schedule:
            self.return_schedule = Schedule(
                len(self.return_schedule) + 1, self.dealer_id, return_date, cylinders)
            self.return_schedule.confirm()

            for cylinder in cylinders:
                cylinder.schedule_check(return_date)

            print(f"Cylinder return scheduled for {return_date}.")
        else:
            print(
                "You have an existing scheduled return. Please cancel it before scheduling a new one.")

    def view_account_information(self):
        print("Viewing account information...")
        print(f"Dealer ID: {self.dealer_id}")
        print(f"Name: {self.name}")
        print(f"Contact Information: {self.contact_info}")
        print(f"Address: {self.address}")

    def mark_cylinder_as_damaged(self, cylinder_id):
        print("Marking a cylinder as damaged...")
        for cylinder in self.cylinder_inventory:
            if cylinder.cylinder_id == cylinder_id:
                if cylinder.status == "Available":
                    cylinder.mark_as_damaged()
                    print(
                        f"Cylinder {cylinder_id} has been marked as damaged.")
                elif cylinder.status == "Ordered":
                    print(
                        f"Cylinder {cylinder_id} is currently ordered and cannot be marked as damaged.")
                else:
                    print(
                        f"Cylinder {cylinder_id} is already marked as damaged.")
                return
        print(f"Cylinder {cylinder_id} not found in the inventory.")

    def replace_cylinder(self, cylinder_id):
        print("Replacing a cylinder...")
        for cylinder in self.cylinder_inventory:
            if cylinder.cylinder_id == cylinder_id:
                if cylinder.status == "Damaged":
                    cylinder.replace()
                    print(
                        f"Cylinder {cylinder_id} has been replaced and is now available.")
                elif cylinder.status == "Ordered":
                    print(
                        f"Cylinder {cylinder_id} is currently ordered and cannot be replaced.")
                elif cylinder.status == "Available":
                    print(
                        f"Cylinder {cylinder_id} is already available and does not need replacement.")
                return
        print(f"Cylinder {cylinder_id} not found in the inventory.")


# Cylinder
class Cylinder:
    def __init__(self, cylinder_id, cylinder_type, capacity, status):
        self.cylinder_id = cylinder_id
        self.cylinder_type = cylinder_type
        self.capacity = capacity
        self.status = status
        self.check_schedule = None

    def get_details(self):
        print(f"Cylinder ID: {self.cylinder_id}")
        print(f"Type: {self.cylinder_type}")
        print(f"Capacity: {self.capacity} liters")
        print(f"Status: {self.status}")
        if self.check_schedule:
            print(f"Next Check Date: {self.check_schedule.scheduled_date}")
        print()

    def schedule_check(self, check_date):
        if self.status == "Available" or self.status == "Ordered":
            if not self.check_schedule:
                self.check_schedule = CheckSchedule(
                    self.cylinder_id, check_date)
                print(
                    f"Check scheduled for Cylinder {self.cylinder_id} on {check_date}.")
            else:
                print(
                    f"Check for Cylinder {self.cylinder_id} is already scheduled for {self.check_schedule.scheduled_date}.")
        else:
            print(
                f"Cylinder {self.cylinder_id} is not available for a check at the moment.")

    def mark_as_damaged(self):
        self.status = "Damaged"

    def replace(self):
        self.status = "Available"


# Order
class Order:
    def __init__(self, order_id, dealer_id, cylinder_type, quantity):
        self.order_id = order_id
        self.dealer_id = dealer_id
        self.cylinder_type = cylinder_type
        self.quantity = quantity
        self.status = "Pending"

    def view_details(self):
        print(f"Order ID: {self.order_id}")
        print(f"Dealer ID: {self.dealer_id}")
        print(f"Cylinder Type: {self.cylinder_type}")
        print(f"Quantity: {self.quantity}")
        print(f"Status: {self.status}")
        print()

    def confirm(self):
        if self.status == "Pending":
            self.status = "Confirmed"
            print(f"Order {self.order_id} has been confirmed.")
        else:
            print(
                f"Order {self.order_id} is already {self.status}. Cannot confirm again.")

    def cancel(self):
        if self.status == "Confirmed":
            self.status = "Cancelled"
            print(f"Order {self.order_id} has been cancelled.")
        else:
            print(
                f"Order {self.order_id} cannot be cancelled as it is {self.status}.")


# Schedule
class Schedule:
    def __init__(self, schedule_id, dealer_id, scheduled_date, cylinders):
        self.schedule_id = schedule_id
        self.dealer_id = dealer_id
        self.scheduled_date = scheduled_date
        self.cylinders = cylinders
        self.status = "Scheduled"

    def view_details(self):
        print(f"Schedule ID: {self.schedule_id}")
        print(f"Dealer ID: {self.dealer_id}")
        print(f"Scheduled Date: {self.scheduled_date}")
        print(f"Status: {self.status}")
        print("Cylinders to return:")
        for cylinder in self.cylinders:
            print(f"Cylinder ID: {cylinder.cylinder_id}")
        print()

    def confirm(self):
        print("Confirming the schedule...")
        self.status = "Confirmed"

    def cancel(self):
        print("Cancelling the schedule...")
        self.status = "Cancelled"


# ReturnSchedule
class ReturnSchedule:
    def __init__(self, dealer_id, return_date, cylinders_to_return):
        self.dealer_id = dealer_id
        self.return_date = return_date
        self.cylinders_to_return = cylinders_to_return
        self.status = "Pending"

    def confirm(self):
        if self.status == "Pending":
            self.status = "Confirmed"

    def cancel(self):
        if self.status == "Pending":
            self.status = "Cancelled"


# GUI Class
class DealerModuleGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Gas Cylinder Management System")
        self.dealer = DealerModule(
            1, "Dealer_name", "Dealer_name@example.com", "123 Jaipur")
        self.create_gui()
        self.load_orders()

    def load_orders(self):
        orders = self.dealer.load_orders()
        for order_data in orders:
            order = Order(
                order_data["order_id"],
                order_data["dealer_id"],
                order_data["cylinder_type"],
                order_data["quantity"]
            )
            order.status = order_data["status"]
            self.dealer.order_list.append(order)

    def save_order(self, order):
        order_info = {
            "order_id": order.order_id,
            "dealer_id": order.dealer_id,
            "cylinder_type": order.cylinder_type,
            "quantity": order.quantity,
            "status": order.status
        }
        self.dealer.save_order_info(order_info)

    def create_gui(self):
        label = tk.Label(
            self.root, text="Welcome, Dealer: " + self.dealer.name)
        label.pack()

        # Increase button size and add spacing
        button_options = {'font': ('Helvetica', 12), 'padx': 10, 'pady': 5}

        order_button = tk.Button(
            self.root, text="Place Cylinder Order", command=self.place_order, **button_options)
        order_button.pack()

        view_orders_button = tk.Button(
            self.root, text="View Orders", command=self.view_orders, **button_options)
        view_orders_button.pack()

        schedule_return_button = tk.Button(
            self.root, text="Schedule Return", command=self.schedule_return, **button_options)
        schedule_return_button.pack()

        view_returns_button = tk.Button(
            self.root, text="View Scheduled Returns", command=self.view_scheduled_returns, **button_options)
        view_returns_button.pack()

        view_account_button = tk.Button(
            self.root, text="View Account Information", command=self.view_account, **button_options)
        view_account_button.pack()

        update_account_button = tk.Button(
            self.root, text="Update Account Information", command=self.update_account, **button_options)
        update_account_button.pack()

    def update_account(self):
        update_window = tk.Toplevel(self.root)
        update_window.title("Update Account Information")

        # Create entry widgets for updating account details
        name_label = tk.Label(update_window, text="New Name:")
        name_label.pack()
        name_entry = tk.Entry(update_window)
        name_entry.insert(tk.END, self.dealer.name)
        name_entry.pack()

        contact_label = tk.Label(
            update_window, text="New Contact Information:")
        contact_label.pack()
        contact_entry = tk.Entry(update_window)
        contact_entry.insert(tk.END, self.dealer.contact_info)
        contact_entry.pack()

        address_label = tk.Label(update_window, text="New Address:")
        address_label.pack()
        address_entry = tk.Entry(update_window)
        address_entry.insert(tk.END, self.dealer.address)
        address_entry.pack()

        # Button to confirm the updates
        confirm_button = tk.Button(update_window, text="Confirm Update",
                                   command=lambda: self.confirm_update(name_entry.get(),
                                                                       contact_entry.get(),
                                                                       address_entry.get(), update_window))
        confirm_button.pack()

    def confirm_update(self, new_name, new_contact, new_address, update_window):
        if not new_name or not new_contact or not new_address:
            messagebox.showerror(
                "Error", "Please enter all the details for update.")
        else:
            # Update the dealer object
            self.dealer.name = new_name
            self.dealer.update_contact_info(new_contact)
            self.dealer.address = new_address

            # Display a success message
            messagebox.showinfo(
                "Success", "Account information updated successfully.")
            # Close the update window
            update_window.destroy()
            # Update the displayed account information
            self.view_account()

    def place_order(self):
        order_window = tk.Toplevel(self.root)
        order_window.title("Place Cylinder Order")
        cylinder_type_label = tk.Label(order_window, text="Cylinder Type:")
        cylinder_type_label.pack()
        cylinder_type_entry = tk.Entry(order_window)
        cylinder_type_entry.pack()
        quantity_label = tk.Label(order_window, text="Quantity:")
        quantity_label.pack()
        quantity_entry = tk.Entry(order_window)
        quantity_entry.pack()
        confirm_button = tk.Button(order_window, text="Confirm Order",
                                   command=lambda: self.confirm_order(cylinder_type_entry.get(),
                                                                      quantity_entry.get(), order_window))
        confirm_button.pack()

    def confirm_order(self, cylinder_type, quantity, order_window):
        if not cylinder_type or not quantity:
            messagebox.showerror(
                "Error", "Please enter both cylinder type and quantity.")
        else:
            order = Order(len(self.dealer.order_list) + 1,
                          self.dealer.dealer_id, cylinder_type, int(quantity))
            order.confirm()
            self.dealer.order_list.append(order)
            self.save_order(order)
            messagebox.showinfo("Success", "Order placed successfully.")
            order_window.destroy()

    def view_orders(self):
        orders_window = tk.Toplevel(self.root)
        orders_window.title("View Orders")
        orders_label = tk.Label(orders_window, text="Your Orders:")
        orders_label.pack()
        orders_text = tk.Text(orders_window, wrap=tk.WORD)
        orders_text.pack()

        for order in self.dealer.order_list:
            order_text = f"Order ID: {order.order_id}\nCylinder Type: {order.cylinder_type}\nQuantity: {order.quantity}\nStatus: {order.status}\n\n"
            orders_text.insert(tk.END, order_text)

            # Add a "Cancel Order" button for each order
            cancel_button = tk.Button(orders_window, text="Cancel Order",
                                      command=lambda order_id=order.order_id: self.cancel_order(order_id, orders_window))
            orders_text.window_create(tk.END, window=cancel_button)
            orders_text.insert(tk.END, "\n")

    def delete_order_from_database(self, order_id):
        conn = sqlite3.connect("gas_cylinder_management.db")
        c = conn.cursor()

        c.execute('DELETE FROM orders WHERE order_id = ?', (order_id,))

        conn.commit()
        conn.close()

    def cancel_order(self, order_id, orders_window):
        found_order = None
        for order in self.dealer.order_list:
            if order.order_id == order_id:
                found_order = order
                break

        if found_order:
            if found_order.status == "Confirmed":
                found_order.cancel()
                print(f"Order {order_id} has been cancelled.")
                # Delete the cancelled order from the database
                self.delete_order_from_database(order_id)
                # Update the order status in the GUI
                orders_window.destroy()
                self.view_orders()
                messagebox.showinfo(
                    "Success", f"Order {order_id} has been cancelled.")
            else:
                print(
                    f"Order {order_id} cannot be cancelled as it is {found_order.status}.")
        else:
            print(f"Order {order_id} not found.")

    def update_order_status(self, order_id, new_status):
        # Read existing orders from the file if it exists
        try:
            with open("order_history.json", "r") as file:
                orders = [json.loads(line) for line in file]
        except FileNotFoundError:
            # If the file doesn't exist, create an empty list
            orders = []

        # Update the status of the specified order
        for order in orders:
            if order["order_id"] == order_id:
                order["status"] = new_status

        # Write the updated orders back to the file
        with open("order_history.json", "w") as file:
            for order in orders:
                json.dump(order, file)
                file.write("\n")

    def schedule_return(self):
        return_window = tk.Toplevel(self.root)
        return_window.title("Schedule Cylinder Return")
        return_date_label = tk.Label(
            return_window, text="Return Date (YYYY-MM-DD):")
        return_date_label.pack()
        return_date_entry = tk.Entry(return_window)
        return_date_entry.pack()
        confirm_return_button = tk.Button(return_window, text="Confirm Return Schedule",
                                          command=lambda: self.confirm_return(return_window, return_date_entry.get()))
        confirm_return_button.pack()

    def view_scheduled_returns(self):
        returns_window = tk.Toplevel(self.root)
        returns_window.title("View Scheduled Returns")
        returns_label = tk.Label(returns_window, text="Scheduled Returns:")
        returns_label.pack()
        returns_text = tk.Text(returns_window, wrap=tk.WORD)
        returns_text.pack()

        if self.dealer.return_schedule:
            return_text = f"Return Date: {self.dealer.return_schedule.return_date}\n"
            returns_text.insert(tk.END, return_text)

            # Add a "Cancel Return" button
            cancel_return_button = tk.Button(returns_window, text="Cancel Return",
                                             command=self.cancel_return)
            cancel_return_button.pack()
        else:
            returns_text.insert(tk.END, "No scheduled returns.")

    def cancel_return(self):
        self.dealer.return_schedule.cancel()
        messagebox.showinfo("Success", "Scheduled return has been cancelled.")

    def confirm_return(self, return_window, return_date):
        if not return_date:
            messagebox.showerror("Error", "Please enter the return date.")
        else:
            return_cylinders = [cylinder for cylinder in self.dealer.cylinder_inventory if
                                cylinder.status == "Available"]
            return_schedule = ReturnSchedule(
                self.dealer.dealer_id, return_date, return_cylinders)
            self.dealer.return_schedule = return_schedule
            messagebox.showinfo("Success", "Return scheduled successfully.")
            return_window.destroy()

    def view_account(self):
        account_window = tk.Toplevel(self.root)
        account_window.title("Account Information")
        account_label = tk.Label(
            account_window, text="Your Account Information:")
        account_label.pack()
        account_text = tk.Text(account_window, wrap=tk.WORD)
        account_text.pack()
        account_text.insert(tk.END, f"Dealer Name: {self.dealer.name}\n")
        account_text.insert(tk.END, f"Dealer ID: {self.dealer.dealer_id}\n")
        account_text.insert(
            tk.END, f"Contact Info: {self.dealer.contact_info}\n")
        account_text.insert(tk.END, f"Address: {self.dealer.address}\n")
        account_text.config(state=tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk()
    app = DealerModuleGUI(root)
    root.mainloop()