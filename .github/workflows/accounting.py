import sqlite3
from datetime import datetime

class AccountingManager:
    def __init__(self, db_path="accounting_data.db"):
        self.db_path = db_path
        
    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def create_journal_entry(self, entry_date, entry_type, reference, description, 
                            currency='GBP', exchange_rate=1.0, lines=[]):
        """
        Create a journal entry with automatic double-entry validation
        lines = [(account_id, debit, credit, description), ...]
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            # Validate double entry (debits must equal credits)
            total_debits = sum(line[1] for line in lines)
            total_credits = sum(line[2] for line in lines)
            
            if round(total_debits, 2) != round(total_credits, 2):
                return False, None, f"Unbalanced entry: Debits={total_debits:.2f}, Credits={total_credits:.2f}"
            
            # Generate entry number
            cursor.execute('SELECT COUNT(*) as count FROM journal_entries')
            count = cursor.fetchone()['count']
            entry_number = f"JE-{count + 1:06d}"
            
            # Insert journal entry header
            cursor.execute('''
                INSERT INTO journal_entries
                (entry_number, entry_date, entry_type, reference, description, 
                 currency, exchange_rate, status, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (entry_number, entry_date, entry_type, reference, description,
                  currency, exchange_rate, 'Posted', datetime.now().isoformat()))
            
            entry_id = cursor.lastrowid
            
            # Insert journal entry lines
            for line in lines:
                account_id, debit, credit, line_desc = line
                
                # Convert to base currency if needed
                debit_base = debit * exchange_rate
                credit_base = credit * exchange_rate
                
                cursor.execute('''
                    INSERT INTO journal_entry_lines
                    (entry_id, account_id, debit_amount, credit_amount, 
                     debit_base_currency, credit_base_currency, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (entry_id, account_id, debit, credit, debit_base, credit_base, line_desc))
            
            conn.commit()
            return True, entry_number, "Journal entry created successfully"
        except Exception as e:
            conn.rollback()
            return False, None, str(e)
        finally:
            conn.close()
    
    def get_account_balance(self, account_id, date_to=None):
        """Get account balance up to a specific date"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Get account type
        cursor.execute('SELECT account_type FROM chart_of_accounts WHERE account_id = ?', (account_id,))
        account = cursor.fetchone()
        
        if not account:
            conn.close()
            return None
        
        account_type = account['account_type']
        
        # Build query
        query = '''
            SELECT 
                COALESCE(SUM(debit_base_currency), 0) as total_debits,
                COALESCE(SUM(credit_base_currency), 0) as total_credits
            FROM journal_entry_lines jel
            JOIN journal_entries je ON jel.entry_id = je.entry_id
            WHERE jel.account_id = ? AND je.status = 'Posted'
        '''
        
        params = [account_id]
        
        if date_to:
            query += ' AND je.entry_date <= ?'
            params.append(date_to)
        
        cursor.execute(query, params)
        result = cursor.fetchone()
        
        total_debits = result['total_debits']
        total_credits = result['total_credits']
        
        # Calculate balance based on account type
        # Asset and Expense accounts: Debit balance (Debits - Credits)
        # Liability, Equity, Revenue accounts: Credit balance (Credits - Debits)
        if account_type in ['Asset', 'Expense']:
            balance = total_debits - total_credits
        else:  # Liability, Equity, Revenue
            balance = total_credits - total_debits
        
        conn.close()
        return balance
    
    def get_trial_balance(self, date_to=None):
        """Generate trial balance report"""
        conn = self.connect()
        cursor = conn.cursor()
        
        query = '''
            SELECT 
                a.account_code,
                a.account_name,
                a.account_type,
                COALESCE(SUM(jel.debit_base_currency), 0) as total_debits,
                COALESCE(SUM(jel.credit_base_currency), 0) as total_credits
            FROM chart_of_accounts a
            LEFT JOIN journal_entry_lines jel ON a.account_id = jel.account_id
            LEFT JOIN journal_entries je ON jel.entry_id = je.entry_id
            WHERE a.is_active = 1
        '''
        
        params = []
        
        if date_to:
            query += ' AND (je.entry_date <= ? OR je.entry_date IS NULL)'
            params.append(date_to)
        
        query += ' AND (je.status = "Posted" OR je.status IS NULL)'
        query += ' GROUP BY a.account_id ORDER BY a.account_code'
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        trial_balance = []
        total_debits = 0
        total_credits = 0
        
        for row in results:
            debits = row['total_debits']
            credits = row['total_credits']
            
            # Calculate balance based on account type
            if row['account_type'] in ['Asset', 'Expense']:
                balance = debits - credits
                if balance > 0:
                    debit_balance = balance
                    credit_balance = 0
                else:
                    debit_balance = 0
                    credit_balance = abs(balance)
            else:  # Liability, Equity, Revenue
                balance = credits - debits
                if balance > 0:
                    credit_balance = balance
                    debit_balance = 0
                else:
                    credit_balance = 0
                    debit_balance = abs(balance)
            
            if debit_balance != 0 or credit_balance != 0:
                trial_balance.append({
                    'account_code': row['account_code'],
                    'account_name': row['account_name'],
                    'account_type': row['account_type'],
                    'debit_balance': debit_balance,
                    'credit_balance': credit_balance
                })
                
                total_debits += debit_balance
                total_credits += credit_balance
        
        conn.close()
        
        return trial_balance, total_debits, total_credits
    
    def get_profit_and_loss(self, date_from, date_to):
        """Generate Profit & Loss Statement"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Get Revenue
        cursor.execute('''
            SELECT 
                a.account_code,
                a.account_name,
                COALESCE(SUM(jel.credit_base_currency - jel.debit_base_currency), 0) as amount
            FROM chart_of_accounts a
            LEFT JOIN journal_entry_lines jel ON a.account_id = jel.account_id
            LEFT JOIN journal_entries je ON jel.entry_id = je.entry_id
            WHERE a.account_type = 'Revenue' 
            AND a.is_active = 1
            AND je.status = 'Posted'
            AND je.entry_date >= ? AND je.entry_date <= ?
            GROUP BY a.account_id
            HAVING amount != 0
            ORDER BY a.account_code
        ''', (date_from, date_to))
        
        revenue_accounts = [dict(row) for row in cursor.fetchall()]
        total_revenue = sum(acc['amount'] for acc in revenue_accounts)
        
        # Get Cost of Sales
        cursor.execute('''
            SELECT 
                a.account_code,
                a.account_name,
                COALESCE(SUM(jel.debit_base_currency - jel.credit_base_currency), 0) as amount
            FROM chart_of_accounts a
            LEFT JOIN journal_entry_lines jel ON a.account_id = jel.account_id
            LEFT JOIN journal_entries je ON jel.entry_id = je.entry_id
            WHERE a.account_type = 'Expense' 
            AND a.account_code LIKE '5%'
            AND a.is_active = 1
            AND je.status = 'Posted'
            AND je.entry_date >= ? AND je.entry_date <= ?
            GROUP BY a.account_id
            HAVING amount != 0
            ORDER BY a.account_code
        ''', (date_from, date_to))
        
        cogs_accounts = [dict(row) for row in cursor.fetchall()]
        total_cogs = sum(acc['amount'] for acc in cogs_accounts)
        
        # Get Operating Expenses
        cursor.execute('''
            SELECT 
                a.account_code,
                a.account_name,
                COALESCE(SUM(jel.debit_base_currency - jel.credit_base_currency), 0) as amount
            FROM chart_of_accounts a
            LEFT JOIN journal_entry_lines jel ON a.account_id = jel.account_id
            LEFT JOIN journal_entries je ON jel.entry_id = je.entry_id
            WHERE a.account_type = 'Expense' 
            AND a.account_code LIKE '6%'
            AND a.is_active = 1
            AND je.status = 'Posted'
            AND je.entry_date >= ? AND je.entry_date <= ?
            GROUP BY a.account_id
            HAVING amount != 0
            ORDER BY a.account_code
        ''', (date_from, date_to))
        
        expense_accounts = [dict(row) for row in cursor.fetchall()]
        total_expenses = sum(acc['amount'] for acc in expense_accounts)
        
        gross_profit = total_revenue - total_cogs
        net_profit = gross_profit - total_expenses
        
        conn.close()
        
        return {
            'revenue': revenue_accounts,
            'total_revenue': total_revenue,
            'cogs': cogs_accounts,
            'total_cogs': total_cogs,
            'gross_profit': gross_profit,
            'expenses': expense_accounts,
            'total_expenses': total_expenses,
            'net_profit': net_profit
        }
    
    def get_balance_sheet(self, date_to):
        """Generate Balance Sheet"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Get Assets
        cursor.execute('''
            SELECT 
                a.account_code,
                a.account_name,
                COALESCE(SUM(jel.debit_base_currency - jel.credit_base_currency), 0) as amount
            FROM chart_of_accounts a
            LEFT JOIN journal_entry_lines jel ON a.account_id = jel.account_id
            LEFT JOIN journal_entries je ON jel.entry_id = je.entry_id
            WHERE a.account_type = 'Asset' 
            AND a.is_active = 1
            AND je.status = 'Posted'
            AND je.entry_date <= ?
            GROUP BY a.account_id
            HAVING amount != 0
            ORDER BY a.account_code
        ''', (date_to,))
        
        asset_accounts = [dict(row) for row in cursor.fetchall()]
        total_assets = sum(acc['amount'] for acc in asset_accounts)
        
        # Get Liabilities
        cursor.execute('''
            SELECT 
                a.account_code,
                a.account_name,
                COALESCE(SUM(jel.credit_base_currency - jel.debit_base_currency), 0) as amount
            FROM chart_of_accounts a
            LEFT JOIN journal_entry_lines jel ON a.account_id = jel.account_id
            LEFT JOIN journal_entries je ON jel.entry_id = je.entry_id
            WHERE a.account_type = 'Liability' 
            AND a.is_active = 1
            AND je.status = 'Posted'
            AND je.entry_date <= ?
            GROUP BY a.account_id
            HAVING amount != 0
            ORDER BY a.account_code
        ''', (date_to,))
        
        liability_accounts = [dict(row) for row in cursor.fetchall()]
        total_liabilities = sum(acc['amount'] for acc in liability_accounts)
        
        # Get Equity
        cursor.execute('''
            SELECT 
                a.account_code,
                a.account_name,
                COALESCE(SUM(jel.credit_base_currency - jel.debit_base_currency), 0) as amount
            FROM chart_of_accounts a
            LEFT JOIN journal_entry_lines jel ON a.account_id = jel.account_id
            LEFT JOIN journal_entries je ON jel.entry_id = je.entry_id
            WHERE a.account_type = 'Equity' 
            AND a.is_active = 1
            AND je.status = 'Posted'
            AND je.entry_date <= ?
            GROUP BY a.account_id
            HAVING amount != 0
            ORDER BY a.account_code
        ''', (date_to,))
        
        equity_accounts = [dict(row) for row in cursor.fetchall()]
        total_equity = sum(acc['amount'] for acc in equity_accounts)
        
        total_liabilities_equity = total_liabilities + total_equity
        
        conn.close()
        
        return {
            'assets': asset_accounts,
            'total_assets': total_assets,
            'liabilities': liability_accounts,
            'total_liabilities': total_liabilities,
            'equity': equity_accounts,
            'total_equity': total_equity,
            'total_liabilities_equity': total_liabilities_equity
        }
    
    def get_general_ledger(self, account_id, date_from=None, date_to=None):
        """Get general ledger for a specific account"""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Get account info
        cursor.execute('SELECT account_code, account_name, account_type FROM chart_of_accounts WHERE account_id = ?', 
                      (account_id,))
        account = cursor.fetchone()
        
        if not account:
            conn.close()
            return None, []
        
        # Get opening balance
        opening_balance = 0
        if date_from:
            cursor.execute('''
                SELECT 
                    COALESCE(SUM(debit_base_currency), 0) as debits,
                    COALESCE(SUM(credit_base_currency), 0) as credits
                FROM journal_entry_lines jel
                JOIN journal_entries je ON jel.entry_id = je.entry_id
                WHERE jel.account_id = ? AND je.entry_date < ? AND je.status = 'Posted'
            ''', (account_id, date_from))
            
            result = cursor.fetchone()
            if account['account_type'] in ['Asset', 'Expense']:
                opening_balance = result['debits'] - result['credits']
            else:
                opening_balance = result['credits'] - result['debits']
        
        # Get transactions
        query = '''
            SELECT 
                je.entry_number,
                je.entry_date,
                je.entry_type,
                je.reference,
                jel.description,
                jel.debit_amount,
                jel.credit_amount,
                je.currency
            FROM journal_entry_lines jel
            JOIN journal_entries je ON jel.entry_id = je.entry_id
            WHERE jel.account_id = ? AND je.status = 'Posted'
        '''
        
        params = [account_id]
        
        if date_from:
            query += ' AND je.entry_date >= ?'
            params.append(date_from)
        
        if date_to:
            query += ' AND je.entry_date <= ?'
            params.append(date_to)
        
        query += ' ORDER BY je.entry_date, je.entry_number'
        
        cursor.execute(query, params)
        transactions = [dict(row) for row in cursor.fetchall()]
        
        # Calculate running balance
        balance = opening_balance
        for trans in transactions:
            if account['account_type'] in ['Asset', 'Expense']:
                balance += trans['debit_amount'] - trans['credit_amount']
            else:
                balance += trans['credit_amount'] - trans['debit_amount']
            trans['balance'] = balance
        
        conn.close()
        
        return dict(account), transactions, opening_balance
