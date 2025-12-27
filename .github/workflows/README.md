# Professional Accounting Software
## Desktop Accounting System with Inventory Management

### Overview
A complete desktop accounting software built with Python and Tkinter, featuring:
- Full double-entry bookkeeping
- Multi-currency support (GBP, USD, EUR, AED)
- Inventory management with weighted average costing
- Multiple location tracking
- UK compliance (VAT, financial reporting)
- Professional financial reports
- Local SQLite database (all data saved on your computer)

### System Requirements
- **Operating System**: Windows 7 or later (also compatible with Mac/Linux)
- **Python**: Version 3.8 or higher
- **Disk Space**: Minimum 100 MB
- **RAM**: 4 GB minimum

### Installation Instructions

#### Method 1: Using Python (Recommended)

1. **Install Python** (if not already installed)
   - Download from https://www.python.org/downloads/
   - During installation, check "Add Python to PATH"

2. **Install Required Libraries**
   Open Command Prompt (Windows) or Terminal (Mac/Linux) and run:
   ```
   pip install reportlab
   ```

3. **Download the Software**
   - Extract all files to a folder (e.g., C:\AccountingSoftware)

4. **Run the Application**
   - Open Command Prompt
   - Navigate to the software folder:
     ```
     cd C:\AccountingSoftware
     ```
   - Run the application:
     ```
     python main_app.py
     ```

#### First Time Setup

1. The software will automatically create a database file (accounting_data.db)
2. Default chart of accounts (UK format) will be created
3. Default currencies will be set up

#### Loading Sample Data (Optional)

To test the software with sample data:
```
python add_sample_data.py
```

This will create:
- 3 sample customers
- 3 sample suppliers
- 3 inventory locations
- 5 inventory items with stock
- Sample journal entries

---

## Features

### 1. Accounting Module

#### Chart of Accounts
- Pre-configured UK chart of accounts
- Hierarchical account structure
- Account types: Assets, Liabilities, Equity, Revenue, Expenses
- Real-time balance calculations

#### Journal Entries
- Manual journal entry creation
- Automatic double-entry validation
- Multi-currency support
- Debit/Credit balance verification

#### Transactions
- Sales Invoices with automatic posting
- Purchase Bills with automatic posting
- Payment receipts
- Payment vouchers
- Bank transactions

### 2. Inventory Management

#### Stock Control
- Weighted average costing method
- Multiple warehouse/location support
- Real-time stock tracking
- Reorder level alerts

#### Stock Transactions
- Stock receipts (purchases)
- Stock issues (sales)
- Stock transfers between locations
- Automatic COGS calculation

#### Stock Reports
- Stock by location
- Stock valuation report
- Inventory movement report
- Reorder alerts

### 3. Financial Reports

#### Management Reports
- **Trial Balance**: Complete list of accounts with balances
- **Profit & Loss Statement**: Revenue and expenses analysis
- **Balance Sheet**: Assets, liabilities, and equity
- **General Ledger**: Detailed transaction history per account

#### Features
- Date range selection
- PDF export capability
- On-screen viewing
- Drill-down capabilities

### 4. Multi-Currency Support

Supported Currencies:
- **GBP** (British Pound) - Base currency
- **USD** (US Dollar)
- **EUR** (Euro)
- **AED** (UAE Dirham)

Features:
- Exchange rate management
- Automatic currency conversion
- Base currency reporting

### 5. VAT Management

UK VAT Rates:
- Standard Rate (20%)
- Reduced Rate (5%)
- Zero Rate (0%)
- Exempt

Features:
- Automatic VAT calculation on invoices
- VAT input/output tracking
- VAT reports

---

## How to Use

### Dashboard
The main dashboard provides:
- Quick statistics (unpaid invoices, bills, stock value)
- Quick action buttons
- Access to all modules

### Creating a Sales Invoice

1. Go to **Transactions → Sales Invoice**
2. Select customer
3. Add invoice lines (items, quantities, prices)
4. VAT automatically calculated
5. Save invoice
6. Stock automatically reduced
7. Accounting entries automatically posted

### Recording a Purchase

1. Go to **Transactions → Purchase Bill**
2. Select supplier
3. Add bill lines (items, quantities, costs)
4. VAT automatically calculated
5. Save bill
6. Stock automatically received
7. Accounting entries automatically posted

### Managing Inventory

#### Adding Items
1. Go to **Inventory → Items**
2. Click "Add New Item"
3. Enter item details (code, name, description)
4. Set reorder level
5. Link to accounting accounts

#### Stock Receipt
1. Go to **Inventory → Stock Receipt**
2. Select item and location
3. Enter quantity and cost
4. Weighted average automatically calculated
5. Stock level updated

#### Stock Transfer
1. Go to **Inventory → Stock Transfer**
2. Select item
3. Choose from/to locations
4. Enter quantity
5. Transfer at weighted average cost

### Generating Reports

#### Trial Balance
1. Go to **Reports → Trial Balance**
2. Select date
3. Click "Generate"
4. Review balances
5. Export to PDF if needed

#### Profit & Loss
1. Go to **Reports → Profit & Loss**
2. Select date range (from/to)
3. Click "Generate"
4. Review revenue, costs, expenses
5. See gross profit and net profit

#### Balance Sheet
1. Go to **Reports → Balance Sheet**
2. Select date
3. Click "Generate"
4. Review assets, liabilities, equity

---

## Database Information

