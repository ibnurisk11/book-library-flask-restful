# app.py

from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta # Import timedelta untuk tanggal kembali
from urllib.parse import quote_plus
from flask_cors import CORS

app = Flask(__name__)

# --- Konfigurasi Database MySQL---
DB_USER = 'go_user'
DB_PASSWORD = 'Sanders123!'
DB_HOST = '127.0.0.1'
DB_PORT = '3306'
DB_NAME = 'perpustakaan_db'

encoded_password = quote_plus(DB_PASSWORD)

app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
api = Api(app)
CORS(app)

# --- Model Database (Pastikan ini ada di bagian ini) ---

class TimestampMixin:
    """Mixin untuk kolom timestamp otomatis."""
    tanggal_dibuat = db.Column(db.DateTime, default=datetime.utcnow)
    tanggal_diupdate = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# (Model Author, Category, Book yang sudah ada)
class Author(db.Model, TimestampMixin):
    __tablename__ = 'authors'
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    tanggal_lahir = db.Column(db.Date, nullable=True)
    books = db.relationship('Book', backref='author', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'nama': self.nama,
            'tanggal_lahir': self.tanggal_lahir.strftime('%Y-%m-%d') if self.tanggal_lahir else None,
            'tanggal_dibuat': self.tanggal_dibuat.isoformat(),
            'tanggal_diupdate': self.tanggal_diupdate.isoformat()
        }

class Category(db.Model, TimestampMixin):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(50), unique=True, nullable=False)
    books = db.relationship('Book', backref='category', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'nama': self.nama,
            'tanggal_dibuat': self.tanggal_dibuat.isoformat(),
            'tanggal_diupdate': self.tanggal_diupdate.isoformat()
        }

class Book(db.Model, TimestampMixin):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    judul = db.Column(db.String(255), unique=True, nullable=False)
    tahun_terbit = db.Column(db.Integer, nullable=True)
    isbn = db.Column(db.String(20), unique=True, nullable=True)
    stok = db.Column(db.Integer, default=0, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('authors.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    borrowings = db.relationship('Borrowing', backref='book', lazy=True)

    def to_dict(self, include_relations=False):
        data = {
            'id': self.id,
            'judul': self.judul,
            'tahun_terbit': self.tahun_terbit,
            'isbn': self.isbn,
            'stok': self.stok,
            'author_id': self.author_id,
            'category_id': self.category_id,
            'tanggal_dibuat': self.tanggal_dibuat.isoformat(),
            'tanggal_diupdate': self.tanggal_diupdate.isoformat()
        }
        if include_relations:
            data['author'] = self.author.to_dict() if self.author else None
            data['category'] = self.category.to_dict() if self.category else None
        return data

# --- Model Member (Baru) ---
class Member(db.Model, TimestampMixin):
    __tablename__ = 'members'
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    alamat = db.Column(db.String(255), nullable=True)
    telepon = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=True)
    borrowings = db.relationship('Borrowing', backref='member', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'nama': self.nama,
            'alamat': self.alamat,
            'telepon': self.telepon,
            'email': self.email,
            'tanggal_registrasi': self.tanggal_dibuat.isoformat(),
            'tanggal_dibuat': self.tanggal_dibuat.isoformat(),
            'tanggal_diupdate': self.tanggal_diupdate.isoformat()
        }

# --- Model Borrowing (Baru) ---
class Borrowing(db.Model, TimestampMixin):
    __tablename__ = 'borrowings'
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    tanggal_peminjaman = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    tanggal_kembali_seharusnya = db.Column(db.Date, nullable=False)
    tanggal_pengembalian_aktual = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='dipinjam', nullable=False) # 'dipinjam', 'dikembalikan', 'terlambat'

    def to_dict(self, include_relations=False):
        data = {
            'id': self.id,
            'book_id': self.book_id,
            'member_id': self.member_id,
            'tanggal_peminjaman': self.tanggal_peminjaman.isoformat(),
            'tanggal_kembali_seharusnya': self.tanggal_kembali_seharusnya.isoformat(),
            'tanggal_pengembalian_aktual': self.tanggal_pengembalian_aktual.isoformat() if self.tanggal_pengembalian_aktual else None,
            'status': self.status,
            'tanggal_dibuat': self.tanggal_dibuat.isoformat(),
            'tanggal_diupdate': self.tanggal_diupdate.isoformat()
        }
        if include_relations:
            data['book'] = self.book.to_dict() if self.book else None
            data['member'] = self.member.to_dict() if self.member else None
        return data

