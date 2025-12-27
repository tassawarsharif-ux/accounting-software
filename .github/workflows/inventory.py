import sqlite3
from datetime import datetime

class InventoryManager:
    def __init__(self, db_path="accounting_data.db"):
        self.db_path = db_path
        
    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def add_inventory_item(self, item_code, item_name, description, unit_of_measure, 
                          reorder_level, inventory_account_id, cogs_account_id, sales_account_id):
        """Add a new inventory item"""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO inventory_items 
                (item_code, item_name, description, unit_of_measure, reorder_level,
                 inventory_account_id, cogs_account_id, sales_account_id, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (item_code, item_name, description, unit_of_measure, reorder_level,
                  inventory_account_id, cogs_account_id, sales_account_id, 
                  datetime.now().isoformat()))
            
            conn.commit()
            item_id = cursor.lastrowid
            return True, item_id, "Item added successfully"
        except sqlite3.IntegrityError:
            return False, None, "Item code already exists"
        finally:
            conn.close()
    
    def add_location(self, location_code, location_name, address):
        """Add a new inventory location"""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO inventory_locations 
                (location_code, location_name, address, created_date)
                VALUES (?, ?, ?, ?)
            ''', (location_code, location_name, address, datetime.now().isoformat()))
            
            conn.commit()
            location_id = cursor.lastrowid
            return True, location_id, "Location added successfully"
        except sqlite3.IntegrityError:
            return False, None, "Location code already exists"
        finally:
            conn.close()
    
    def calculate_weighted_average(self, item_id, location_id, new_quantity, new_cost):
        """Calculate new weighted average cost after stock receipt"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Get current stock
        cursor.execute('''
            SELECT quantity, weighted_avg_cost, total_value 
            FROM inventory_stock 
            WHERE item_id = ? AND location_id = ?
        ''', (item_id, location_id))
        
        stock = cursor.fetchone()
        
        if stock:
            current_qty = stock['quantity']
            current_avg_cost = stock['weighted_avg_cost']
            current_value = stock['total_value']
        else:
            current_qty = 0
            current_avg_cost = 0
            current_value = 0
        
        # Calculate new weighted average
        new_value = new_quantity * new_cost
        total_qty = current_qty + new_quantity
        total_value = current_value + new_value
        
        if total_qty > 0:
            new_weighted_avg = total_value / total_qty
        else:
            new_weighted_avg = 0
        
        conn.close()
        return new_weighted_avg, total_qty, total_value
    
    def stock_receipt(self, item_id, location_id, quantity, unit_cost, reference, description, journal_entry_id=None):
        """Record stock receipt (purchase) with weighted average calculation"""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            # Calculate new weighted average
            new_avg_cost, new_qty, new_value = self.calculate_weighted_average(
                item_id, location_id, quantity, unit_cost
            )
            
            # Generate transaction number
            cursor.execute('SELECT COUNT(*) as count FROM inventory_transactions')
            count = cursor.fetchone()['count']
            trans_number = f"STK-IN-{count + 1:06d}"
            
            # Insert inventory transaction
            cursor.execute('''
                INSERT INTO inventory_transactions
                (transaction_number, transaction_date, transaction_type, item_id,
                 to_location_id, quantity, unit_cost, total_value, reference, description,
                 journal_entry_id, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (trans_number, datetime.now().date().isoformat(), 'Receipt', item_id,
                  location_id, quantity, unit_cost, quantity * unit_cost, reference,
                  description, journal_entry_id, datetime.now().isoformat()))
            
            # Update or insert stock record
            cursor.execute('''
                SELECT stock_id FROM inventory_stock 
                WHERE item_id = ? AND location_id = ?
            ''', (item_id, location_id))
            
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute('''
                    UPDATE inventory_stock 
                    SET quantity = ?, weighted_avg_cost = ?, total_value = ?, last_updated = ?
                    WHERE item_id = ? AND location_id = ?
                ''', (new_qty, new_avg_cost, new_value, datetime.now().isoformat(),
                      item_id, location_id))
            else:
                cursor.execute('''
                    INSERT INTO inventory_stock
                    (item_id, location_id, quantity, weighted_avg_cost, total_value, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (item_id, location_id, new_qty, new_avg_cost, new_value,
                      datetime.now().isoformat()))
            
            conn.commit()
            return True, trans_number, "Stock received successfully"
        except Exception as e:
            conn.rollback()
            return False, None, str(e)
        finally:
            conn.close()
    
    def stock_issue(self, item_id, location_id, quantity, reference, description, journal_entry_id=None):
        """Issue stock (sale/consumption) using weighted average cost"""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            # Get current stock
            cursor.execute('''
                SELECT quantity, weighted_avg_cost, total_value 
                FROM inventory_stock 
                WHERE item_id = ? AND location_id = ?
            ''', (item_id, location_id))
            
            stock = cursor.fetchone()
            
            if not stock:
                return False, None, "No stock available at this location"
            
            current_qty = stock['quantity']
            current_avg_cost = stock['weighted_avg_cost']
            current_value = stock['total_value']
            
            if current_qty < quantity:
                return False, None, f"Insufficient stock. Available: {current_qty}"
            
            # Calculate issue value at weighted average cost
            issue_value = quantity * current_avg_cost
            new_qty = current_qty - quantity
            new_value = current_value - issue_value
            
            # Generate transaction number
            cursor.execute('SELECT COUNT(*) as count FROM inventory_transactions')
            count = cursor.fetchone()['count']
            trans_number = f"STK-OUT-{count + 1:06d}"
            
            # Insert inventory transaction
            cursor.execute('''
                INSERT INTO inventory_transactions
                (transaction_number, transaction_date, transaction_type, item_id,
                 from_location_id, quantity, unit_cost, total_value, reference, description,
                 journal_entry_id, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (trans_number, datetime.now().date().isoformat(), 'Issue', item_id,
                  location_id, quantity, current_avg_cost, issue_value, reference,
                  description, journal_entry_id, datetime.now().isoformat()))
            
            # Update stock record
            cursor.execute('''
                UPDATE inventory_stock 
                SET quantity = ?, total_value = ?, last_updated = ?
                WHERE item_id = ? AND location_id = ?
            ''', (new_qty, new_value, datetime.now().isoformat(), item_id, location_id))
            
            conn.commit()
            return True, trans_number, current_avg_cost  # Return cost for COGS posting
        except Exception as e:
            conn.rollback()
            return False, None, str(e)
        finally:
            conn.close()
    
    def stock_transfer(self, item_id, from_location_id, to_location_id, quantity, reference, description):
        """Transfer stock between locations at weighted average cost"""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            # Get stock from source location
            cursor.execute('''
                SELECT quantity, weighted_avg_cost 
                FROM inventory_stock 
                WHERE item_id = ? AND location_id = ?
            ''', (item_id, from_location_id))
            
            from_stock = cursor.fetchone()
            
            if not from_stock:
                return False, None, "No stock at source location"
            
            if from_stock['quantity'] < quantity:
                return False, None, f"Insufficient stock. Available: {from_stock['quantity']}"
            
            transfer_cost = from_stock['weighted_avg_cost']
            
            # Issue from source location
            success, trans_out, cost = self.stock_issue(
                item_id, from_location_id, quantity, reference, 
                f"Transfer Out - {description}", None
            )
            
            if not success:
                return False, None, cost  # cost contains error message
            
            # Receive at destination location
            success, trans_in, msg = self.stock_receipt(
                item_id, to_location_id, quantity, transfer_cost, reference,
                f"Transfer In - {description}", None
            )
            
            if not success:
                return False, None, msg
            
            # Generate transfer transaction number
            cursor.execute('SELECT COUNT(*) as count FROM inventory_transactions WHERE transaction_type = "Transfer"')
            count = cursor.fetchone()['count']
            trans_number = f"STK-TRF-{count + 1:06d}"
            
            # Record transfer transaction
            cursor.execute('''
                INSERT INTO inventory_transactions
                (transaction_number, transaction_date, transaction_type, item_id,
                 from_location_id, to_location_id, quantity, unit_cost, total_value, 
                 reference, description, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (trans_number, datetime.now().date().isoformat(), 'Transfer', item_id,
                  from_location_id, to_location_id, quantity, transfer_cost, 
                  quantity * transfer_cost, reference, description, datetime.now().isoformat()))
            
            conn.commit()
            return True, trans_number, "Stock transferred successfully"
        except Exception as e:
            conn.rollback()
            return False, None, str(e)
        finally:
            conn.close()
    
    def get_stock_by_location(self, item_id=None):
        """Get current stock levels by location"""
        conn = self.connect()
        cursor = conn.cursor()
        
        if item_id:
            cursor.execute('''
                SELECT 
                    i.item_code,
                    i.item_name,
                    l.location_code,
                    l.location_name,
                    s.quantity,
                    s.weighted_avg_cost,
                    s.total_value,
                    i.unit_of_measure,
                    i.reorder_level
                FROM inventory_stock s
                JOIN inventory_items i ON s.item_id = i.item_id
                JOIN inventory_locations l ON s.location_id = l.location_id
                WHERE s.item_id = ?
                ORDER BY l.location_name
            ''', (item_id,))
        else:
            cursor.execute('''
                SELECT 
                    i.item_code,
                    i.item_name,
                    l.location_code,
                    l.location_name,
                    s.quantity,
                    s.weighted_avg_cost,
                    s.total_value,
                    i.unit_of_measure,
                    i.reorder_level
                FROM inventory_stock s
                JOIN inventory_items i ON s.item_id = i.item_id
                JOIN inventory_locations l ON s.location_id = l.location_id
                WHERE s.quantity > 0
                ORDER BY i.item_name, l.location_name
            ''')
        
        results = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
    
    def get_stock_valuation(self):
        """Get total stock valuation by item"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                i.item_code,
                i.item_name,
                SUM(s.quantity) as total_quantity,
                AVG(s.weighted_avg_cost) as avg_cost,
                SUM(s.total_value) as total_value,
                i.unit_of_measure
            FROM inventory_stock s
            JOIN inventory_items i ON s.item_id = i.item_id
            WHERE s.quantity > 0
            GROUP BY s.item_id
            ORDER BY i.item_name
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
    
    def get_reorder_alerts(self):
        """Get items below reorder level"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                i.item_code,
                i.item_name,
                l.location_name,
                s.quantity,
                i.reorder_level,
                i.unit_of_measure
            FROM inventory_stock s
            JOIN inventory_items i ON s.item_id = i.item_id
            JOIN inventory_locations l ON s.location_id = l.location_id
            WHERE s.quantity <= i.reorder_level AND i.reorder_level > 0
            ORDER BY i.item_name
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
    
    def get_inventory_movements(self, item_id=None, location_id=None, date_from=None, date_to=None):
        """Get inventory movement history"""
        conn = self.connect()
        cursor = conn.cursor()
        
        query = '''
            SELECT 
                t.transaction_number,
                t.transaction_date,
                t.transaction_type,
                i.item_code,
                i.item_name,
                fl.location_name as from_location,
                tl.location_name as to_location,
                t.quantity,
                t.unit_cost,
                t.total_value,
                t.reference,
                t.description
            FROM inventory_transactions t
            JOIN inventory_items i ON t.item_id = i.item_id
            LEFT JOIN inventory_locations fl ON t.from_location_id = fl.location_id
            LEFT JOIN inventory_locations tl ON t.to_location_id = tl.location_id
            WHERE 1=1
        '''
        
        params = []
        
        if item_id:
            query += ' AND t.item_id = ?'
            params.append(item_id)
        
        if location_id:
            query += ' AND (t.from_location_id = ? OR t.to_location_id = ?)'
            params.extend([location_id, location_id])
        
        if date_from:
            query += ' AND t.transaction_date >= ?'
            params.append(date_from)
        
        if date_to:
            query += ' AND t.transaction_date <= ?'
            params.append(date_to)
        
        query += ' ORDER BY t.transaction_date DESC, t.transaction_number DESC'
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
