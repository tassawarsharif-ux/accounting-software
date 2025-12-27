import sqlite3
import os
from datetime import datetime

class AccountingDatabase:
    def __init__(self, db_path="accounting_data.db"):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """Connect to the database"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            
    def initialize_database(self):
        """Create all necessary tables"""
        self.connect()
        
        # Company Settings Table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS company_settings (
                id INTEGER PRIMARY KEY,
                company_name TEXT NOT NULL,
                address TEXT,
                phone TEXT,
                email TEXT,
                tax_number TEXT,
                base_currency TEXT DEFAULT 'GBP',
                financial_year_start TEXT,
                created_date TEXT
            )
        ''')
        
        # Currency Table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS currencies (
                currency_code TEXT PRIMARY KEY,
                currency_name TEXT NOT NULL,
                symbol TEXT,
                exchange_rate REAL DEFAULT 1.0,
                last_updated TEXT
            )
        ''')
        
        # Chart of Accounts
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS chart_of_accounts (
                account_id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_code TEXT UNIQUE NOT NULL,
                account_name TEXT NOT NULL,
                account_type TEXT NOT NULL,
                parent_account_id INTEGER,
                currency TEXT DEFAULT 'GBP',
                is_active INTEGER DEFAULT 1,
                created_date TEXT,
                FOREIGN KEY (parent_account_id) REFERENCES chart_of_accounts(account_id)
            )
        ''')
        
        # Inventory Locations
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory_locations (
                location_id INTEGER PRIMARY KEY AUTOINCREMENT,
                location_code TEXT UNIQUE NOT NULL,
                location_name TEXT NOT NULL,
                address TEXT,
                is_active INTEGER DEFAULT 1,
                created_date TEXT
            )
        ''')
        
        # Inventory Items
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory_items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_code TEXT UNIQUE NOT NULL,
                item_name TEXT NOT NULL,
                description TEXT,
                unit_of_measure TEXT,
                reorder_level REAL DEFAULT 0,
                inventory_account_id INTEGER,
                cogs_account_id INTEGER,
                sales_account_id INTEGER,
                is_active INTEGER DEFAULT 1,
                created_date TEXT,
                FOREIGN KEY (inventory_account_id) REFERENCES chart_of_accounts(account_id),
                FOREIGN KEY (cogs_account_id) REFERENCES chart_of_accounts(account_id),
                FOREIGN KEY (sales_account_id) REFERENCES chart_of_accounts(account_id)
            )
        ''')
        
        # Inventory Stock (Weighted Average Tracking)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory_stock (
                stock_id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                location_id INTEGER NOT NULL,
                quantity REAL DEFAULT 0,
                weighted_avg_cost REAL DEFAULT 0,
                total_value REAL DEFAULT 0,
                last_updated TEXT,
                FOREIGN KEY (item_id) REFERENCES inventory_items(item_id),
                FOREIGN KEY (location_id) REFERENCES inventory_locations(location_id),
                UNIQUE(item_id, location_id)
            )
        ''')
        
        # Journal Entries Header
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS journal_entries (
                entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_number TEXT UNIQUE NOT NULL,
                entry_date TEXT NOT NULL,
                entry_type TEXT NOT NULL,
                reference TEXT,
                description TEXT,
                currency TEXT DEFAULT 'GBP',
                exchange_rate REAL DEFAULT 1.0,
                status TEXT DEFAULT 'Posted',
                created_by TEXT,
                created_date TEXT,
                modified_date TEXT
            )
        ''')
        
        # Journal Entry Lines (Detail)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS journal_entry_lines (
                line_id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id INTEGER NOT NULL,
                account_id INTEGER NOT NULL,
                debit_amount REAL DEFAULT 0,
                credit_amount REAL DEFAULT 0,
                debit_base_currency REAL DEFAULT 0,
                credit_base_currency REAL DEFAULT 0,
                description TEXT,
                FOREIGN KEY (entry_id) REFERENCES journal_entries(entry_id) ON DELETE CASCADE,
                FOREIGN KEY (account_id) REFERENCES chart_of_accounts(account_id)
            )
        ''')
        
        # Inventory Transactions
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory_transactions (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_number TEXT UNIQUE NOT NULL,
                transaction_date TEXT NOT NULL,
                transaction_type TEXT NOT NULL,
                item_id INTEGER NOT NULL,
                from_location_id INTEGER,
                to_location_id INTEGER,
                quantity REAL NOT NULL,
                unit_cost REAL DEFAULT 0,
                total_value REAL DEFAULT 0,
                reference TEXT,
                description TEXT,
                journal_entry_id INTEGER,
                created_date TEXT,
                FOREIGN KEY (item_id) REFERENCES inventory_items(item_id),
                FOREIGN KEY (from_location_id) REFERENCES inventory_locations(location_id),
                FOREIGN KEY (to_location_id) REFERENCES inventory_locations(location_id),
                FOREIGN KEY (journal_entry_id) REFERENCES journal_entries(entry_id)
            )
        ''')
        
        # Customers
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_code TEXT UNIQUE NOT NULL,
                customer_name TEXT NOT NULL,
                contact_person TEXT,
                email TEXT,
                phone TEXT,
                address TEXT,
                credit_limit REAL DEFAULT 0,
                currency TEXT DEFAULT 'GBP',
                receivable_account_id INTEGER,
                is_active INTEGER DEFAULT 1,
                created_date TEXT,
                FOREIGN KEY (receivable_account_id) REFERENCES chart_of_accounts(account_id)
            )
        ''')
        
        # Suppliers
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS suppliers (
                supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_code TEXT UNIQUE NOT NULL,
                supplier_name TEXT NOT NULL,
                contact_person TEXT,
                email TEXT,
                phone TEXT,
                address TEXT,
                currency TEXT DEFAULT 'GBP',
                payable_account_id INTEGER,
                is_active INTEGER DEFAULT 1,
                created_date TEXT,
                FOREIGN KEY (payable_account_id) REFERENCES chart_of_accounts(account_id)
            )
        ''')
        
        # Sales Invoices
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales_invoices (
                invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT UNIQUE NOT NULL,
                invoice_date TEXT NOT NULL,
                customer_id INTEGER NOT NULL,
                currency TEXT DEFAULT 'GBP',
                exchange_rate REAL DEFAULT 1.0,
                subtotal REAL DEFAULT 0,
                vat_amount REAL DEFAULT 0,
                total_amount REAL DEFAULT 0,
                status TEXT DEFAULT 'Unpaid',
                due_date TEXT,
                payment_terms TEXT,
                notes TEXT,
                journal_entry_id INTEGER,
                created_date TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
                FOREIGN KEY (journal_entry_id) REFERENCES journal_entries(entry_id)
            )
        ''')
        
        # Sales Invoice Lines
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales_invoice_lines (
                line_id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                item_id INTEGER,
                description TEXT,
                quantity REAL DEFAULT 0,
                unit_price REAL DEFAULT 0,
                vat_rate REAL DEFAULT 0,
                line_total REAL DEFAULT 0,
                location_id INTEGER,
                FOREIGN KEY (invoice_id) REFERENCES sales_invoices(invoice_id) ON DELETE CASCADE,
                FOREIGN KEY (item_id) REFERENCES inventory_items(item_id),
                FOREIGN KEY (location_id) REFERENCES inventory_locations(location_id)
            )
        ''')
        
        # Purchase Bills
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchase_bills (
                bill_id INTEGER PRIMARY KEY AUTOINCREMENT,
                bill_number TEXT UNIQUE NOT NULL,
                bill_date TEXT NOT NULL,
                supplier_id INTEGER NOT NULL,
                currency TEXT DEFAULT 'GBP',
                exchange_rate REAL DEFAULT 1.0,
                subtotal REAL DEFAULT 0,
                vat_amount REAL DEFAULT 0,
                total_amount REAL DEFAULT 0,
                status TEXT DEFAULT 'Unpaid',
                due_date TEXT,
                notes TEXT,
                journal_entry_id INTEGER,
                created_date TEXT,
                FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id),
                FOREIGN KEY (journal_entry_id) REFERENCES journal_entries(entry_id)
            )
        ''')
        
        # Purchase Bill Lines
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchase_bill_lines (
                line_id INTEGER PRIMARY KEY AUTOINCREMENT,
                bill_id INTEGER NOT NULL,
                item_id INTEGER,
                description TEXT,
                quantity REAL DEFAULT 0,
                unit_cost REAL DEFAULT 0,
                vat_rate REAL DEFAULT 0,
                line_total REAL DEFAULT 0,
                location_id INTEGER,
                FOREIGN KEY (bill_id) REFERENCES purchase_bills(bill_id) ON DELETE CASCADE,
                FOREIGN KEY (item_id) REFERENCES inventory_items(item_id),
                FOREIGN KEY (location_id) REFERENCES inventory_locations(location_id)
            )
        ''')
        
        # Payments
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                payment_number TEXT UNIQUE NOT NULL,
                payment_date TEXT NOT NULL,
                payment_type TEXT NOT NULL,
                party_type TEXT NOT NULL,
                party_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                currency TEXT DEFAULT 'GBP',
                exchange_rate REAL DEFAULT 1.0,
                payment_method TEXT,
                reference TEXT,
                description TEXT,
                bank_account_id INTEGER,
                journal_entry_id INTEGER,
                created_date TEXT,
                FOREIGN KEY (bank_account_id) REFERENCES chart_of_accounts(account_id),
                FOREIGN KEY (journal_entry_id) REFERENCES journal_entries(entry_id)
            )
        ''')
        
        # VAT Rates
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS vat_rates (
                vat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                vat_name TEXT NOT NULL,
                vat_rate REAL NOT NULL,
                vat_account_id INTEGER,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (vat_account_id) REFERENCES chart_of_accounts(account_id)
            )
        ''')
        
        self.conn.commit()
        print("Database initialized successfully!")
        
    def insert_default_data(self):
        """Insert default chart of accounts and currencies"""
        self.connect()
        
        # Insert default currencies
        currencies = [
            ('GBP', 'British Pound Sterling', '£', 1.0),
            ('USD', 'US Dollar', '$', 1.27),
            ('EUR', 'Euro', '€', 1.17),
            ('AED', 'UAE Dirham', 'AED', 4.67)
        ]
        
        for curr in currencies:
            try:
                self.cursor.execute('''
                    INSERT INTO currencies (currency_code, currency_name, symbol, exchange_rate, last_updated)
                    VALUES (?, ?, ?, ?, ?)
                ''', (curr[0], curr[1], curr[2], curr[3], datetime.now().isoformat()))
            except sqlite3.IntegrityError:
                pass  # Currency already exists
        
        # Insert default Chart of Accounts (UK Format)
        default_accounts = [
            # ASSETS
            ('1000', 'Assets', 'Asset', None),
            ('1100', 'Current Assets', 'Asset', '1000'),
            ('1110', 'Cash and Bank', 'Asset', '1100'),
            ('1111', 'Petty Cash', 'Asset', '1110'),
            ('1112', 'Main Bank Account', 'Asset', '1110'),
            ('1120', 'Accounts Receivable', 'Asset', '1100'),
            ('1121', 'Trade Debtors', 'Asset', '1120'),
            ('1130', 'Inventory', 'Asset', '1100'),
            ('1131', 'Stock - Finished Goods', 'Asset', '1130'),
            ('1132', 'Stock - Raw Materials', 'Asset', '1130'),
            ('1140', 'Prepayments', 'Asset', '1100'),
            ('1200', 'Fixed Assets', 'Asset', '1000'),
            ('1210', 'Property, Plant & Equipment', 'Asset', '1200'),
            ('1211', 'Office Equipment', 'Asset', '1210'),
            ('1212', 'Furniture & Fixtures', 'Asset', '1210'),
            ('1213', 'Motor Vehicles', 'Asset', '1210'),
            ('1220', 'Accumulated Depreciation', 'Asset', '1200'),
            
            # LIABILITIES
            ('2000', 'Liabilities', 'Liability', None),
            ('2100', 'Current Liabilities', 'Liability', '2000'),
            ('2110', 'Accounts Payable', 'Liability', '2100'),
            ('2111', 'Trade Creditors', 'Liability', '2110'),
            ('2120', 'VAT Payable', 'Liability', '2100'),
            ('2121', 'VAT Output', 'Liability', '2120'),
            ('2122', 'VAT Input', 'Liability', '2120'),
            ('2130', 'Accruals', 'Liability', '2100'),
            ('2200', 'Long-term Liabilities', 'Liability', '2000'),
            ('2210', 'Bank Loans', 'Liability', '2200'),
            
            # EQUITY
            ('3000', 'Equity', 'Equity', None),
            ('3100', 'Share Capital', 'Equity', '3000'),
            ('3200', 'Retained Earnings', 'Equity', '3000'),
            ('3300', 'Current Year Earnings', 'Equity', '3000'),
            
            # REVENUE
            ('4000', 'Revenue', 'Revenue', None),
            ('4100', 'Sales Revenue', 'Revenue', '4000'),
            ('4110', 'Product Sales', 'Revenue', '4100'),
            ('4120', 'Service Revenue', 'Revenue', '4100'),
            ('4200', 'Other Income', 'Revenue', '4000'),
            
            # EXPENSES
            ('5000', 'Cost of Sales', 'Expense', None),
            ('5100', 'Cost of Goods Sold', 'Expense', '5000'),
            
            ('6000', 'Operating Expenses', 'Expense', None),
            ('6100', 'Administrative Expenses', 'Expense', '6000'),
            ('6110', 'Salaries & Wages', 'Expense', '6100'),
            ('6120', 'Rent Expense', 'Expense', '6100'),
            ('6130', 'Utilities', 'Expense', '6100'),
            ('6140', 'Office Supplies', 'Expense', '6100'),
            ('6150', 'Insurance', 'Expense', '6100'),
            ('6200', 'Marketing & Advertising', 'Expense', '6000'),
            ('6300', 'Professional Fees', 'Expense', '6000'),
            ('6310', 'Accounting & Legal Fees', 'Expense', '6300'),
            ('6400', 'Depreciation Expense', 'Expense', '6000'),
            ('6500', 'Finance Costs', 'Expense', '6000'),
            ('6510', 'Bank Charges', 'Expense', '6500'),
            ('6520', 'Interest Expense', 'Expense', '6500'),
        ]
        
        for acc in default_accounts:
            # Find parent account ID if parent code is provided
            parent_id = None
            if acc[3]:
                self.cursor.execute('SELECT account_id FROM chart_of_accounts WHERE account_code = ?', (acc[3],))
                parent_result = self.cursor.fetchone()
                if parent_result:
                    parent_id = parent_result[0]
            
            try:
                self.cursor.execute('''
                    INSERT INTO chart_of_accounts 
                    (account_code, account_name, account_type, parent_account_id, created_date)
                    VALUES (?, ?, ?, ?, ?)
                ''', (acc[0], acc[1], acc[2], parent_id, datetime.now().isoformat()))
            except sqlite3.IntegrityError:
                pass  # Account already exists
        
        # Insert default VAT rates (UK)
        vat_rates = [
            ('Standard Rate (20%)', 20.0),
            ('Reduced Rate (5%)', 5.0),
            ('Zero Rate (0%)', 0.0),
            ('Exempt', 0.0)
        ]
        
        # Get VAT Output account ID
        self.cursor.execute('SELECT account_id FROM chart_of_accounts WHERE account_code = ?', ('2121',))
        vat_account = self.cursor.fetchone()
        vat_account_id = vat_account[0] if vat_account else None
        
        for vat in vat_rates:
            try:
                self.cursor.execute('''
                    INSERT INTO vat_rates (vat_name, vat_rate, vat_account_id)
                    VALUES (?, ?, ?)
                ''', (vat[0], vat[1], vat_account_id))
            except sqlite3.IntegrityError:
                pass
        
        # Insert default company settings
        try:
            self.cursor.execute('''
                INSERT INTO company_settings 
                (company_name, base_currency, financial_year_start, created_date)
                VALUES (?, ?, ?, ?)
            ''', ('My Company Ltd', 'GBP', '2025-04-01', datetime.now().isoformat()))
        except sqlite3.IntegrityError:
            pass
        
        self.conn.commit()
        print("Default data inserted successfully!")
        self.close()


if __name__ == "__main__":
    # Initialize database
    db = AccountingDatabase()
    db.initialize_database()
    db.insert_default_data()
    print("\nAccounting database created successfully!")
    print("Database file: accounting_data.db")
