from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this to a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    min_stock = db.Column(db.Integer, default=5)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    gst_number = db.Column(db.String(15))  # 15 characters for GSTIN format: 22AAAAA0000A1Z5
    balance = db.Column(db.Float, default=0.0)

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False)
    amount_paid = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)  # 'cash' or 'cheque'
    balance = db.Column(db.Float, default=0.0)  # Remaining balance to be paid
    customer = db.relationship('Customer', backref=db.backref('sales', lazy=True))

class SaleItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    product = db.relationship('Product', backref=db.backref('sale_items', lazy=True))

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_method = db.Column(db.String(20), nullable=False)  # 'cash' or 'cheque'
    notes = db.Column(db.Text)
    customer = db.relationship('Customer', backref=db.backref('payments', lazy=True))

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Routes
@app.route('/')
@login_required
def index():
    low_stock_products = Product.query.filter(Product.quantity <= Product.min_stock).all()
    recent_sales = Sale.query.order_by(Sale.date.desc()).limit(5).all()
    total_products = Product.query.count()
    total_customers = Customer.query.count()
    
    # Calculate total sales for today
    today = datetime.now(timezone.utc).date()
    today_sales = Sale.query.filter(
        db.func.date(Sale.date) == today
    ).all()
    daily_sales = sum(sale.amount_paid for sale in today_sales)
    
    return render_template('index.html', 
                         low_stock_products=low_stock_products,
                         recent_sales=recent_sales,
                         total_products=total_products,
                         total_customers=total_customers,
                         daily_sales=daily_sales)

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Product routes

@app.route('/products')
@login_required
def products():
    all_products = Product.query.order_by(Product.name).all()
    return render_template('products.html', products=all_products)

