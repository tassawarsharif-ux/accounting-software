import sqlite3
from datetime import datetime
from accounting import AccountingManager
from inventory import InventoryManager

class SalesManager:
    def __init__(self, db_path="accounting_data.db"):
        self.db_path = db_path
        self.accounting = AccountingManager(db_path)
        self.inventory = InventoryManager(db_path)
        
    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def create_sales_invoice(self, customer_id, invoice_date, due_date, currency, exchange_rate, 
                            payment_terms, notes, lines):
        """
        Create sales invoice with automatic journal posting
        lines = [(item_id, description, quantity, unit_price, vat_rate, location_id), ...]
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            # Calculate totals
            subtotal = 0
            vat_amount = 0
            
            for line in lines:
                item_id, description, quantity, unit_price, vat_rate, location_id = line
                line_total = quantity * unit_price
                line_vat = line_total * (vat_rate / 100)
                subtotal += line_total
                vat_amount += line_vat
            
            total_amount = subtotal + vat_amount
            
            # Generate invoice number
            cursor.execute('SELECT COUNT(*) as count FROM sales_invoices')
            count = cursor.fetchone()['count']
            invoice_number = f"INV-{count + 1:06d}"
            
            # Get customer details
            cursor.execute('SELECT receivable_account_id FROM customers WHERE customer_id = ?', (customer_id,))
            customer = cursor.fetchone()
            receivable_account = customer['receivable_account_id']
            
            # Get revenue and VAT accounts
            cursor.execute('SELECT account_id FROM chart_of_accounts WHERE account_code = ?', ('4110',))
            revenue_account = cursor.fetchone()['account_id']
            
            cursor.execute('SELECT account_id FROM chart_of_accounts WHERE account_code = ?', ('2121',))
            vat_account = cursor.fetchone()['account_id']
            
            # Create journal entry
            journal_lines = [
                (receivable_account, total_amount * exchange_rate, 0, f"Sales Invoice {invoice_number}"),
                (revenue_account, 0, subtotal * exchange_rate, f"Sales Revenue - {invoice_number}"),
            ]
            
            if vat_amount > 0:
                journal_lines.append(
                    (vat_account, 0, vat_amount * exchange_rate, f"VAT on Sales - {invoice_number}")
                )
            
            success, entry_number, msg = self.accounting.create_journal_entry(
                invoice_date, 'Sales Invoice', invoice_number, 
                f"Sales Invoice to Customer", currency, exchange_rate, journal_lines
            )
            
            if not success:
                raise Exception(f"Failed to create journal entry: {msg}")
            
            # Get journal entry ID
            cursor.execute('SELECT entry_id FROM journal_entries WHERE entry_number = ?', (entry_number,))
            journal_entry_id = cursor.fetchone()['entry_id']
            
            # Insert sales invoice
            cursor.execute('''
                INSERT INTO sales_invoices
                (invoice_number, invoice_date, customer_id, currency, exchange_rate,
                 subtotal, vat_amount, total_amount, status, due_date, payment_terms,
                 notes, journal_entry_id, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (invoice_number, invoice_date, customer_id, currency, exchange_rate,
                  subtotal, vat_amount, total_amount, 'Unpaid', due_date, payment_terms,
                  notes, journal_entry_id, datetime.now().isoformat()))
            
            invoice_id = cursor.lastrowid
            
            # Insert invoice lines and issue stock
            cursor.execute('SELECT account_id FROM chart_of_accounts WHERE account_code = ?', ('5100',))
            cogs_account = cursor.fetchone()['account_id']
            
            cursor.execute('SELECT account_id FROM chart_of_accounts WHERE account_code = ?', ('1131',))
            inventory_account = cursor.fetchone()['account_id']
            
            for line in lines:
                item_id, description, quantity, unit_price, vat_rate, location_id = line
                line_total = quantity * unit_price
                
                cursor.execute('''
                    INSERT INTO sales_invoice_lines
                    (invoice_id, item_id, description, quantity, unit_price, vat_rate, 
                     line_total, location_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (invoice_id, item_id, description, quantity, unit_price, vat_rate,
                      line_total, location_id))
                
                # Issue stock if item_id is provided
                if item_id:
                    success, trans_num, cogs_cost = self.inventory.stock_issue(
                        item_id, location_id, quantity, invoice_number,
                        f"Sale - Invoice {invoice_number}", None
                    )
                    
                    if success:
                        # Post COGS entry
                        cogs_value = quantity * cogs_cost
                        cogs_lines = [
                            (cogs_account, cogs_value, 0, f"COGS - {invoice_number}"),
                            (inventory_account, 0, cogs_value, f"Inventory Reduction - {invoice_number}")
                        ]
                        
                        self.accounting.create_journal_entry(
                            invoice_date, 'COGS', invoice_number,
                            f"Cost of Goods Sold - {invoice_number}", 'GBP', 1.0, cogs_lines
                        )
            
            conn.commit()
            return True, invoice_number, "Invoice created successfully"
        except Exception as e:
            conn.rollback()
            return False, None, str(e)
        finally:
            conn.close()
    
    def record_payment(self, invoice_number, payment_date, amount, payment_method, 
                      bank_account_id, reference, description):
        """Record payment against sales invoice"""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            # Get invoice details
            cursor.execute('''
                SELECT invoice_id, customer_id, total_amount, currency, exchange_rate
                FROM sales_invoices WHERE invoice_number = ?
            ''', (invoice_number,))
            
            invoice = cursor.fetchone()
            if not invoice:
                return False, None, "Invoice not found"
            
            # Get customer receivable account
            cursor.execute('SELECT receivable_account_id FROM customers WHERE customer_id = ?', 
                          (invoice['customer_id'],))
            customer = cursor.fetchone()
            receivable_account = customer['receivable_account_id']
            
            # Create journal entry
            journal_lines = [
                (bank_account_id, amount * invoice['exchange_rate'], 0, f"Payment received - {invoice_number}"),
                (receivable_account, 0, amount * invoice['exchange_rate'], f"Payment from customer - {invoice_number}")
            ]
            
            success, entry_number, msg = self.accounting.create_journal_entry(
                payment_date, 'Payment Receipt', reference,
                description, invoice['currency'], invoice['exchange_rate'], journal_lines
            )
            
            if not success:
                raise Exception(f"Failed to create journal entry: {msg}")
            
            # Get journal entry ID
            cursor.execute('SELECT entry_id FROM journal_entries WHERE entry_number = ?', (entry_number,))
            journal_entry_id = cursor.fetchone()['entry_id']
            
            # Generate payment number
            cursor.execute('SELECT COUNT(*) as count FROM payments WHERE party_type = "Customer"')
            count = cursor.fetchone()['count']
            payment_number = f"PMT-IN-{count + 1:06d}"
            
            # Record payment
            cursor.execute('''
                INSERT INTO payments
                (payment_number, payment_date, payment_type, party_type, party_id,
                 amount, currency, exchange_rate, payment_method, reference, description,
                 bank_account_id, journal_entry_id, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (payment_number, payment_date, 'Receipt', 'Customer', invoice['customer_id'],
                  amount, invoice['currency'], invoice['exchange_rate'], payment_method,
                  reference, description, bank_account_id, journal_entry_id,
                  datetime.now().isoformat()))
            
            # Update invoice status if fully paid
            if amount >= invoice['total_amount']:
                cursor.execute('UPDATE sales_invoices SET status = "Paid" WHERE invoice_id = ?',
                             (invoice['invoice_id'],))
            else:
                cursor.execute('UPDATE sales_invoices SET status = "Partially Paid" WHERE invoice_id = ?',
                             (invoice['invoice_id'],))
            
            conn.commit()
            return True, payment_number, "Payment recorded successfully"
        except Exception as e:
            conn.rollback()
            return False, None, str(e)
        finally:
            conn.close()


class PurchaseManager:
    def __init__(self, db_path="accounting_data.db"):
        self.db_path = db_path
        self.accounting = AccountingManager(db_path)
        self.inventory = InventoryManager(db_path)
        
    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def create_purchase_bill(self, supplier_id, bill_date, due_date, currency, exchange_rate,
                            notes, lines):
        """
        Create purchase bill with automatic journal posting and stock receipt
        lines = [(item_id, description, quantity, unit_cost, vat_rate, location_id), ...]
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            # Calculate totals
            subtotal = 0
            vat_amount = 0
            
            for line in lines:
                item_id, description, quantity, unit_cost, vat_rate, location_id = line
                line_total = quantity * unit_cost
                line_vat = line_total * (vat_rate / 100)
                subtotal += line_total
                vat_amount += line_vat
            
            total_amount = subtotal + vat_amount
            
            # Generate bill number
            cursor.execute('SELECT COUNT(*) as count FROM purchase_bills')
            count = cursor.fetchone()['count']
            bill_number = f"BILL-{count + 1:06d}"
            
            # Get supplier details
            cursor.execute('SELECT payable_account_id FROM suppliers WHERE supplier_id = ?', (supplier_id,))
            supplier = cursor.fetchone()
            payable_account = supplier['payable_account_id']
            
            # Get expense and VAT accounts
            cursor.execute('SELECT account_id FROM chart_of_accounts WHERE account_code = ?', ('1131',))
            inventory_account = cursor.fetchone()['account_id']
            
            cursor.execute('SELECT account_id FROM chart_of_accounts WHERE account_code = ?', ('2122',))
            vat_input_account = cursor.fetchone()['account_id']
            
            # Create journal entry
            journal_lines = [
                (inventory_account, subtotal * exchange_rate, 0, f"Purchase - {bill_number}"),
                (payable_account, 0, total_amount * exchange_rate, f"Purchase Bill {bill_number}"),
            ]
            
            if vat_amount > 0:
                journal_lines.append(
                    (vat_input_account, vat_amount * exchange_rate, 0, f"VAT on Purchase - {bill_number}")
                )
            
            success, entry_number, msg = self.accounting.create_journal_entry(
                bill_date, 'Purchase Bill', bill_number,
                f"Purchase Bill from Supplier", currency, exchange_rate, journal_lines
            )
            
            if not success:
                raise Exception(f"Failed to create journal entry: {msg}")
            
            # Get journal entry ID
            cursor.execute('SELECT entry_id FROM journal_entries WHERE entry_number = ?', (entry_number,))
            journal_entry_id = cursor.fetchone()['entry_id']
            
            # Insert purchase bill
            cursor.execute('''
                INSERT INTO purchase_bills
                (bill_number, bill_date, supplier_id, currency, exchange_rate,
                 subtotal, vat_amount, total_amount, status, due_date, notes,
                 journal_entry_id, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (bill_number, bill_date, supplier_id, currency, exchange_rate,
                  subtotal, vat_amount, total_amount, 'Unpaid', due_date, notes,
                  journal_entry_id, datetime.now().isoformat()))
            
            bill_id = cursor.lastrowid
            
            # Insert bill lines and receive stock
            for line in lines:
                item_id, description, quantity, unit_cost, vat_rate, location_id = line
                line_total = quantity * unit_cost
                
                cursor.execute('''
                    INSERT INTO purchase_bill_lines
                    (bill_id, item_id, description, quantity, unit_cost, vat_rate,
                     line_total, location_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (bill_id, item_id, description, quantity, unit_cost, vat_rate,
                      line_total, location_id))
                
                # Receive stock if item_id is provided
                if item_id:
                    self.inventory.stock_receipt(
                        item_id, location_id, quantity, unit_cost, bill_number,
                        f"Purchase - Bill {bill_number}", None
                    )
            
            conn.commit()
            return True, bill_number, "Purchase bill created successfully"
        except Exception as e:
            conn.rollback()
            return False, None, str(e)
        finally:
            conn.close()
    
    def make_payment(self, bill_number, payment_date, amount, payment_method,
                    bank_account_id, reference, description):
        """Record payment against purchase bill"""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            # Get bill details
            cursor.execute('''
                SELECT bill_id, supplier_id, total_amount, currency, exchange_rate
                FROM purchase_bills WHERE bill_number = ?
            ''', (bill_number,))
            
            bill = cursor.fetchone()
            if not bill:
                return False, None, "Bill not found"
            
            # Get supplier payable account
            cursor.execute('SELECT payable_account_id FROM suppliers WHERE supplier_id = ?',
                          (bill['supplier_id'],))
            supplier = cursor.fetchone()
            payable_account = supplier['payable_account_id']
            
            # Create journal entry
            journal_lines = [
                (payable_account, amount * bill['exchange_rate'], 0, f"Payment made - {bill_number}"),
                (bank_account_id, 0, amount * bill['exchange_rate'], f"Payment to supplier - {bill_number}")
            ]
            
            success, entry_number, msg = self.accounting.create_journal_entry(
                payment_date, 'Payment', reference,
                description, bill['currency'], bill['exchange_rate'], journal_lines
            )
            
            if not success:
                raise Exception(f"Failed to create journal entry: {msg}")
            
            # Get journal entry ID
            cursor.execute('SELECT entry_id FROM journal_entries WHERE entry_number = ?', (entry_number,))
            journal_entry_id = cursor.fetchone()['entry_id']
            
            # Generate payment number
            cursor.execute('SELECT COUNT(*) as count FROM payments WHERE party_type = "Supplier"')
            count = cursor.fetchone()['count']
            payment_number = f"PMT-OUT-{count + 1:06d}"
            
            # Record payment
            cursor.execute('''
                INSERT INTO payments
                (payment_number, payment_date, payment_type, party_type, party_id,
                 amount, currency, exchange_rate, payment_method, reference, description,
                 bank_account_id, journal_entry_id, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (payment_number, payment_date, 'Payment', 'Supplier', bill['supplier_id'],
                  amount, bill['currency'], bill['exchange_rate'], payment_method,
                  reference, description, bank_account_id, journal_entry_id,
                  datetime.now().isoformat()))
            
            # Update bill status if fully paid
            if amount >= bill['total_amount']:
                cursor.execute('UPDATE purchase_bills SET status = "Paid" WHERE bill_id = ?',
                             (bill['bill_id'],))
            else:
                cursor.execute('UPDATE purchase_bills SET status = "Partially Paid" WHERE bill_id = ?',
                             (bill['bill_id'],))
            
            conn.commit()
            return True, payment_number, "Payment made successfully"
        except Exception as e:
            conn.rollback()
            return False, None, str(e)
        finally:
            conn.close()