# --- Resource API untuk setiap Model ---

# (Resource Author dan Category yang sudah ada)
class AuthorList(Resource):
    def get(self):
        authors = Author.query.all()
        return [author.to_dict() for author in authors], 200

    def post(self):
        data = request.get_json()
        if not data or 'nama' not in data:
            return {'message': 'Nama author is required.'}, 400
        
        if Author.query.filter_by(nama=data['nama']).first():
            return {'message': 'Author with this name already exists.'}, 409

        tanggal_lahir_str = data.get('tanggal_lahir')
        tanggal_lahir_obj = None
        if tanggal_lahir_str:
            try:
                tanggal_lahir_obj = datetime.strptime(tanggal_lahir_str, '%Y-%m-%d').date()
            except ValueError:
                return {'message': 'Invalid date format for tanggal_lahir. Use YYYY-MM-DD.'}, 400

        new_author = Author(
            nama=data['nama'],
            tanggal_lahir=tanggal_lahir_obj
        )
        db.session.add(new_author)
        db.session.commit()
        return new_author.to_dict(), 201

class AuthorResource(Resource):
    def get(self, author_id):
        author = Author.query.get_or_404(author_id)
        return author.to_dict(), 200

    def put(self, author_id):
        author = Author.query.get_or_404(author_id)
        data = request.get_json()
        if not data:
            return {'message': 'No update data provided'}, 400

        if 'nama' in data:
            author.nama = data['nama']
        if 'tanggal_lahir' in data:
            if data['tanggal_lahir'] is None:
                author.tanggal_lahir = None
            else:
                try:
                    author.tanggal_lahir = datetime.strptime(data['tanggal_lahir'], '%Y-%m-%d').date()
                except ValueError:
                    return {'message': 'Invalid date format for tanggal_lahir. Use YYYY-MM-DD.'}, 400

        db.session.commit()
        return author.to_dict(), 200

    def delete(self, author_id):
        author = Author.query.get_or_404(author_id)
        if author.books:
            return {'message': 'Cannot delete author with associated books. Delete books first.'}, 409
        db.session.delete(author)
        db.session.commit()
        return {'message': 'Author deleted successfully'}, 204

class CategoryList(Resource):
    def get(self):
        categories = Category.query.all()
        return [category.to_dict() for category in categories], 200

    def post(self):
        data = request.get_json()
        if not data or 'nama' not in data:
            return {'message': 'Nama category is required.'}, 400
        
        if Category.query.filter_by(nama=data['nama']).first():
            return {'message': 'Category with this name already exists.'}, 409

        new_category = Category(nama=data['nama'])
        db.session.add(new_category)
        db.session.commit()
        return new_category.to_dict(), 201

class CategoryResource(Resource):
    def get(self, category_id):
        category = Category.query.get_or_404(category_id)
        return category.to_dict(), 200

    def put(self, category_id):
        category = Category.query.get_or_404(category_id)
        data = request.get_json()
        if not data:
            return {'message': 'No update data provided'}, 400

        if 'nama' in data:
            category.nama = data['nama']
        
        db.session.commit()
        return category.to_dict(), 200

    def delete(self, category_id):
        category = Category.query.get_or_404(category_id)
        if category.books:
            return {'message': 'Cannot delete category with associated books. Delete books first.'}, 409
        db.session.delete(category)
        db.session.commit()
        return {'message': 'Category deleted successfully'}, 204

class BookList(Resource):
    def get(self):
        books = Book.query.all()
        return [book.to_dict(include_relations=False) for book in books], 200

    def post(self):
        data = request.get_json()
        required_fields = ['judul', 'author_id', 'category_id']
        if not all(field in data for field in required_fields):
            return {'message': f'Required fields are: {", ".join(required_fields)}'}, 400

        author = Author.query.get(data['author_id'])
        if not author:
            return {'message': f"Author with ID {data['author_id']} not found."}, 404
        category = Category.query.get(data['category_id'])
        if not category:
            return {'message': f"Category with ID {data['category_id']} not found."}, 404

        if 'isbn' in data and data['isbn'] and Book.query.filter_by(isbn=data['isbn']).first():
            return {'message': 'Book with this ISBN already exists.'}, 409
        if Book.query.filter_by(judul=data['judul']).first():
            return {'message': 'Book with this title already exists.'}, 409

        new_book = Book(
            judul=data['judul'],
            tahun_terbit=data.get('tahun_terbit'),
            isbn=data.get('isbn'),
            stok=data.get('stok', 0),
            author_id=data['author_id'],
            category_id=data['category_id']
        )
        db.session.add(new_book)
        db.session.commit()
        return new_book.to_dict(include_relations=True), 201

