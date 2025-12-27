import sqlite3
from datetime import datetime, timedelta
from inventory import InventoryManager
from accounting import AccountingManager
from transactions import SalesManager, PurchaseManager

def add_sample_data():
    db_path = "accounting_data.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Adding sample data...")
    
    # Add Customers
    print("Adding customers...")
    customers = [
        ('CUST001', 'ABC Trading Ltd', 'John Smith', 'john@abctrading.co.uk', '020 1234 5678', 
         '123 High Street, London, UK', 10000, 'GBP'),
        ('CUST002', 'XYZ Corporation', 'Sarah Jones', 'sarah@xyzcorp.com', '020 8765 4321',
         '456 Park Lane, Manchester, UK', 15000, 'GBP'),
        ('CUST003', 'Global Imports Inc', 'Ahmed Ali', 'ahmed@globalimports.ae', '+971 4 123 4567',
         'Dubai Silicon Oasis, Dubai, UAE', 20000, 'AED'),
    ]
    
    # Get receivable account
    cursor.execute('SELECT account_id FROM chart_of_accounts WHERE account_code = ?', ('1121',))
    receivable_account = cursor.fetchone()[0]
    
    for cust in customers:
        try:
            cursor.execute('''
                INSERT INTO customers
                (customer_code, customer_name, contact_person, email, phone, address,
                 credit_limit, currency, receivable_account_id, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (*cust, receivable_account, datetime.now().isoformat()))
        except sqlite3.IntegrityError:
            pass
    
    # Add Suppliers
    print("Adding suppliers...")
    suppliers = [
        ('SUPP001', 'Wholesale Direct Ltd', 'Tom Brown', 'tom@wholesaledirect.co.uk', 
         '0161 234 5678', '789 Trade Park, Birmingham, UK', 'GBP'),
        ('SUPP002', 'Import Masters PLC', 'Lisa Green', 'lisa@importmasters.co.uk',
         '0113 876 5432', '321 Industrial Estate, Leeds, UK', 'GBP'),
        ('SUPP003', 'Middle East Suppliers', 'Khalid Hassan', 'khalid@mesuppliers.ae',
         '+971 2 987 6543', 'Abu Dhabi Industrial City, UAE', 'AED'),
    ]
    
    # Get payable account
    cursor.execute('SELECT account_id FROM chart_of_accounts WHERE account_code = ?', ('2111',))
    payable_account = cursor.fetchone()[0]
    
    for supp in suppliers:
        try:
            cursor.execute('''
                INSERT INTO suppliers
                (supplier_code, supplier_name, contact_person, email, phone, address,
                 currency, payable_account_id, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (*supp, payable_account, datetime.now().isoformat()))
        except sqlite3.IntegrityError:
            pass
    
    # Add Inventory Locations
    print("Adding inventory locations...")
    locations = [
        ('WH-LONDON', 'London Warehouse', '100 Storage Street, London, UK'),
        ('WH-MANC', 'Manchester Warehouse', '200 Industrial Road, Manchester, UK'),
        ('SHOP-01', 'Retail Shop - High Street', '50 High Street, London, UK'),
    ]
    
    for loc in locations:
        try:
            cursor.execute('''
                INSERT INTO inventory_locations 
                (location_code, location_name, address, created_date)
                VALUES (?, ?, ?, ?)
            ''', (loc[0], loc[1], loc[2], datetime.now().isoformat()))
        except sqlite3.IntegrityError:
            pass
    
    inventory = InventoryManager(db_path)
    
    # Get location IDs
    cursor.execute('SELECT location_id FROM inventory_locations WHERE location_code = ?', ('WH-LONDON',))
    london_location = cursor.fetchone()[0]
    
    cursor.execute('SELECT location_id FROM inventory_locations WHERE location_code = ?', ('WH-MANC',))
    manc_location = cursor.fetchone()[0]
    
    # Get accounts for inventory
    cursor.execute('SELECT account_id FROM chart_of_accounts WHERE account_code = ?', ('1131',))
    inventory_account = cursor.fetchone()[0]
    
    cursor.execute('SELECT account_id FROM chart_of_accounts WHERE account_code = ?', ('5100',))
    cogs_account = cursor.fetchone()[0]
    
    cursor.execute('SELECT account_id FROM chart_of_accounts WHERE account_code = ?', ('4110',))
    sales_account = cursor.fetchone()[0]
    
    # Add Inventory Items
    print("Adding inventory items...")
    items = [
        ('PROD-001', 'Laptop Computer', 'High-performance business laptop', 'Each', 5,
         inventory_account, cogs_account, sales_account),
        ('PROD-002', 'Wireless Mouse', 'Ergonomic wireless mouse', 'Each', 20,
         inventory_account, cogs_account, sales_account),
        ('PROD-003', 'USB-C Hub', 'Multi-port USB-C hub', 'Each', 15,
         inventory_account, cogs_account, sales_account),
        ('PROD-004', 'Monitor 24"', '24-inch Full HD monitor', 'Each', 10,
         inventory_account, cogs_account, sales_account),
        ('PROD-005', 'Keyboard Mechanical', 'Mechanical gaming keyboard', 'Each', 12,
         inventory_account, cogs_account, sales_account),
    ]
    
    item_ids = {}
    for item in items:
        try:
            cursor.execute('''
                INSERT INTO inventory_items 
                (item_code, item_name, description, unit_of_measure, reorder_level,
                 inventory_account_id, cogs_account_id, sales_account_id, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (*item, datetime.now().isoformat()))
            item_ids[item[0]] = cursor.lastrowid
        except sqlite3.IntegrityError:
            cursor.execute('SELECT item_id FROM inventory_items WHERE item_code = ?', (item[0],))
            item_ids[item[0]] = cursor.fetchone()[0]
    
    conn.commit()
    
    # Add some stock receipts
    print("Adding stock receipts...")
    stock_receipts = [
        (item_ids['PROD-001'], london_location, 10, 500.00, 'PO-001', 'Initial purchase'),
        (item_ids['PROD-002'], london_location, 50, 15.00, 'PO-001', 'Initial purchase'),
        (item_ids['PROD-003'], london_location, 30, 25.00, 'PO-002', 'Initial purchase'),
        (item_ids['PROD-004'], london_location, 15, 120.00, 'PO-003', 'Initial purchase'),
        (item_ids['PROD-005'], manc_location, 20, 75.00, 'PO-004', 'Initial purchase'),
        (item_ids['PROD-001'], manc_location, 8, 500.00, 'PO-005', 'Stock replenishment'),
    ]
    
    for receipt in stock_receipts:
        inventory.stock_receipt(*receipt)
    
    # Add some manual journal entries
    print("Adding sample journal entries...")
    accounting = AccountingManager(db_path)
    
    # Opening capital entry
    cursor.execute('SELECT account_id FROM chart_of_accounts WHERE account_code = ?', ('1112',))
    bank_account = cursor.fetchone()[0]
    
    cursor.execute('SELECT account_id FROM chart_of_accounts WHERE account_code = ?', ('3100',))
    capital_account = cursor.fetchone()[0]
    
    accounting.create_journal_entry(
        '2025-01-01', 'Opening Balance', 'OB-001', 'Opening capital investment',
        'GBP', 1.0, [
            (bank_account, 50000, 0, 'Cash deposited'),
            (capital_account, 0, 50000, 'Share capital')
        ]
    )
    
    # Office rent payment
    cursor.execute('SELECT account_id FROM chart_of_accounts WHERE account_code = ?', ('6120',))
    rent_account = cursor.fetchone()[0]
    
    accounting.create_journal_entry(
        (datetime.now() - timedelta(days=15)).date().isoformat(), 
        'Payment', 'RENT-JAN', 'January office rent',
        'GBP', 1.0, [
            (rent_account, 2000, 0, 'Office rent - January'),
            (bank_account, 0, 2000, 'Payment from bank')
        ]
    )
    
    # Utilities payment
    cursor.execute('SELECT account_id FROM chart_of_accounts WHERE account_code = ?', ('6130',))
    utilities_account = cursor.fetchone()[0]
    
    accounting.create_journal_entry(
        (datetime.now() - timedelta(days=10)).date().isoformat(),
        'Payment', 'UTIL-JAN', 'Utilities payment',
        'GBP', 1.0, [
            (utilities_account, 350, 0, 'Electricity and water'),
            (bank_account, 0, 350, 'Payment from bank')
        ]
    )
    
    # Salary payment
    cursor.execute('SELECT account_id FROM chart_of_accounts WHERE account_code = ?', ('6110',))
    salary_account = cursor.fetchone()[0]
    
    accounting.create_journal_entry(
        (datetime.now() - timedelta(days=5)).date().isoformat(),
        'Payment', 'SAL-DEC', 'December salaries',
        'GBP', 1.0, [
            (salary_account, 8000, 0, 'Staff salaries - December'),
            (bank_account, 0, 8000, 'Payment from bank')
        ]
    )
    
    conn.commit()
    conn.close()
    
    print("\nSample data added successfully!")
    print("\nSummary:")
    print("- 3 Customers added")
    print("- 3 Suppliers added")
    print("- 3 Inventory locations added")
    print("- 5 Inventory items added")
    print("- 6 Stock receipts created")
    print("- 4 Journal entries posted")
    print("\nYou can now test the software with this sample data!")

if __name__ == "__main__":
    add_sample_data()
