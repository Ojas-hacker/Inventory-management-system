# Inventory Management System with Billing

A Flask-based web application for managing inventory, sales, and customer balances with support for cash and cheque payments, featuring GST compliance and comprehensive reporting.

## Features

- **Inventory Management**: Add, view, edit, and delete products with stock level tracking
- **Customer Management**: Maintain detailed customer records including GST numbers and contact information
- **Sales Processing**: Process sales with support for both cash and cheque payments
- **GST Compliance**: Track and manage GST numbers for business customers
- **Balance Tracking**: Monitor outstanding customer balances with detailed transaction history
- **Payment Recording**: Record and track customer payments with multiple payment methods
- **Low Stock Alerts**: Get automatic alerts for products that are low in stock
- **Receipt Generation**: Professional receipt generation for all sales transactions
- **Search Functionality**: Quick search for products and customers
- **Responsive Design**: Mobile-friendly interface that works across all devices

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd inventory-management
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   # On Windows
   python -m venv venv
   venv\Scripts\activate
   
   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database**
   The database will be automatically created when you run the application for the first time.

## Running the Application

1. **Start the development server**
   ```bash
   python app.py
   ```

2. **Access the application**
   Open your web browser and go to:
   ```
   http://localhost:5000
   ```

3. **Login**
   - Username: `admin`
   - Password: `admin123`

## Usage

1. **Add Products**
   - Go to Products > Add Product
   - Fill in the product details and save

2. **Add Customers**
   - Go to Customers > Add Customer
   - Fill in the customer details and save

3. **Process Sales**
   - Go to Sales > New Sale
   - Select a customer and add products to the cart
   - Choose payment method (cash/cheque) and enter the amount paid
   - Complete the sale

4. **Record Payments**
   - Go to Balance Sheet
   - Click "Add Payment" for a customer with an outstanding balance
   - Enter the payment details and save
   

## Security Notes

- Change the default admin password after first login
- The default secret key in `app.py` should be changed in production
- For production use, consider using a more secure database like PostgreSQL
- Enable HTTPS in production

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Future Enhancements

- **User Management**: Multiple user roles with different permission levels
- **Barcode Integration**: Support for barcode scanning of products
- **Advanced Reporting**: Detailed sales analytics and financial reports
- **Data Export**: Export functionality for Excel and PDF formats
- **Automated Alerts**: Email/SMS notifications for low stock and payment reminders
- **Multi-branch Support**: Manage inventory across multiple locations
- **Tax Reports**: Generate GST and other tax-related reports
- **Batch Processing**: Support for batch imports/exports
- **REST API**: API endpoints for integration with other systems