### Location
- **File**: accounting_data.db
- **Location**: Same folder as the application
- **Format**: SQLite database

### Backup
1. Go to **File → Backup Database**
2. Choose location and filename
3. Database copy created

**Recommendation**: Backup daily or weekly depending on transaction volume

### Multi-Company Setup
To manage multiple companies:
1. Create separate folders for each company
2. Copy all software files to each folder
3. Each folder will have its own database file

---

## Accounting Principles

### Double-Entry Bookkeeping
Every transaction affects at least two accounts:
- One account is debited
- One account is credited
- Total debits must equal total credits

### Account Types
- **Assets**: Increase with Debits (e.g., Cash, Inventory, Receivables)
- **Liabilities**: Increase with Credits (e.g., Payables, Loans)
- **Equity**: Increase with Credits (e.g., Share Capital, Retained Earnings)
- **Revenue**: Increase with Credits (e.g., Sales)
- **Expenses**: Increase with Debits (e.g., Rent, Salaries)

### Weighted Average Costing
When inventory is purchased at different prices:
1. Calculate total value: (Existing Qty × Existing Cost) + (New Qty × New Cost)
2. Calculate total quantity: Existing Qty + New Qty
3. New Average Cost = Total Value ÷ Total Quantity
4. Used for all stock issues until next purchase

---

## Troubleshooting

### Application Won't Start
- Ensure Python is installed
- Check if all required libraries are installed: `pip install reportlab`
- Verify you're in the correct folder

### Database Locked Error
- Close all instances of the application
- Wait a few seconds
- Restart the application

### Missing Reports
- Ensure transactions are posted (status = "Posted")
- Check date ranges in report parameters

### Stock Issues
- Verify sufficient stock at location
- Check item is active
- Ensure location is active

---

## Technical Details

### Architecture
- **Frontend**: Tkinter (Python GUI library)
- **Backend**: Python with SQLite
- **Database**: SQLite (single file database)
- **Reports**: ReportLab for PDF generation

### Database Tables
- **Chart of Accounts**: Account master data
- **Journal Entries**: All accounting transactions
- **Customers/Suppliers**: Party master data
- **Inventory Items**: Product master data
- **Inventory Stock**: Stock levels by location
- **Sales Invoices/Purchase Bills**: Trading documents
- **Payments**: Payment transactions

### File Structure
```
accounting_software/
├── main_app.py           # Main GUI application
├── database.py           # Database creation and setup
├── accounting.py         # Accounting engine
├── inventory.py          # Inventory management
├── transactions.py       # Sales and purchase transactions
├── add_sample_data.py    # Sample data loader
├── accounting_data.db    # Database file (created on first run)
└── README.md            # This file
```

---

## Limitations

### Current Version
- Single user (no concurrent access)
- Desktop only (no mobile app)
- No automatic bank reconciliation
- PDF export basic (can be enhanced)
- No email integration

### Data Limits
- Unlimited transactions (limited by disk space)
- Database size: Up to 2 TB
- Recommended: < 1 million transactions for best performance

---

## Future Enhancements

Planned features for future versions:
1. Multi-user support with login system
2. Automated bank reconciliation
3. Email invoices directly
4. Advanced reporting with charts
5. Budget vs. actual analysis
6. Cash flow forecasting
7. Integration with UK HMRC Making Tax Digital
8. Mobile companion app
9. Cloud backup option
10. Barcode scanning for inventory

---

## Support & Contact

### Documentation
- README file (this document)
- In-app help (coming soon)

### Best Practices
1. **Daily**: Enter transactions as they occur
2. **Weekly**: Review trial balance
3. **Monthly**: Generate P&L and Balance Sheet
4. **Monthly**: Backup database
5. **Quarterly**: Review stock levels and reorder
6. **Yearly**: Close books and archive

---

## UK Compliance Notes

### VAT
- Standard rate: 20% (as of 2025)
- VAT registration threshold: £90,000
- This software tracks VAT but does not submit returns
- Export reports for VAT return preparation

### Financial Year
- Default: April 1 to March 31
- Can be customized in company settings

### Reporting Standards
- Reports follow UK GAAP principles
- Suitable for small and medium businesses
- For statutory accounts, consult an accountant

---

## License & Warranty

### License
This software is provided as-is for business use.

### Warranty
No warranty is provided. Users are responsible for:
- Data accuracy
- Regular backups
- Compliance with accounting regulations
- Tax filings and submissions

### Disclaimer
This software is an accounting tool, not a substitute for professional accounting advice. For statutory accounts, tax returns, and complex transactions, consult a qualified accountant.

---

## Quick Reference

### Keyboard Shortcuts
- **Alt+F**: File menu
- **Alt+T**: Transactions menu
- **Alt+I**: Inventory menu
- **Alt+R**: Reports menu

### Common Tasks

| Task | Menu Path |
|------|-----------|
| New Invoice | Transactions → Sales Invoice |
| New Bill | Transactions → Purchase Bill |
| Journal Entry | Transactions → Journal Entry |
| Stock Receipt | Inventory → Stock Receipt |
| Trial Balance | Reports → Trial Balance |
| P&L Statement | Reports → Profit & Loss |
| Balance Sheet | Reports → Balance Sheet |

---

## Version History

**Version 1.0** (December 2025)
- Initial release
- Core accounting features
- Inventory management with weighted average
- Multi-currency support
- UK VAT compliance
- Standard financial reports

---

**END OF README**
