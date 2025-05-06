from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
import uuid
from datetime import datetime

# Initialize the app
app = Flask(__name__)

# Set up database URI and configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'inventory.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'

# Initialize database and migrations
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Models
class Location(db.Model):
    location_id = db.Column(db.String(100), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    
    def __repr__(self):
        return f'<Location {self.name}>'

class Item(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    product_id = db.Column(db.String(length=10), nullable=False, unique=True)
    product_name = db.Column(db.String(length=30), nullable=False)
    price = db.Column(db.Float(), nullable=False)
    stock = db.Column(db.Integer(), nullable=False)

    def __repr__(self):
        return f'<Item {self.product_name}>'

class ProductMove(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.String(10), db.ForeignKey('item.product_id'), nullable=False)
    from_location = db.Column(db.String(100), db.ForeignKey('location.location_id'), nullable=False)
    to_location = db.Column(db.String(100), db.ForeignKey('location.location_id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    movement_qty = db.Column(db.Integer, nullable=False)

    # Relationships
    from_loc = db.relationship('Location', foreign_keys=[from_location], backref=db.backref('product_moves_from', lazy=True))
    to_loc = db.relationship('Location', foreign_keys=[to_location], backref=db.backref('product_moves_to', lazy=True))
    product = db.relationship('Item', backref=db.backref('movements', lazy=True))

    def __repr__(self):
        return f'<ProductMove {self.product_id} from {self.from_location} to {self.to_location}>'

class BuyMovement(db.Model):
    movement_id = db.Column(db.String(50), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    from_location = db.Column(db.String(50), db.ForeignKey('location.location_id'))
    product_id = db.Column(db.String(10), db.ForeignKey('item.product_id'), nullable=False)
    movement_qty = db.Column(db.Integer(), nullable=False)
    
    product = db.relationship('Item', backref=db.backref('buy_movements', lazy=True))
    location = db.relationship('Location', backref=db.backref('buy_movements', lazy=True))

    def __repr__(self):
        return f'<BuyMovement {self.movement_id}>'

class SaleMovement(db.Model):
    movement_id = db.Column(db.String(50), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    to_location = db.Column(db.String(50), db.ForeignKey('location.location_id'))
    product_id = db.Column(db.String(10), db.ForeignKey('item.product_id'), nullable=False)
    movement_qty = db.Column(db.Integer(), nullable=False)
    
    product = db.relationship('Item', backref=db.backref('sale_movements', lazy=True))
    location = db.relationship('Location', backref=db.backref('sale_movements', lazy=True))

    def __repr__(self):
        return f'<SaleMovement {self.movement_id}>'

# Routes
@app.route('/')
def home():
    return redirect(url_for('list_items'))

@app.route('/items')
def list_items():
    items = Item.query.all()
    return render_template('items.html', items=items)

@app.route('/items/add', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        try:
            new_item = Item(
                product_id=request.form['product_id'],
                product_name=request.form['product_name'],
                price=float(request.form['price']),
                stock=int(request.form['stock'])
            )
            db.session.add(new_item)
            db.session.commit()
            flash('Product added successfully!', 'success')
            return redirect(url_for('list_items'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding product: {str(e)}', 'danger')
    return render_template('add_item.html')

@app.route('/items/edit/<int:id>', methods=['GET', 'POST'])
def edit_item(id):
    item = Item.query.get_or_404(id)
    if request.method == 'POST':
        try:
            item.product_name = request.form['product_name']
            item.price = float(request.form['price'])
            item.stock = int(request.form['stock'])
            db.session.commit()
            flash('Product updated successfully!', 'success')
            return redirect(url_for('list_items'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating product: {str(e)}', 'danger')
    return render_template('edit_item.html', item=item)

@app.route('/items/delete/<int:id>', methods=['POST'])
def delete_item(id):
    item = Item.query.get_or_404(id)
    try:
        db.session.delete(item)
        db.session.commit()
        flash('Product deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting product: {str(e)}', 'danger')
    return redirect(url_for('list_items'))

@app.route('/locations')
def list_locations():
    locations = Location.query.all()
    return render_template('locations.html', locations=locations)

@app.route('/locations/add', methods=['GET', 'POST'])
def add_location():
    if request.method == 'POST':
        try:
            location = Location(
                location_id=str(uuid.uuid4()),
                name=request.form['name']
            )
            db.session.add(location)
            db.session.commit()
            flash('Location added successfully!', 'success')
            return redirect(url_for('list_locations'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding location: {str(e)}', 'danger')
    return render_template('add_location.html')

@app.route('/locations/edit/<string:location_id>', methods=['GET', 'POST'])
def edit_location(location_id):
    location = Location.query.get_or_404(location_id)
    if request.method == 'POST':
        try:
            location.name = request.form['name']
            db.session.commit()
            flash('Location updated successfully!', 'success')
            return redirect(url_for('list_locations'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating location: {str(e)}', 'danger')
    return render_template('edit_location.html', location=location)

@app.route('/locations/delete/<string:location_id>', methods=['POST'])
def delete_location(location_id):
    location = Location.query.get_or_404(location_id)
    try:
        db.session.delete(location)
        db.session.commit()
        flash('Location deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting location: {str(e)}', 'danger')
    return redirect(url_for('list_locations'))

@app.route('/movements')
def list_movements():
    transfers = ProductMove.query.order_by(ProductMove.timestamp.desc()).all()
    buys = BuyMovement.query.order_by(BuyMovement.timestamp.desc()).all()
    sales = SaleMovement.query.order_by(SaleMovement.timestamp.desc()).all()
    return render_template('movements.html',
                         transfers=transfers,
                         buys=buys,
                         sales=sales,
                         products=Item.query.all(),
                         locations=Location.query.all())

@app.route('/movements/add', methods=['POST'])
def add_movement():
    try:
        movement_type = request.form['movement_type']
        
        if movement_type == 'buy':
            movement = BuyMovement(
                movement_id=str(uuid.uuid4()),
                product_id=request.form['product_id'],
                from_location='supplier',
                movement_qty=int(request.form['qty']),
                timestamp=datetime.utcnow()
            )
            # Update inventory
            product = Item.query.filter_by(product_id=request.form['product_id']).first()
            product.stock += int(request.form['qty'])
            
        elif movement_type == 'sale':
            product = Item.query.filter_by(product_id=request.form['product_id']).first()
            if product.stock < int(request.form['qty']):
                flash(f'Only {product.stock} units available!', 'danger')
                return redirect(url_for('list_movements'))
            
            movement = SaleMovement(
                movement_id=str(uuid.uuid4()),
                product_id=request.form['product_id'],
                to_location='customer',
                movement_qty=int(request.form['qty']),
                timestamp=datetime.utcnow()
            )
            product.stock -= int(request.form['qty'])
            
        elif movement_type == 'transfer':
            from_loc = request.form['from_location']
            to_loc = request.form['to_location']
            
            if from_loc == to_loc:
                flash('Cannot transfer to same location!', 'danger')
                return redirect(url_for('list_movements'))
                
            movement = ProductMove(
                product_id=request.form['product_id'],
                from_location=from_loc,
                to_location=to_loc,
                movement_qty=int(request.form['qty'])
            )
        
        db.session.add(movement)
        db.session.commit()
        flash(f'{movement_type.capitalize()} recorded!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('list_movements'))

@app.route('/movements/delete/<string:movement_type>/<string:movement_id>', methods=['POST'])
def delete_movement(movement_type, movement_id):
    try:
        if movement_type == 'transfer':
            movement = ProductMove.query.get_or_404(movement_id)
        elif movement_type == 'buy':
            movement = BuyMovement.query.get_or_404(movement_id)
            # Reverse inventory impact
            product = Item.query.filter_by(product_id=movement.product_id).first()
            product.stock -= movement.movement_qty
        elif movement_type == 'sale':
            movement = SaleMovement.query.get_or_404(movement_id)
            # Reverse inventory impact
            product = Item.query.filter_by(product_id=movement.product_id).first()
            product.stock += movement.movement_qty
        else:
            flash('Invalid movement type', 'danger')
            return redirect(url_for('list_movements'))
        
        db.session.delete(movement)
        db.session.commit()
        flash('Movement deleted!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error: {str(e)}', 'danger')
    return redirect(url_for('list_movements'))
@app.route('/report')
def report():
    locations = Location.query.all()
    products = Item.query.all()

    # Prepare the list of product names
    product_names = [p.product_name for p in products]
    
    # Prepare the dictionary to store the report data
    report_data = {}

    for location in locations:
        stock = {}
        for product in products:
            # Calculate the total stock for each product at each location
            total_buy_qty = db.session.query(db.func.sum(BuyMovement.movement_qty)).filter_by(
                product_id=product.product_id,
                from_location=location.location_id
            ).scalar() or 0

            total_sale_qty = db.session.query(db.func.sum(SaleMovement.movement_qty)).filter_by(
                product_id=product.product_id,
                to_location=location.location_id
            ).scalar() or 0

            total_transfer_in_qty = db.session.query(db.func.sum(ProductMove.movement_qty)).filter_by(
                product_id=product.product_id,
                to_location=location.location_id
            ).scalar() or 0

            total_transfer_out_qty = db.session.query(db.func.sum(ProductMove.movement_qty)).filter_by(
                product_id=product.product_id,
                from_location=location.location_id
            ).scalar() or 0

            # The available stock is calculated as:
            # Initial stock + Buy quantity - Sale quantity + Transfer-in quantity - Transfer-out quantity
            available_stock = total_buy_qty - total_sale_qty + total_transfer_in_qty - total_transfer_out_qty
            
            stock[product.product_name] = available_stock

        report_data[location.name] = stock

    return render_template('report.html', report_data=report_data, product_names=product_names)



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)