class BookResource(Resource):
    def get(self, book_id):
        book = Book.query.get_or_404(book_id)
        return book.to_dict(include_relations=True), 200

    def put(self, book_id):
        book = Book.query.get_or_404(book_id)
        data = request.get_json()
        if not data:
            return {'message': 'No update data provided'}, 400

        if 'judul' in data:
            book.judul = data['judul']
        if 'tahun_terbit' in data:
            book.tahun_terbit = data['tahun_terbit']
        if 'isbn' in data:
            if data['isbn'] and Book.query.filter(Book.id != book_id, Book.isbn == data['isbn']).first():
                return {'message': 'Another book with this ISBN already exists.'}, 409
            book.isbn = data['isbn']
        if 'stok' in data:
            book.stok = data['stok']
        if 'author_id' in data:
            author = Author.query.get(data['author_id'])
            if not author:
                return {'message': f"Author with ID {data['author_id']} not found."}, 404
            book.author_id = data['author_id']
        if 'category_id' in data:
            category = Category.query.get(data['category_id'])
            if not category:
                return {'message': f"Category with ID {data['category_id']} not found."}, 404
            book.category_id = data['category_id']

        db.session.commit()
        return book.to_dict(include_relations=True), 200

    def delete(self, book_id):
        book = Book.query.get_or_404(book_id)
        if book.borrowings:
            return {'message': 'Cannot delete book with active borrowings. Return all borrowings first.'}, 409
        db.session.delete(book)
        db.session.commit()
        return {'message': 'Book deleted successfully'}, 204

# --- Resource Member (Baru) ---
class MemberList(Resource):
    def get(self):
        members = Member.query.all()
        return [member.to_dict() for member in members], 200

    def post(self):
        data = request.get_json()
        required_fields = ['nama', 'telepon']
        if not all(field in data for field in required_fields):
            return {'message': f'Required fields are: {", ".join(required_fields)}'}, 400

        if Member.query.filter_by(telepon=data['telepon']).first():
            return {'message': 'Member with this phone number already exists.'}, 409
        if 'email' in data and data['email'] and Member.query.filter_by(email=data['email']).first():
            return {'message': 'Member with this email already exists.'}, 409

        new_member = Member(
            nama=data['nama'],
            alamat=data.get('alamat'),
            telepon=data['telepon'],
            email=data.get('email')
        )
        db.session.add(new_member)
        db.session.commit()
        return new_member.to_dict(), 201

class MemberResource(Resource):
    def get(self, member_id):
        member = Member.query.get_or_404(member_id)
        return member.to_dict(), 200

    def put(self, member_id):
        member = Member.query.get_or_404(member_id)
        data = request.get_json()
        if not data:
            return {'message': 'No update data provided'}, 400

        if 'nama' in data:
            member.nama = data['nama']
        if 'alamat' in data:
            member.alamat = data['alamat']
        if 'telepon' in data:
            if data['telepon'] and Member.query.filter(Member.id != member_id, Member.telepon == data['telepon']).first():
                return {'message': 'Another member with this phone number already exists.'}, 409
            member.telepon = data['telepon']
        if 'email' in data:
            if data['email'] and Member.query.filter(Member.id != member_id, Member.email == data['email']).first():
                return {'message': 'Another member with this email already exists.'}, 409
            member.email = data['email']

        db.session.commit()
        return member.to_dict(), 200

    def delete(self, member_id):
        member = Member.query.get_or_404(member_id)
        if member.borrowings:
            return {'message': 'Cannot delete member with active borrowings. Return all borrowings first.'}, 409
        db.session.delete(member)
        db.session.commit()
        return {'message': 'Member deleted successfully'}, 204