@app.route('/product/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        name = request.form.get('name')
        price = float(request.form.get('price', 0))
        quantity = int(request.form.get('quantity', 0))
        min_stock = int(request.form.get('min_stock', 5))
        
        product = Product(name=name, price=price, quantity=quantity, min_stock=min_stock)
        db.session.add(product)
        db.session.commit()
        
        flash('Product added successfully!', 'success')
        return redirect(url_for('products'))
    
    return render_template('add_product.html')

@app.route('/product/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.price = float(request.form.get('price', 0))
        product.quantity = int(request.form.get('quantity', 0))
        product.min_stock = int(request.form.get('min_stock', 5))
        
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('products'))
    
    return render_template('add_product.html', product=product)

@app.route('/product/delete/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Check if product is in any sales before deleting
    if product.sale_items:
        return jsonify({
            'success': False,
            'message': 'Cannot delete product that has sales records.'
        }), 400
    
    db.session.delete(product)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/api/products/search')
@login_required
def search_products():
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify([])
        
    # Search by product name or ID
    try:
        # Try to convert query to integer for ID search
        product_id = int(query)
        products = Product.query.filter(
            (Product.id == product_id) | 
            (Product.name.ilike(f'%{query}%'))
        ).limit(10).all()
    except ValueError:
        # If not a number, search by name only
        products = Product.query.filter(Product.name.ilike(f'%{query}%')).limit(10).all()
    
    # Convert products to list of dicts
    result = [{
        'id': p.id,
        'name': p.name,
        'price': float(p.price) if p.price else 0.0,
        'quantity': p.quantity,
        'unit': getattr(p, 'unit', 'pcs'),
        'barcode': getattr(p, 'barcode', '')
    } for p in products]
    
    return jsonify(result)

# Customer routes
@app.route('/api/customers/search')
@login_required
def search_customers():
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify([])
        
    # Search by name or phone
    customers = Customer.query.filter(
        (Customer.name.ilike(f'%{query}%')) |
        (Customer.phone.ilike(f'%{query}%'))
    ).limit(10).all()
    
    # Convert customers to list of dicts
    result = [{
        'id': c.id,
        'name': c.name,
        'phone': c.phone or 'No phone',
        'address': c.address or ''
    } for c in customers]
    
    return jsonify(result)

@app.route('/customers')
@login_required
def customers():
    all_customers = Customer.query.all()
    return render_template('customers.html', customers=all_customers)

@app.route('/customer/add', methods=['GET', 'POST'])
@login_required
def add_customer():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        address = request.form.get('address')
        gst_number = request.form.get('gst_number', '').strip().upper() or None
        
        # Validate GST number format if provided
        if gst_number:
            import re
            gst_pattern = re.compile(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$')
            if not gst_pattern.match(gst_number):
                flash('Invalid GST number format. Please check and try again.', 'error')
                return render_template('add_customer.html', 
                                    name=name, 
                                    phone=phone, 
                                    address=address,
                                    gst_number=gst_number)
        
        customer = Customer(name=name, phone=phone, address=address, gst_number=gst_number)
        db.session.add(customer)
        db.session.commit()
        
        flash('Customer added successfully!', 'success')
        return redirect(url_for('customers'))
    
    return render_template('add_customer.html')

@app.route('/customer/edit/<int:customer_id>', methods=['GET', 'POST'])
@login_required
def edit_customer(customer_id):
    customer = db.session.get(Customer, customer_id)
    if not customer:
        flash('Customer not found!', 'error')
        return redirect(url_for('customers'))
    
    if request.method == 'POST':
        customer.name = request.form.get('name', customer.name)
        customer.phone = request.form.get('phone', customer.phone)
        customer.address = request.form.get('address', customer.address)
        
        # Handle GST number
        gst_number = request.form.get('gst_number', '').strip().upper() or None
        if gst_number != customer.gst_number:
            if gst_number:
                # Validate GST number format if provided
                import re
                gst_pattern = re.compile(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$')
                if not gst_pattern.match(gst_number):
                    flash('Invalid GST number format. Please check and try again.', 'error')
                    return render_template('edit_customer.html', customer={
                        'id': customer.id,
                        'name': customer.name,
                        'phone': customer.phone,
                        'address': customer.address,
                        'gst_number': gst_number
                    })
            customer.gst_number = gst_number
        
        db.session.commit()
        flash('Customer updated successfully!', 'success')
        return redirect(url_for('customers'))
    
    return render_template('edit_customer.html', customer=customer)
@app.route('/sales')
@login_required
def sales():
    from datetime import datetime, time
    
    # Handle date range filter
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    # Initialize query with customer join
    query = db.session.query(Sale).join(Customer)
    
    # Apply date range filter if provided
    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            # Set end_date to end of day
            end_date = datetime.combine(end_date, time(23, 59, 59))
            query = query.filter(Sale.date.between(start_date, end_date))
        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD format.', 'error')
    
    # Handle sorting
    sort_by = request.args.get('sort', 'date_desc')
    sort_mapping = {
        'date_asc': Sale.date.asc(),
        'date_desc': Sale.date.desc(),
        'total_asc': Sale.total_amount.asc(),
        'total_desc': Sale.total_amount.desc(),
        'customer_asc': Customer.name.asc(),
        'customer_desc': Customer.name.desc()
    }
    
    # Apply sorting
    order_by = sort_mapping.get(sort_by, Sale.date.desc())
    all_sales = query.order_by(order_by).all()
    
    # Get min and max dates for date picker
    min_max_dates = db.session.query(
        db.func.min(Sale.date).label('min_date'),
        db.func.max(Sale.date).label('max_date')
    ).first()
    
    # Handle CSV export
    if 'export' in request.args and request.args['export'] == 'csv':
        import csv
        from io import StringIO
        from flask import make_response
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write CSV header
        writer.writerow([
            'Sale ID', 'Date', 'Customer', 'Total Amount (₹)', 
            'Amount Paid (₹)', 'Balance (₹)', 'Payment Method'
        ])
        
        # Write data rows
        for sale in all_sales:
            writer.writerow([
                sale.id,
                sale.date.strftime('%Y-%m-%d %H:%M:%S'),
                sale.customer.name if sale.customer else 'Walk-in Customer',
                f"{sale.total_amount:.2f}",
                f"{sale.amount_paid:.2f}",
                f"{sale.balance:.2f}",
                sale.payment_method.title()
            ])
        
        # Create response with CSV data
        output.seek(0)
        response = make_response(output.getvalue())
        response.mimetype = 'text/csv'
        filename = 'sales_export'
        if start_date_str and end_date_str:
            filename += f'_{start_date_str}_to_{end_date_str}'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}.csv'
        return response
    
    return render_template('sales.html', 
                         sales=all_sales, 
                         current_sort=sort_by,
                         start_date=start_date_str,
                         end_date=end_date_str,
                         min_date=min_max_dates.min_date.strftime('%Y-%m-%d') if min_max_dates and min_max_dates.min_date else '',
                         max_date=min_max_dates.max_date.strftime('%Y-%m-%d') if min_max_dates and min_max_dates.max_date else ''
                        )

@app.route('/sale/new', methods=['GET', 'POST'])
@login_required
def new_sale():
    if request.method == 'POST':
        try:
            if not request.is_json:
                return jsonify({
                    'success': False,
                    'message': 'Content-Type must be application/json'
                }), 415
                
            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'No JSON data received'
                }), 400
                
            customer_id = int(data.get('customer_id'))
            payment_method = data.get('payment_method', 'cash')
            amount_paid = float(data.get('amount_paid', 0))
            items = data.get('items', [])
            
            # Get customer
            customer = db.session.get(Customer, customer_id)
            if not customer:
                return jsonify({'success': False, 'message': 'Customer not found'}), 400
            
            # Validate items
            if not items:
                return jsonify({'success': False, 'message': 'No items in the sale'}), 400
            
            # Calculate total amount and update inventory
            total_amount = 0
            sale_items = []
            
            for item in items:
                product = db.session.get(Product, item.get('product_id'))
                if not product:
                    return jsonify({'success': False, 'message': f'Product {item.get("product_id")} not found'}), 400
                
                quantity = int(item.get('quantity', 1))
                if quantity <= 0:
                    return jsonify({'success': False, 'message': f'Invalid quantity for {product.name}'}), 400
                
                if product.quantity < quantity:
                    return jsonify({
                        'success': False, 
                        'message': f'Not enough stock for {product.name}. Only {product.quantity} available.'
                    }), 400
                
                # Update product quantity
                product.quantity -= quantity
                
                # Calculate item total
                item_total = product.price * quantity
                total_amount += item_total
                
                # Create sale item
                sale_item = SaleItem(
                    product_id=product.id,
                    quantity=quantity,
                    price=product.price
                )
                sale_items.append(sale_item)
            
            # Calculate tax (10% for example)
            tax_rate = 0.1
            tax = total_amount * tax_rate
            total_with_tax = total_amount + tax
            
            # Validate payment
            amount_paid = float(amount_paid)
            if amount_paid < 0:
                return jsonify({'success': False, 'message': 'Invalid payment amount'}), 400
                
            if amount_paid > total_with_tax:
                return jsonify({
                    'success': False, 
                    'message': 'Amount paid cannot be greater than total amount'
                }), 400
            
            # Calculate balance
            balance = total_with_tax - amount_paid
            
            # Update customer balance
            customer.balance += balance
            
            # Create sale
            sale = Sale(
                customer_id=customer_id,
                total_amount=total_with_tax,
                amount_paid=amount_paid,
                payment_method=payment_method,
                balance=balance,
                date=datetime.utcnow()
            )
            db.session.add(sale)
            db.session.flush()  # This assigns an ID to the sale without committing
            
            # Create and add sale items
            for item in sale_items:
                db.session.add(item)
                item.sale_id = sale.id  # Explicitly set the sale_id
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'sale_id': sale.id,
                'message': 'Sale recorded successfully!',
                'redirect_url': url_for('view_receipt', sale_id=sale.id, _external=True)
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': f'Error processing sale: {str(e)}'
            }), 500
    
    # GET request - show the form
    customers = Customer.query.order_by(Customer.name).all()
    return render_template('new_sale.html', customers=customers)

