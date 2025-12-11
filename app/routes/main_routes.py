from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..models import Book, BorrowRecord
from .. import db
from werkzeug.security import generate_password_hash

main_bp = Blueprint('main', __name__)

# Home page showing all books
@main_bp.route('/')
@login_required
def home():
    books = Book.query.all()
    return render_template('home.html', books=books)

# Borrow a book
@main_bp.route('/borrow/<int:book_id>', methods=['GET', 'POST'])
@login_required
def borrow(book_id):
    book = Book.query.get_or_404(book_id)

    if not book.available:
        flash('Sorry, this book is already borrowed.', 'danger')
        return redirect(url_for('main.home'))

    if request.method == 'POST':
        borrow_record = BorrowRecord(
            user_id=current_user.id,
            book_id=book.id,
            borrow_date=datetime.utcnow(),
            due_date=datetime.utcnow() + timedelta(weeks=2)  # always set due_date
        )
        db.session.add(borrow_record)
        book.available = False
        db.session.commit()

        return redirect(url_for('main.borrow_confirmation', borrow_id=borrow_record.id))

    due_date = datetime.utcnow() + timedelta(weeks=2)
    return render_template('borrow.html', book=book, due_date=due_date)

# Confirmation page after borrowing
@main_bp.route('/borrow/confirmation/<int:borrow_id>')
@login_required
def borrow_confirmation(borrow_id):
    borrow_record = BorrowRecord.query.get_or_404(borrow_id)
    due_date = borrow_record.due_date or (borrow_record.borrow_date + timedelta(weeks=2))
    return render_template('borrow_confirmation.html', borrow=borrow_record, due_date=due_date)

# User profile page
@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile_page():
    if request.method == 'POST':
        # Update profile picture
        if 'profile_image' in request.files:
            image = request.files['profile_image']
            if image.filename != '':
                image_path = f'profile_pics/{current_user.id}_{image.filename}'
                image.save(f'static/{image_path}')
                current_user.profile_image = image_path
                db.session.commit()
                flash('Profile picture updated!', 'success')

        # Update password
        new_password = request.form.get('new_password')
        if new_password:
            current_user.password = generate_password_hash(new_password)
            db.session.commit()
            flash('Password updated!', 'success')

        return redirect(url_for('main.profile_page'))

    # Fetch borrowed books and ensure due_date is never None
    borrowed_records = BorrowRecord.query.filter_by(user_id=current_user.id).all()
    borrowed_books = []
    for record in borrowed_records:
        due_date = record.due_date or (record.borrow_date + timedelta(weeks=2))
        borrowed_books.append({
            'book': record.book,
            'borrow_date': record.borrow_date,
            'due_date': due_date
        })

    return render_template('profile.html', borrowed_books=borrowed_books, datetime=datetime)

@main_bp.route('/return/<int:borrow_id>', methods=['POST'])
@login_required
def return_book(borrow_id):
    borrow = Borrow.query.get_or_404(borrow_id)
    if borrow.user_id != current_user.id:
        flash("You cannot return this book.", "danger")
        return redirect(url_for('main.profile_page'))

    db.session.delete(borrow)
    db.session.commit()
    flash(f"Book '{borrow.book.title}' returned successfully!", "success")
    return redirect(url_for('main.profile_page'))
