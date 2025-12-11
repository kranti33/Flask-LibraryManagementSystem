from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..models import Book
from .. import db
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if current_user.role != 'admin':
            flash("Admin access required.", "danger")
            return redirect(url_for('main.home'))
        return func(*args, **kwargs)
    return wrapper

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    books = Book.query.all()
    return render_template('admin/dashboard.html', books=books)

@admin_bp.route('/add_book', methods=['GET', 'POST'])
@login_required
@admin_required
def add_book():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        genre = request.form['genre']
        new_book = Book(title=title, author=author, genre=genre)
        db.session.add(new_book)
        db.session.commit()
        flash('Book added successfully!', 'success')
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/add_book.html')

@admin_bp.route('/edit_book/<int:book_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)
    if request.method == 'POST':
        book.title = request.form['title']
        book.author = request.form['author']
        book.genre = request.form['genre']
        book.description = request.form['description']
        db.session.commit()
        flash('Book updated!', 'success')
        return redirect(url_for('admin.dashboard'))
    return render_template('admin/edit_book.html', book=book)

@admin_bp.route('/delete_book/<int:book_id>')
@login_required
@admin_required
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    flash('Book deleted!', 'success')
    return redirect(url_for('admin.dashboard'))