@app.route('/sale/receipt/<int:sale_id>')
@login_required
def view_receipt(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    return render_template('receipt.html', sale=sale)

# Balance Sheet/Reports
@app.route('/reports/balance_sheet')
@login_required
def balance_sheet():
    # Get customers with outstanding balances
    customers = Customer.query.filter(Customer.balance > 0).all()
    
    # Calculate total outstanding
    total_outstanding = sum(customer.balance for customer in customers)
    
    return render_template('balance_sheet.html', 
                         customers=customers, 
                         total_outstanding=total_outstanding)

# Record payment
@app.route('/payment/add', methods=['GET', 'POST'])
@login_required
def add_payment():
    customers = Customer.query.filter(Customer.balance > 0).all()
    customer_id = request.args.get('customer_id', request.form.get('customer_id', ''))
    
    if request.method == 'POST':
        customer_id = request.form.get('customer_id')
        amount = float(request.form.get('amount', 0))
        payment_method = request.form.get('payment_method')
        notes = request.form.get('notes', '')
        
        if not customer_id or amount <= 0:
            flash('Please fill in all required fields with valid data', 'danger')
            return render_template('add_payment.html', customers=customers, customer_id=customer_id)
        
        customer = db.session.get(Customer, customer_id)
        if not customer:
            flash('Customer not found', 'danger')
            return render_template('add_payment.html', customers=customers, customer_id=customer_id)
        
        # Start a transaction
        try:
            # Update customer balance
            payment_amount = min(amount, customer.balance)  # Don't allow overpayment
            customer.balance -= payment_amount
            
            # Record payment
            payment = Payment(
                customer_id=customer_id,
                amount=payment_amount,
                payment_method=payment_method,
                notes=notes
            )
            db.session.add(payment)
            
            # Update any outstanding sales for this customer
            if payment_amount > 0:
                # Find all sales with outstanding balance for this customer
                outstanding_sales = Sale.query.filter(
                    Sale.customer_id == customer_id,
                    Sale.balance > 0
                ).order_by(Sale.date).all()
                
                remaining_payment = payment_amount
                for sale in outstanding_sales:
                    if remaining_payment <= 0:
                        break
                        
                    # Calculate how much of this payment applies to this sale
                    payment_for_sale = min(remaining_payment, sale.balance)
                    
                    # Debug: Print payment application
                    print(f"\nApplying payment to sale {sale.id}")
                    print(f"Before - Balance: {sale.balance}, Amount Paid: {sale.amount_paid}")
                    
                    # Update the sale's balance and amount_paid
                    sale.balance = max(0, sale.balance - payment_for_sale)  # Ensure balance doesn't go negative
                    sale.amount_paid = min(sale.total_amount, sale.amount_paid + payment_for_sale)  # Ensure amount_paid doesn't exceed total
                    remaining_payment -= payment_for_sale
                    
                    print(f"After - Balance: {sale.balance}, Amount Paid: {sale.amount_paid}")
                    print(f"Remaining payment to apply: {remaining_payment}")
            
            db.session.commit()
            flash('Payment recorded successfully!', 'success')
            return redirect(url_for('balance_sheet'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error recording payment: {str(e)}', 'danger')
            return render_template('add_payment.html', customers=customers, customer_id=customer_id)
    
    return render_template('add_payment.html', customers=customers, customer_id=customer_id)

# Initialize database and create admin user if not exists
with app.app_context():
    # Create database tables
    db.create_all()
    
    # Create admin user if not exists
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            password_hash=generate_password_hash('admin123', method='pbkdf2:sha256')
        )
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)
