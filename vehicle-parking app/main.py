from flask import Flask, request, render_template, redirect, flash, session, url_for
from database import app, db, User, ParkingLot, BookingHistory, create_auto_admin, ParkingSpot
from datetime import datetime

# ---------- Home & Auth ----------
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        user = User.query.filter_by(username=u).first()

        if user:
            if user.is_admin:
                session['username'] = u
                return redirect('/admin_dashboard')

            if user.password == p:
                session['username'] = u
                return redirect(f'/dashboard/{u}')
            else:
                flash('Incorrect password')
        else:
            flash('User not found. Please register.')
            return redirect('/register')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.form
        if User.query.filter_by(username=data['username']).first():
            flash('User already exists.'); return redirect('/register')

        db.session.add(User(username=data['username'], password=data['password'],
                            is_admin=False, pincode=data['pincode'], address=data['address']))
        db.session.commit(); flash('Registered successfully. Please log in.')
        return redirect('/login')
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Logged out.'); return redirect('/login')


# ---------- User Dashboard & Booking ----------
@app.route('/dashboard/<string:username>')
def dashboard(username):
    user = User.query.filter_by(username=username).first_or_404()
    lots = ParkingLot.query.all()
    for lot in lots:
        lot.available_spots = ParkingSpot.query.filter_by(lot_id=lot.id, status='A').count()
    bookings = BookingHistory.query.filter_by(user_id=user.id).all()
    return render_template('user_dashboard.html', username=username, parking_lots=lots, bookings=bookings)

@app.route('/reserve/<int:lot_id>/<string:username>', methods=['GET', 'POST'])
def show_reserve_form(lot_id, username):
    user, lot = User.query.filter_by(username=username).first(), ParkingLot.query.get(lot_id)
    spot = ParkingSpot.query.filter_by(lot_id=lot_id, status='A').first()
    if not (user and lot and spot): flash('No available spot.'); return redirect(f'/dashboard/{username}')

    if request.method == 'POST':
        spot.status = 'O'
        db.session.add(BookingHistory(user_id=user.id, lot_id=lot.id, spot_id=spot.id,
                                      start_time=datetime.now(), vehicle_number=request.form['vehicle_number']))
        db.session.commit(); flash(f"Spot {spot.spot_number} reserved!"); return redirect(f'/dashboard/{username}')
    return render_template('reserve_form.html', lot=lot, spot=spot, username=username)

@app.route('/release/<int:booking_id>/<string:username>', methods=['POST'])
def release(booking_id, username):
    booking = BookingHistory.query.get(booking_id)
    if not booking or booking.end_time: flash("Invalid release."); return redirect(f'/dashboard/{username}')

    booking.end_time = datetime.now()
    hrs = (booking.end_time - booking.start_time).total_seconds() / 3600
    lot = ParkingLot.query.get(booking.lot_id)
    booking.cost = round(hrs * lot.price, 2)

    spot = ParkingSpot.query.get(booking.spot.spot_number); spot.status = 'A'
    db.session.commit(); flash(f"Spot released. Cost: ₹{booking.cost}")
    return redirect(f'/dashboard/{username}')


# ---------- Summary ----------
@app.route('/summary/<string:username>')
def summary(username):
    user = User.query.filter_by(username=username).first_or_404()
    bookings = BookingHistory.query.filter_by(user_id=user.id).all()

    total_hours = total_cost = 0
    labels, costs = [], []
    for b in bookings:
        if b.end_time:
            hrs = (b.end_time - b.start_time).total_seconds() / 3600
            total_hours += hrs; total_cost += b.cost
            labels.append(b.start_time.strftime('%d %b %Y')); costs.append(b.cost)

    return render_template('summary.html', username=username,
                           total_hours=total_hours, total_cost=total_cost,
                           bookings=bookings, labels=labels, costs=costs)


# ---------- Admin Views ----------
@app.route('/admin_dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html',
                           parking_lots=ParkingLot.query.all(),
                           users=User.query.filter_by(is_admin=False).all())

@app.route('/admin/add_lot', methods=['GET', 'POST'])
def add_lot():
    if request.method == 'POST':
        data = request.form
        lot = ParkingLot(name=data['name'], location=data['location'],
                         price=float(data['price']), total_spots=int(data['total_spots']))
        db.session.add(lot); db.session.commit()

        create_spots_for_lot(lot.id, lot.total_spots)
        flash('Lot added.')
        return redirect('/admin_dashboard')
    return render_template('add_parking_lot.html')