# --- Resource Borrowing (Baru) ---
class BorrowingList(Resource):
    def get(self):
        borrowings = Borrowing.query.all()
        # Mengembalikan dengan relasi agar lebih informatif
        return [borrowing.to_dict(include_relations=True) for borrowing in borrowings], 200

    def post(self):
        data = request.get_json()
        required_fields = ['book_id', 'member_id', 'durasi_peminjaman_hari'] # durasi_peminjaman_hari adalah input baru dari frontend
        if not all(field in data for field in required_fields):
            return {'message': f'Required fields are: {", ".join(required_fields)}'}, 400
        
        book = Book.query.get(data['book_id'])
        if not book:
            return {'message': f"Book with ID {data['book_id']} not found."}, 404
        if book.stok <= 0:
            return {'message': 'Book is out of stock.'}, 400
        
        member = Member.query.get(data['member_id'])
        if not member:
            return {'message': f"Member with ID {data['member_id']} not found."}, 404

        # Hitung tanggal_kembali_seharusnya
        try:
            durasi_peminjaman = int(data['durasi_peminjaman_hari'])
            if durasi_peminjaman <= 0:
                return {'message': 'Durasi peminjaman harus lebih dari 0 hari.'}, 400
        except ValueError:
            return {'message': 'Durasi peminjaman harus berupa angka.'}, 400
        
        tanggal_peminjaman = datetime.utcnow()
        tanggal_kembali_seharusnya = (tanggal_peminjaman + timedelta(days=durasi_peminjaman)).date()

        new_borrowing = Borrowing(
            book_id=data['book_id'],
            member_id=data['member_id'],
            tanggal_peminjaman=tanggal_peminjaman,
            tanggal_kembali_seharusnya=tanggal_kembali_seharusnya,
            status='dipinjam'
        )
        db.session.add(new_borrowing)
        
        # Kurangi stok buku
        book.stok -= 1
        
        db.session.commit()
        return new_borrowing.to_dict(include_relations=True), 201

class BorrowingResource(Resource):
    def get(self, borrowing_id):
        borrowing = Borrowing.query.get_or_404(borrowing_id)
        return borrowing.to_dict(include_relations=True), 200

    def put(self, borrowing_id):
        borrowing = Borrowing.query.get_or_404(borrowing_id)
        data = request.get_json()
        if not data:
            return {'message': 'No update data provided'}, 400

        # Hanya izinkan update status dan tanggal_pengembalian_aktual
        if 'status' in data:
            if data['status'] not in ['dipinjam', 'dikembalikan', 'terlambat']:
                return {'message': 'Invalid status. Must be "dipinjam", "dikembalikan", or "terlambat".'}, 400
            
            # Jika status diubah menjadi 'dikembalikan', set tanggal_pengembalian_aktual
            if data['status'] == 'dikembalikan' and not borrowing.tanggal_pengembalian_aktual:
                borrowing.tanggal_pengembalian_aktual = datetime.utcnow()
                # Tambah stok buku jika dikembalikan
                borrowing.book.stok += 1
            elif data['status'] != 'dikembalikan' and borrowing.tanggal_pengembalian_aktual:
                # Jika status diubah dari 'dikembalikan' ke lainnya (misal: 'dipinjam')
                # dan ada tanggal_pengembalian_aktual, bisa jadi error logika atau perlu dikurangi stok lagi.
                # Untuk kesederhanaan, kita hanya fokus pada flow 'dikembalikan'.
                pass # Atau tambahkan logika rollback stok jika diperlukan
            
            borrowing.status = data['status']

        db.session.commit()
        return borrowing.to_dict(include_relations=True), 200

    def delete(self, borrowing_id):
        borrowing = Borrowing.query.get_or_404(borrowing_id)
        # Jika peminjaman dihapus dan statusnya masih 'dipinjam', kembalikan stok buku
        if borrowing.status == 'dipinjam':
            book = Book.query.get(borrowing.book_id)
            if book:
                book.stok += 1
        
        db.session.delete(borrowing)
        db.session.commit()
        return {'message': 'Borrowing record deleted successfully'}, 204

# --- Endpoint API untuk setiap Resource ---
api.add_resource(AuthorList, '/authors')
api.add_resource(AuthorResource, '/authors/<int:author_id>')

api.add_resource(CategoryList, '/categories')
api.add_resource(CategoryResource, '/categories/<int:category_id>')

api.add_resource(BookList, '/books')
api.add_resource(BookResource, '/books/<int:book_id>')

api.add_resource(MemberList, '/members') # Endpoint baru
api.add_resource(MemberResource, '/members/<int:member_id>') # Endpoint baru

api.add_resource(BorrowingList, '/borrowings') # Endpoint baru
api.add_resource(BorrowingResource, '/borrowings/<int:borrowing_id>') # Endpoint baru


# --- Inisialisasi Database (Hanya untuk Development/Testing Awal) ---
with app.app_context():
    db.create_all()
    print("Database tables created/checked.")

if __name__ == '__main__':
    app.run(debug=True)
    print("Flask app is running...")