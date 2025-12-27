import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, date
import sqlite3
from accounting import AccountingManager
from inventory import InventoryManager
from transactions import SalesManager, PurchaseManager
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import os

class AccountingSoftware:
    def __init__(self, root):
        self.root = root
        self.root.title("Accounting Software - Professional Edition")
        self.root.geometry("1400x800")
        
        # Database connection
        self.db_path = "accounting_data.db"
        self.accounting = AccountingManager(self.db_path)
        self.inventory = InventoryManager(self.db_path)
        self.sales = SalesManager(self.db_path)
        self.purchase = PurchaseManager(self.db_path)
        
        # Create main menu
        self.create_menu()
        
        # Create main container
        self.main_container = ttk.Frame(root)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create dashboard
        self.show_dashboard()
    
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Company Settings", command=self.show_company_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Backup Database", command=self.backup_database)
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Transactions Menu
        trans_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Transactions", menu=trans_menu)
        trans_menu.add_command(label="Journal Entry", command=self.show_journal_entry)
        trans_menu.add_separator()
        trans_menu.add_command(label="Sales Invoice", command=self.show_sales_invoice)
        trans_menu.add_command(label="Purchase Bill", command=self.show_purchase_bill)
        trans_menu.add_separator()
        trans_menu.add_command(label="Receive Payment", command=self.show_receive_payment)
        trans_menu.add_command(label="Make Payment", command=self.show_make_payment)
        
        # Inventory Menu
        inventory_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Inventory", menu=inventory_menu)
        inventory_menu.add_command(label="Items", command=self.show_inventory_items)
        inventory_menu.add_command(label="Locations", command=self.show_locations)
        inventory_menu.add_separator()
        inventory_menu.add_command(label="Stock Receipt", command=self.show_stock_receipt)
        inventory_menu.add_command(label="Stock Issue", command=self.show_stock_issue)
        inventory_menu.add_command(label="Stock Transfer", command=self.show_stock_transfer)
        inventory_menu.add_separator()
        inventory_menu.add_command(label="Stock by Location", command=self.show_stock_by_location)
        inventory_menu.add_command(label="Stock Valuation", command=self.show_stock_valuation)
        
        # Reports Menu
        reports_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Reports", menu=reports_menu)
        reports_menu.add_command(label="Trial Balance", command=self.show_trial_balance)
        reports_menu.add_command(label="Profit & Loss", command=self.show_profit_loss)
        reports_menu.add_command(label="Balance Sheet", command=self.show_balance_sheet)
        reports_menu.add_command(label="General Ledger", command=self.show_general_ledger)
        reports_menu.add_separator()
        reports_menu.add_command(label="Inventory Movement", command=self.show_inventory_movements)
        
        # Masters Menu
        masters_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Masters", menu=masters_menu)
        masters_menu.add_command(label="Chart of Accounts", command=self.show_chart_of_accounts)
        masters_menu.add_command(label="Customers", command=self.show_customers)
        masters_menu.add_command(label="Suppliers", command=self.show_suppliers)
        masters_menu.add_command(label="Currencies", command=self.show_currencies)
    
    def clear_main_container(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()
    
    def show_dashboard(self):
        self.clear_main_container()
        
        title = ttk.Label(self.main_container, text="Dashboard", font=("Arial", 24, "bold"))
        title.pack(pady=20)
        
        # Create dashboard panels
        panels_frame = ttk.Frame(self.main_container)
        panels_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Quick Stats
        stats_frame = ttk.LabelFrame(panels_frame, text="Quick Statistics", padding=20)
        stats_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        
        # Get some quick stats
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM sales_invoices WHERE status = "Unpaid"')
        unpaid_invoices = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM purchase_bills WHERE status = "Unpaid"')
        unpaid_bills = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(total_value) FROM inventory_stock')
        stock_value = cursor.fetchone()[0] or 0
        
        conn.close()
        
        ttk.Label(stats_frame, text=f"Unpaid Invoices: {unpaid_invoices}", 
                 font=("Arial", 12)).grid(row=0, column=0, padx=20, pady=5)
        ttk.Label(stats_frame, text=f"Unpaid Bills: {unpaid_bills}", 
                 font=("Arial", 12)).grid(row=0, column=1, padx=20, pady=5)
        ttk.Label(stats_frame, text=f"Stock Value: £{stock_value:,.2f}", 
                 font=("Arial", 12)).grid(row=0, column=2, padx=20, pady=5)
        
        # Quick Actions
        actions_frame = ttk.LabelFrame(panels_frame, text="Quick Actions", padding=20)
        actions_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        ttk.Button(actions_frame, text="New Sales Invoice", 
                  command=self.show_sales_invoice, width=25).pack(pady=5)
        ttk.Button(actions_frame, text="New Purchase Bill", 
                  command=self.show_purchase_bill, width=25).pack(pady=5)
        ttk.Button(actions_frame, text="Journal Entry", 
                  command=self.show_journal_entry, width=25).pack(pady=5)
        ttk.Button(actions_frame, text="Stock Receipt", 
                  command=self.show_stock_receipt, width=25).pack(pady=5)
        
        # Quick Reports
        reports_frame = ttk.LabelFrame(panels_frame, text="Quick Reports", padding=20)
        reports_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        
        ttk.Button(reports_frame, text="Trial Balance", 
                  command=self.show_trial_balance, width=25).pack(pady=5)
        ttk.Button(reports_frame, text="Profit & Loss", 
                  command=self.show_profit_loss, width=25).pack(pady=5)
        ttk.Button(reports_frame, text="Balance Sheet", 
                  command=self.show_balance_sheet, width=25).pack(pady=5)
        ttk.Button(reports_frame, text="Stock Valuation", 
                  command=self.show_stock_valuation, width=25).pack(pady=5)
        
        panels_frame.columnconfigure(0, weight=1)
        panels_frame.columnconfigure(1, weight=1)
    
    def show_chart_of_accounts(self):
        self.clear_main_container()
        
        title = ttk.Label(self.main_container, text="Chart of Accounts", font=("Arial", 18, "bold"))
        title.pack(pady=10)
        
        # Create treeview
        tree_frame = ttk.Frame(self.main_container)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ('Code', 'Account Name', 'Type', 'Balance')
        tree = ttk.Treeview(tree_frame, columns=columns, show='tree headings', height=25)
        
        tree.heading('#0', text='Account Structure')
        tree.heading('Code', text='Code')
        tree.heading('Account Name', text='Account Name')
        tree.heading('Type', text='Type')
        tree.heading('Balance', text='Balance (£)')
        
        tree.column('#0', width=50)
        tree.column('Code', width=100)
        tree.column('Account Name', width=300)
        tree.column('Type', width=100)
        tree.column('Balance', width=150)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load accounts
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT account_id, account_code, account_name, account_type, parent_account_id
            FROM chart_of_accounts WHERE is_active = 1
            ORDER BY account_code
        ''')
        
        accounts = cursor.fetchall()
        conn.close()
        
        # Build tree structure
        account_nodes = {}
        
        for acc in accounts:
            balance = self.accounting.get_account_balance(acc['account_id'])
            balance_str = f"{balance:,.2f}" if balance else "0.00"
            
            if acc['parent_account_id'] is None:
                node = tree.insert('', 'end', text='',
                                  values=(acc['account_code'], acc['account_name'], 
                                         acc['account_type'], balance_str))
                account_nodes[acc['account_id']] = node
            else:
                parent_node = account_nodes.get(acc['parent_account_id'], '')
                node = tree.insert(parent_node, 'end', text='',
                                  values=(acc['account_code'], acc['account_name'],
                                         acc['account_type'], balance_str))
                account_nodes[acc['account_id']] = node
    
    def show_journal_entry(self):
        self.clear_main_container()
        
        title = ttk.Label(self.main_container, text="Journal Entry", font=("Arial", 18, "bold"))
        title.pack(pady=10)
        
        # Entry form
        form_frame = ttk.Frame(self.main_container)
        form_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(form_frame, text="Date:").grid(row=0, column=0, sticky=tk.W, pady=5)
        date_entry = ttk.Entry(form_frame, width=20)
        date_entry.insert(0, date.today().isoformat())
        date_entry.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(form_frame, text="Reference:").grid(row=0, column=2, sticky=tk.W, pady=5, padx=(20, 0))
        ref_entry = ttk.Entry(form_frame, width=30)
        ref_entry.grid(row=0, column=3, sticky=tk.W, pady=5)
        
        ttk.Label(form_frame, text="Description:").grid(row=1, column=0, sticky=tk.W, pady=5)
        desc_entry = ttk.Entry(form_frame, width=80)
        desc_entry.grid(row=1, column=1, columnspan=3, sticky=tk.W, pady=5)
        
        # Lines treeview
        lines_frame = ttk.LabelFrame(self.main_container, text="Journal Lines", padding=10)
        lines_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        columns = ('Account', 'Description', 'Debit', 'Credit')
        lines_tree = ttk.Treeview(lines_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            lines_tree.heading(col, text=col)
        
        lines_tree.column('Account', width=300)
        lines_tree.column('Description', width=300)
        lines_tree.column('Debit', width=150)
        lines_tree.column('Credit', width=150)
        
        lines_tree.pack(fill=tk.BOTH, expand=True)
        
        # Line entry frame
        line_entry_frame = ttk.Frame(lines_frame)
        line_entry_frame.pack(fill=tk.X, pady=10)
        
        # Get accounts for dropdown
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT account_id, account_code, account_name FROM chart_of_accounts WHERE is_active = 1 ORDER BY account_code')
        accounts = cursor.fetchall()
        conn.close()
        
        account_options = [f"{acc['account_code']} - {acc['account_name']}" for acc in accounts]
        account_map = {f"{acc['account_code']} - {acc['account_name']}": acc['account_id'] for acc in accounts}
        
        ttk.Label(line_entry_frame, text="Account:").grid(row=0, column=0, padx=5)
        account_combo = ttk.Combobox(line_entry_frame, values=account_options, width=35)
        account_combo.grid(row=0, column=1, padx=5)
        
        ttk.Label(line_entry_frame, text="Line Desc:").grid(row=0, column=2, padx=5)
        line_desc = ttk.Entry(line_entry_frame, width=25)
        line_desc.grid(row=0, column=3, padx=5)
        
        ttk.Label(line_entry_frame, text="Debit:").grid(row=0, column=4, padx=5)
        debit_entry = ttk.Entry(line_entry_frame, width=15)
        debit_entry.insert(0, "0.00")
        debit_entry.grid(row=0, column=5, padx=5)
        
        ttk.Label(line_entry_frame, text="Credit:").grid(row=0, column=6, padx=5)
        credit_entry = ttk.Entry(line_entry_frame, width=15)
        credit_entry.insert(0, "0.00")
        credit_entry.grid(row=0, column=7, padx=5)
        
        def add_line():
            account = account_combo.get()
            desc = line_desc.get()
            debit = float(debit_entry.get())
            credit = float(credit_entry.get())
            
            if not account:
                messagebox.showerror("Error", "Please select an account")
                return
            
            lines_tree.insert('', 'end', values=(account, desc, f"{debit:.2f}", f"{credit:.2f}"))
            
            # Clear entries
            line_desc.delete(0, tk.END)
            debit_entry.delete(0, tk.END)
            debit_entry.insert(0, "0.00")
            credit_entry.delete(0, tk.END)
            credit_entry.insert(0, "0.00")
            
            # Update totals
            update_totals()
        
        ttk.Button(line_entry_frame, text="Add Line", command=add_line).grid(row=0, column=8, padx=10)
        
        # Totals frame
        totals_frame = ttk.Frame(lines_frame)
        totals_frame.pack(fill=tk.X, pady=5)
        
        total_debit_label = ttk.Label(totals_frame, text="Total Debits: £0.00", font=("Arial", 10, "bold"))
        total_debit_label.pack(side=tk.LEFT, padx=20)
        
        total_credit_label = ttk.Label(totals_frame, text="Total Credits: £0.00", font=("Arial", 10, "bold"))
        total_credit_label.pack(side=tk.LEFT, padx=20)
        
        balance_label = ttk.Label(totals_frame, text="Difference: £0.00", font=("Arial", 10, "bold"))
        balance_label.pack(side=tk.LEFT, padx=20)
        
        def update_totals():
            total_debit = 0
            total_credit = 0
            
            for item in lines_tree.get_children():
                values = lines_tree.item(item)['values']
                total_debit += float(values[2])
                total_credit += float(values[3])
            
            diff = total_debit - total_credit
            
            total_debit_label.config(text=f"Total Debits: £{total_debit:,.2f}")
            total_credit_label.config(text=f"Total Credits: £{total_credit:,.2f}")
            balance_label.config(text=f"Difference: £{diff:,.2f}",
                               foreground="red" if abs(diff) > 0.01 else "green")
        
        def save_entry():
            # Collect lines
            lines = []
            for item in lines_tree.get_children():
                values = lines_tree.item(item)['values']
                account_id = account_map[values[0]]
                lines.append((account_id, float(values[2]), float(values[3]), values[1]))
            
            if not lines:
                messagebox.showerror("Error", "Please add at least one line")
                return
            
            success, entry_num, msg = self.accounting.create_journal_entry(
                date_entry.get(), 'Manual', ref_entry.get(), desc_entry.get(),
                'GBP', 1.0, lines
            )
            
            if success:
                messagebox.showinfo("Success", f"Journal entry {entry_num} created successfully!")
                self.show_dashboard()
            else:
                messagebox.showerror("Error", msg)
        
        # Buttons
        button_frame = ttk.Frame(self.main_container)
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(button_frame, text="Save Entry", command=save_entry).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.show_dashboard).pack(side=tk.LEFT, padx=5)
    
    def show_trial_balance(self):
        self.clear_main_container()
        
        title = ttk.Label(self.main_container, text="Trial Balance", font=("Arial", 18, "bold"))
        title.pack(pady=10)
        
        # Date selection
        date_frame = ttk.Frame(self.main_container)
        date_frame.pack(fill=tk.X, padx=20, pady=5)
        
        ttk.Label(date_frame, text="As at:").pack(side=tk.LEFT, padx=5)
        date_entry = ttk.Entry(date_frame, width=15)
        date_entry.insert(0, date.today().isoformat())
        date_entry.pack(side=tk.LEFT, padx=5)
        
        def generate_report():
            trial_balance, total_dr, total_cr = self.accounting.get_trial_balance(date_entry.get())
            
            # Clear tree
            for item in tree.get_children():
                tree.delete(item)
            
            # Populate tree
            for acc in trial_balance:
                tree.insert('', 'end', values=(
                    acc['account_code'],
                    acc['account_name'],
                    f"{acc['debit_balance']:,.2f}" if acc['debit_balance'] > 0 else "",
                    f"{acc['credit_balance']:,.2f}" if acc['credit_balance'] > 0 else ""
                ))
            
            # Add totals
            tree.insert('', 'end', values=('', 'TOTAL', f"{total_dr:,.2f}", f"{total_cr:,.2f}"),
                       tags=('total',))
            tree.tag_configure('total', font=("Arial", 10, "bold"))
        
        ttk.Button(date_frame, text="Generate", command=generate_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(date_frame, text="Export to PDF", 
                  command=lambda: self.export_trial_balance_pdf(date_entry.get())).pack(side=tk.LEFT, padx=5)
        
        # Create treeview
        tree_frame = ttk.Frame(self.main_container)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        columns = ('Code', 'Account Name', 'Debit', 'Credit')
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=25)
        
        for col in columns:
            tree.heading(col, text=col)
        
        tree.column('Code', width=100)
        tree.column('Account Name', width=400)
        tree.column('Debit', width=150)
        tree.column('Credit', width=150)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Auto-generate on load
        generate_report()
    
    def show_profit_loss(self):
        self.clear_main_container()
        
        title = ttk.Label(self.main_container, text="Profit & Loss Statement", font=("Arial", 18, "bold"))
        title.pack(pady=10)
        
        # Date selection
        date_frame = ttk.Frame(self.main_container)
        date_frame.pack(fill=tk.X, padx=20, pady=5)
        
        ttk.Label(date_frame, text="From:").pack(side=tk.LEFT, padx=5)
        from_entry = ttk.Entry(date_frame, width=15)
        from_entry.insert(0, "2025-01-01")
        from_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(date_frame, text="To:").pack(side=tk.LEFT, padx=5)
        to_entry = ttk.Entry(date_frame, width=15)
        to_entry.insert(0, date.today().isoformat())
        to_entry.pack(side=tk.LEFT, padx=5)
        
        def generate_report():
            pl = self.accounting.get_profit_and_loss(from_entry.get(), to_entry.get())
            
            # Clear tree
            for item in tree.get_children():
                tree.delete(item)
            
            # Revenue
            tree.insert('', 'end', values=('REVENUE', '', ''), tags=('header',))
            for acc in pl['revenue']:
                tree.insert('', 'end', values=(acc['account_name'], f"{acc['amount']:,.2f}", ''))
            tree.insert('', 'end', values=('Total Revenue', '', f"{pl['total_revenue']:,.2f}"),
                       tags=('subtotal',))
            
            tree.insert('', 'end', values=('', '', ''))
            
            # COGS
            tree.insert('', 'end', values=('COST OF SALES', '', ''), tags=('header',))
            for acc in pl['cogs']:
                tree.insert('', 'end', values=(acc['account_name'], f"{acc['amount']:,.2f}", ''))
            tree.insert('', 'end', values=('Total Cost of Sales', '', f"{pl['total_cogs']:,.2f}"),
                       tags=('subtotal',))
            
            tree.insert('', 'end', values=('GROSS PROFIT', '', f"{pl['gross_profit']:,.2f}"),
                       tags=('total',))
            
            tree.insert('', 'end', values=('', '', ''))
            
            # Expenses
            tree.insert('', 'end', values=('OPERATING EXPENSES', '', ''), tags=('header',))
            for acc in pl['expenses']:
                tree.insert('', 'end', values=(acc['account_name'], f"{acc['amount']:,.2f}", ''))
            tree.insert('', 'end', values=('Total Expenses', '', f"{pl['total_expenses']:,.2f}"),
                       tags=('subtotal',))
            
            tree.insert('', 'end', values=('', '', ''))
            tree.insert('', 'end', values=('NET PROFIT', '', f"{pl['net_profit']:,.2f}"),
                       tags=('total',))
            
            tree.tag_configure('header', font=("Arial", 10, "bold"), background='#e0e0e0')
            tree.tag_configure('subtotal', font=("Arial", 10, "bold"))
            tree.tag_configure('total', font=("Arial", 11, "bold"), background='#d0d0d0')
        
        ttk.Button(date_frame, text="Generate", command=generate_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(date_frame, text="Export to PDF",
                  command=lambda: self.export_pl_pdf(from_entry.get(), to_entry.get())).pack(side=tk.LEFT, padx=5)
        
        # Create treeview
        tree_frame = ttk.Frame(self.main_container)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        columns = ('Account', 'Amount', 'Total')
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=25)
        
        tree.heading('Account', text='Account')
        tree.heading('Amount', text='Amount (£)')
        tree.heading('Total', text='Total (£)')
        
        tree.column('Account', width=500)
        tree.column('Amount', width=150)
        tree.column('Total', width=150)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Auto-generate
        generate_report()
    
    def show_balance_sheet(self):
        self.clear_main_container()
        
        title = ttk.Label(self.main_container, text="Balance Sheet", font=("Arial", 18, "bold"))
        title.pack(pady=10)
        
        # Date selection
        date_frame = ttk.Frame(self.main_container)
        date_frame.pack(fill=tk.X, padx=20, pady=5)
        
        ttk.Label(date_frame, text="As at:").pack(side=tk.LEFT, padx=5)
        date_entry = ttk.Entry(date_frame, width=15)
        date_entry.insert(0, date.today().isoformat())
        date_entry.pack(side=tk.LEFT, padx=5)
        
        def generate_report():
            bs = self.accounting.get_balance_sheet(date_entry.get())
            
            # Clear tree
            for item in tree.get_children():
                tree.delete(item)
            
            # Assets
            tree.insert('', 'end', values=('ASSETS', ''), tags=('header',))
            for acc in bs['assets']:
                tree.insert('', 'end', values=(acc['account_name'], f"{acc['amount']:,.2f}"))
            tree.insert('', 'end', values=('Total Assets', f"{bs['total_assets']:,.2f}"),
                       tags=('total',))
            
            tree.insert('', 'end', values=('', ''))
            
            # Liabilities
            tree.insert('', 'end', values=('LIABILITIES', ''), tags=('header',))
            for acc in bs['liabilities']:
                tree.insert('', 'end', values=(acc['account_name'], f"{acc['amount']:,.2f}"))
            tree.insert('', 'end', values=('Total Liabilities', f"{bs['total_liabilities']:,.2f}"),
                       tags=('subtotal',))
            
            tree.insert('', 'end', values=('', ''))
            
            # Equity
            tree.insert('', 'end', values=('EQUITY', ''), tags=('header',))
            for acc in bs['equity']:
                tree.insert('', 'end', values=(acc['account_name'], f"{acc['amount']:,.2f}"))
            tree.insert('', 'end', values=('Total Equity', f"{bs['total_equity']:,.2f}"),
                       tags=('subtotal',))
            
            tree.insert('', 'end', values=('', ''))
            tree.insert('', 'end', values=('TOTAL LIABILITIES & EQUITY', 
                                          f"{bs['total_liabilities_equity']:,.2f}"),
                       tags=('total',))
            
            tree.tag_configure('header', font=("Arial", 10, "bold"), background='#e0e0e0')
            tree.tag_configure('subtotal', font=("Arial", 10, "bold"))
            tree.tag_configure('total', font=("Arial", 11, "bold"), background='#d0d0d0')
        
        ttk.Button(date_frame, text="Generate", command=generate_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(date_frame, text="Export to PDF",
                  command=lambda: self.export_bs_pdf(date_entry.get())).pack(side=tk.LEFT, padx=5)
        
        # Create treeview
        tree_frame = ttk.Frame(self.main_container)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        columns = ('Account', 'Amount')
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=25)
        
        tree.heading('Account', text='Account')
        tree.heading('Amount', text='Amount (£)')
        
        tree.column('Account', width=600)
        tree.column('Amount', width=200)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Auto-generate
        generate_report()
    
    # Placeholder methods for other features
    def show_company_settings(self):
        messagebox.showinfo("Info", "Company Settings - Coming Soon")
    
    def show_sales_invoice(self):
        messagebox.showinfo("Info", "Sales Invoice Form - Coming Soon")
    
    def show_purchase_bill(self):
        messagebox.showinfo("Info", "Purchase Bill Form - Coming Soon")
    
    def show_receive_payment(self):
        messagebox.showinfo("Info", "Receive Payment - Coming Soon")
    
    def show_make_payment(self):
        messagebox.showinfo("Info", "Make Payment - Coming Soon")
    
    def show_inventory_items(self):
        messagebox.showinfo("Info", "Inventory Items - Coming Soon")
    
    def show_locations(self):
        messagebox.showinfo("Info", "Locations - Coming Soon")
    
    def show_stock_receipt(self):
        messagebox.showinfo("Info", "Stock Receipt - Coming Soon")
    
    def show_stock_issue(self):
        messagebox.showinfo("Info", "Stock Issue - Coming Soon")
    
    def show_stock_transfer(self):
        messagebox.showinfo("Info", "Stock Transfer - Coming Soon")
    
    def show_stock_by_location(self):
        messagebox.showinfo("Info", "Stock by Location - Coming Soon")
    
    def show_stock_valuation(self):
        messagebox.showinfo("Info", "Stock Valuation - Coming Soon")
    
    def show_general_ledger(self):
        messagebox.showinfo("Info", "General Ledger - Coming Soon")
    
    def show_inventory_movements(self):
        messagebox.showinfo("Info", "Inventory Movements - Coming Soon")
    
    def show_customers(self):
        messagebox.showinfo("Info", "Customers - Coming Soon")
    
    def show_suppliers(self):
        messagebox.showinfo("Info", "Suppliers - Coming Soon")
    
    def show_currencies(self):
        messagebox.showinfo("Info", "Currencies - Coming Soon")
    
    def backup_database(self):
        import shutil
        filename = filedialog.asksaveasfilename(
            defaultextension=".db",
            filetypes=[("Database files", "*.db"), ("All files", "*.*")],
            initialfile=f"accounting_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        )
        if filename:
            shutil.copy(self.db_path, filename)
            messagebox.showinfo("Success", f"Database backed up to {filename}")
    
    def export_trial_balance_pdf(self, date_to):
        messagebox.showinfo("Info", "PDF Export - Feature available in full version")
    
    def export_pl_pdf(self, date_from, date_to):
        messagebox.showinfo("Info", "PDF Export - Feature available in full version")
    
    def export_bs_pdf(self, date_to):
        messagebox.showinfo("Info", "PDF Export - Feature available in full version")


if __name__ == "__main__":
    root = tk.Tk()
    app = AccountingSoftware(root)
    root.mainloop()