@app.route('/edit_lot/<int:lot_id>', methods=['GET', 'POST'])
def edit_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    if request.method == 'POST':
        new_total = int(request.form['total_spots'])
        spots = ParkingSpot.query.filter_by(lot_id=lot.id).order_by(ParkingSpot.spot_number).all()
        current = len(spots)

        if new_total > current:
            # Find current max spot number or 0 if none
            max_spot_number = db.session.query(db.func.max(ParkingSpot.spot_number)) \
                .filter_by(lot_id=lot.id).scalar() or 0
            
            # Add new spots with unique spot numbers continuing from max_spot_number
            for i in range(1, new_total - current + 1):
                new_spot = ParkingSpot(
                    lot_id=lot.id,
                    status='A',
                    spot_number=max_spot_number + i
                )
                db.session.add(new_spot)

        elif new_total < current:
            # Get free spots ordered by descending spot_number to delete highest spots first
            free_spots = ParkingSpot.query.filter_by(lot_id=lot.id, status='A') \
                .order_by(ParkingSpot.spot_number.desc()).all()
            if len(free_spots) < (current - new_total):
                flash('Cannot reduce spots. Some are occupied.')
                return redirect('/admin_dashboard')
            for spot in free_spots[:current - new_total]:
                db.session.delete(spot)

        # Update lot details
        lot.name = request.form['name']
        lot.location = request.form['location']
        lot.price = float(request.form['price'])
        lot.total_spots = new_total

        db.session.flush()  # Flush changes to DB before renumbering

        # Re-fetch all spots and renumber from 1 to new_total consecutively
        all_spots = ParkingSpot.query.filter_by(lot_id=lot.id).order_by(ParkingSpot.spot_number).all()
        for idx, spot in enumerate(all_spots, start=1):
            spot.spot_number = idx

        db.session.commit()
        flash('Lot updated.')
        return redirect('/admin_dashboard')

    return render_template('edit_lot.html', lot=lot)



@app.route('/delete_lot/<int:lot_id>')
def delete_lot(lot_id):
    if ParkingSpot.query.filter_by(lot_id=lot_id, status='O').first():
        flash('Cannot delete lot with occupied spots.'); return redirect('/admin_dashboard')
    ParkingSpot.query.filter_by(lot_id=lot_id).delete()
    db.session.delete(ParkingLot.query.get(lot_id))
    db.session.commit(); flash('Lot deleted.')
    return redirect('/admin_dashboard')

def create_spots_for_lot(lot_id, number_of_spots):
    existing_spots = ParkingSpot.query.filter_by(lot_id=lot_id).count()
    for i in range(number_of_spots):
        spot = ParkingSpot(
            lot_id=lot_id,
            spot_number=existing_spots + i + 1,
            status='A'
        )
        db.session.add(spot)
    db.session.commit()

# ---------- Admin Spot & User View ----------
@app.route('/view_spots/<int:lot_id>')
def view_spots(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    spots = ParkingSpot.query.filter_by(lot_id=lot_id).order_by(ParkingSpot.spot_number).all()

    for s in spots:
        s.user = s.vehicle_number = None
        if s.status == 'O':
            b = BookingHistory.query.filter_by(spot_id=s.id).order_by(BookingHistory.id.desc()).first()
            if b:
                s.user, s.vehicle_number = b.user, b.vehicle_number

    return render_template('admin_view_spot.html',
                           parking_lots=ParkingLot.query.all(),
                           users=User.query.filter_by(is_admin=False).all(),
                           selected_lot=lot, parking_spots=spots)


@app.route('/admin_users')
def admin_users():
    users = User.query.filter_by(is_admin=False).all()
    user_spots = {}; user_vehicles = {}

    for u in users:
        bookings = BookingHistory.query.filter_by(user_id=u.id).all()
        spots = []; vehicles = set()
        for b in bookings:
            vehicles.add(b.vehicle_number)
            spot = ParkingSpot.query.get(b.spot_id)
            lot = ParkingLot.query.get(spot.lot_id) if spot else None
            if lot: spots.append((spot.id, lot.name))
        user_spots[u.id], user_vehicles[u.id] = spots, vehicles

    return render_template('admin_users.html', users=users,
                           user_spots_lots=user_spots, user_vehicles=user_vehicles)


@app.route('/admin/dashboard/summary')
def admin_summary():
    total = ParkingSpot.query.count()
    occupied = ParkingSpot.query.filter_by(status='O').count()
    revenue = db.session.query(db.func.sum(BookingHistory.cost)).scalar() or 0
    return render_template('admin_summary.html', occupied=occupied,
                           unoccupied=total - occupied, total_revenue=revenue)



if __name__ == '__main__':
    create_auto_admin()
    app.run(debug=True)
















