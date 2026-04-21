from flask import Flask, render_template, redirect, url_for, request, session, flash, abort
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from flask_mail import Mail
from datetime import timedelta
from data import db_session
from data.cart import Cart
from data.users import User
from data.product import Products
from data.product_image import ProductImage
from form.users import LoginForm, RegistrationForm, StaffRegistrationForm
from data.employee import Employee
from form.product import NewProductsForm, Supply
from form.store import StoreForm
from data.store import Store
from data.review import Review
from waitress import serve
from contextlib import contextmanager
from services.otp_service import create_otp, verify_otp
from services.rate_limit import check_rate, set_rate
from utils.mail_utils import send_otp_email
import os
import uuid


@contextmanager
def session_scope():
    db_sess = db_session.create_session()
    try:
        yield db_sess
    finally:
        db_sess.close()


app = Flask(__name__)
app.secret_key = 'dev-secret-key'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}

app.config.update(
    MAIL_SERVER="localhost",
    MAIL_PORT = 25,
    MAIL_USE_TLS = False,
    MAIL_USE_SSL = False,
    MAIL_USERNAME = None,
    MAIL_PASSWORD = None
)

mail = Mail(app)


def save_photo(file):
    ext = file.filename.rsplit('.', 1)[-1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return filename


login_manager = LoginManager()
login_manager.init_app(app)

db_session.global_init("db/blogs.sqlite")

CATEGORIES = ['Электроника', 'Одежда', 'Книги']


def cart_count():
    if not current_user.is_authenticated:
        return 0
    with session_scope() as db_sess:
        items = db_sess.query(Cart).filter(Cart.user_id == current_user.id).all()
        return sum(item.quantity for item in items)


@app.context_processor
def inject_cart_count():
    return dict(cart_count=cart_count())


@app.route('/auth/request-code', methods=['POST'])
def request_code():
    email = request.json['email']

    if check_rate(email):
        return {"error": "too_many_requests"}, 429

    code = create_otp(email)
    send_otp_email(mail, email, code)
    set_rate(email)

    return {"status": "sent"}


@app.route('/auth/verify', methods=['POST'])
def verify():
    email = request.json['email']
    code = request.json['code']

    result = verify_otp(email, code)

    if result == "expired":
        return {"error": "expired"}, 400
    if result == "blocked":
        return {"error": "too_many_attempts"}, 429
    if result == "invalid":
        return {"error": "invalid"}, 400

    with session_scope() as db_sess:
        user = db_sess.query(User).filter(User.email == email).first()
        if not user:
            return {"error": "user not found"}, 404
        login_user(user, remember=True)

    return {"status": "logged_in"}


@app.route('/')
def index():
    return render_template('index.html', featured=[])


@app.route('/catalog')
def catalog():
    q = request.args.get('q', '').strip()
    selected_category = request.args.get('category', '')
    with session_scope() as db_sess:
        query = db_sess.query(Products)
        if q:
            query = query.filter(Products.name.ilike(f'%{q}%'))
        products = query.all()
        # картинки собираем заранее, чтобы не делать запрос на каждый товар
        images = {img.product_id: url_for('static', filename=f'uploads/{img.filename}')
                  for img in db_sess.query(ProductImage).all()}
        all_reviews = db_sess.query(Review).all()
    ratings = {}
    for rev in all_reviews:
        ratings.setdefault(rev.product_id, []).append(rev.rating)
    ratings = {pid: round(sum(vals) / len(vals), 1) for pid, vals in ratings.items()}
    is_staff = current_user.is_authenticated and current_user.role in ['admin', 'manager', 'warehouse']
    return render_template('catalog.html', products=products, images=images,
                           is_staff=is_staff, ratings=ratings, q=q,
                           categories=CATEGORIES, selected_category=selected_category)


@app.route('/product/<int:product_id>')
def product(product_id):
    with session_scope() as db_sess:
        item = db_sess.get(Products, product_id)
        if item is None:
            return render_template('404.html'), 404
        image = db_sess.query(ProductImage).filter_by(product_id=product_id).first()
        image_url = url_for('static', filename=f'uploads/{image.filename}') if image else None
        reviews = db_sess.query(Review, User).join(User, Review.user_id == User.id)\
            .filter(Review.product_id == product_id).order_by(Review.created_date.desc()).all()
        reviews = [{'review': r, 'user': u} for r, u in reviews]
        avg = round(sum(row['review'].rating for row in reviews) / len(reviews), 1) if reviews else None
        user_reviewed = current_user.is_authenticated and any(
            row['review'].user_id == current_user.id for row in reviews)
        return render_template('product.html', product=item, image_url=image_url,
                               reviews=reviews, avg=avg, user_reviewed=user_reviewed)


@app.route('/product/<int:product_id>/review', methods=['POST'])
@login_required
def add_review(product_id):
    rating = request.form.get('rating', type=int)
    text = request.form.get('text', '').strip()
    if not rating or not (1 <= rating <= 5):
        flash('Укажите оценку от 1 до 5.')
        return redirect(url_for('product', product_id=product_id))
    with session_scope() as db_sess:
        already = db_sess.query(Review).filter_by(product_id=product_id, user_id=current_user.id).first()
        if already:
            flash('Вы уже оставили отзыв на этот товар.')
            return redirect(url_for('product', product_id=product_id))
        rev = Review(product_id=product_id, user_id=current_user.id, rating=rating, text=text or None)
        db_sess.add(rev)
        db_sess.commit()
    flash('Отзыв добавлен.')
    return redirect(url_for('product', product_id=product_id))


@app.route('/product/<int:product_id>/reviews/data')
def reviews_data(product_id):
    with session_scope() as db_sess:
        rows = db_sess.query(Review, User).join(User, Review.user_id == User.id)\
            .filter(Review.product_id == product_id).order_by(Review.created_date.asc()).all()
        data = [{'id': r.id, 'user': u.name, 'user_id': r.user_id,
                 'rating': r.rating, 'text': r.text or '',
                 'date': r.created_date.strftime('%d.%m.%Y')} for r, u in rows]
    return {'reviews': data}


@app.route('/product/<int:product_id>/review/delete', methods=['POST'])
@login_required
def delete_review(product_id):
    with session_scope() as db_sess:
        rev = db_sess.query(Review).filter_by(product_id=product_id, user_id=current_user.id).first()
        if rev:
            db_sess.delete(rev)
            db_sess.commit()
    return redirect(url_for('product', product_id=product_id))


@app.route('/cart')
@login_required
def cart():
    with session_scope() as db_sess:
        items = db_sess.query(Cart).filter_by(user_id=current_user.id).all()
        result = []
        total = 0
        for item in items:
            product = db_sess.get(Products, item.product_id)
            subtotal = product.price * item.quantity
            result.append({'product': product, 'qty': item.quantity, 'subtotal': subtotal})
            total += subtotal
        return render_template('cart.html', items=result, total=total)


@app.route('/cart/add/<int:product_id>', methods=['POST'])
@login_required
def cart_add(product_id):
    with session_scope() as db_sess:
        item = db_sess.query(Cart).filter_by(product_id=product_id, user_id=current_user.id).first()
        if item:
            item.quantity += 1
        else:
            item = Cart(user_id=current_user.id, product_id=product_id, quantity=1)
            db_sess.add(item)
        db_sess.commit()
    return redirect(request.referrer or url_for('catalog'))


@app.route('/cart/remove/<int:product_id>', methods=['POST'])
@login_required
def cart_remove(product_id):
    with session_scope() as db_sess:
        item = db_sess.query(Cart).filter_by(product_id=product_id, user_id=current_user.id).first()
        if item:
            db_sess.delete(item)
            db_sess.commit()
    return redirect(url_for('cart'))


@app.route('/cart/clear', methods=['POST'])
@login_required
def cart_clear():
    with session_scope() as db_sess:
        db_sess.query(Cart).filter_by(user_id=current_user.id).delete()
        db_sess.commit()
    return redirect(url_for('cart'))


@app.route('/product/delete/<int:product_id>', methods=['POST'])
@login_required
def product_delete(product_id):
    if current_user.role not in ['admin', 'manager', 'warehouse']:
        abort(403)
    with session_scope() as db_sess:
        # сначала чистим картинки и корзину, иначе будет ошибка внешнего ключа
        db_sess.query(ProductImage).filter_by(product_id=product_id).delete()
        db_sess.query(Cart).filter_by(product_id=product_id).delete()
        product = db_sess.get(Products, product_id)
        if product:
            db_sess.delete(product)
            db_sess.commit()
            flash(f'Товар «{product.name}» удалён.')
    return redirect(url_for('catalog'))


@app.route('/supply', methods=['GET', 'POST'])
@login_required
def supply():
    if current_user.role not in ['admin', 'manager', 'warehouse']:
        abort(403)
    form = Supply()
    if form.validate_on_submit():
        with session_scope() as db_sess:
            product = db_sess.query(Products).filter(Products.name == form.name.data).first()
            if product:
                return render_template('supply.html', form=form)
    return render_template('supply.html', form=form)


@app.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    if current_user.role not in ['admin', 'manager', 'warehouse']:
        abort(403)
    form = NewProductsForm()
    if form.validate_on_submit():
        with session_scope() as db_sess:
            if db_sess.query(Products).filter(Products.name == form.name.data).first():
                flash('Товар с таким названием уже существует.')
                return render_template('add_product.html', form=form)
            product = Products(
                name=form.name.data,
                price=form.price.data,
                quantity=form.quantity.data
            )
            db_sess.add(product)
            db_sess.flush()  # нужен id до коммита, чтобы привязать фото
            if form.photo.data and form.photo.data.filename:
                filename = save_photo(form.photo.data)
                img = ProductImage(product_id=product.id, filename=filename)
                db_sess.add(img)
            db_sess.commit()
            flash(f'Товар «{product.name}» добавлен.')
            return redirect(url_for('catalog'))
    return render_template('add_product.html', form=form)


@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    if request.method == 'POST':
        session.pop('cart', None)
        flash('Заказ оформлен!')
        return redirect(url_for('index'))
    return render_template('checkout.html', total=0)


@login_manager.user_loader
def load_user(user_id):
    with session_scope() as db_sess:
        return db_sess.get(User, user_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        with session_scope() as db_sess:
            user = db_sess.query(User).filter(User.email == form.email.data).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember_me.data)
                return redirect('/')
            return render_template('login.html', message='Неправильный логин или пароль', form=form)
    return render_template('login.html', form=form)


def _render_register(message=None, active_tab='buyer', buyer_form=None, staff_form=None):
    return render_template('register.html',
                           buyer_form=buyer_form or RegistrationForm(),
                           staff_form=staff_form or StaffRegistrationForm(),
                           message=message,
                           active_tab=active_tab)


@app.route('/register', methods=['GET', 'POST'])
def register():
    buyer_form = RegistrationForm()
    if buyer_form.validate_on_submit():
        with session_scope() as db_sess:
            if db_sess.query(User).filter(User.email == buyer_form.email.data).first():
                return _render_register(message='Такой пользователь уже есть', buyer_form=buyer_form)
            user = User(name=buyer_form.name.data, email=buyer_form.email.data, role='user')
            user.set_password(buyer_form.password.data)
            db_sess.add(user)
            db_sess.commit()
            login_user(user)
            return redirect(url_for('account'))
    return _render_register(buyer_form=buyer_form)


@app.route('/register/staff', methods=['GET', 'POST'])
def register_staff():
    staff_form = StaffRegistrationForm()
    if staff_form.validate_on_submit():
        with session_scope() as db_sess:
            if db_sess.query(User).filter(User.email == staff_form.email.data).first():
                return _render_register(message='Пользователь с таким email уже существует',
                                        active_tab='staff', staff_form=staff_form)
            user = User(name=staff_form.name.data, email=staff_form.email.data, role=staff_form.role.data)
            user.set_password(staff_form.password.data)
            db_sess.add(user)
            db_sess.flush()
            emp = Employee(
                user_id=user.id,
                position=dict(staff_form.role.choices)[staff_form.role.data],
                employee_code=staff_form.code.data,
            )
            db_sess.add(emp)
            db_sess.commit()
            login_user(user)
            return redirect(url_for('account'))
    return _render_register(active_tab='staff', staff_form=staff_form)


@app.route('/staff')
@login_required
def staff_list():
    if current_user.role not in ['admin', 'manager']:
        abort(403)
    with session_scope() as db_sess:
        employees = db_sess.query(Employee, User).join(User, Employee.user_id == User.id).all()
        staff = [{'emp': e, 'user': u} for e, u in employees]
    return render_template('staff_list.html', staff=staff)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/account')
@login_required
def account():
    return render_template('account.html', user=current_user)


@app.route('/stores', methods=['GET', 'POST'])
def stores():
    form = StoreForm()
    is_staff = current_user.is_authenticated and current_user.role in ['admin', 'manager', 'warehouse']
    if form.validate_on_submit():
        if not is_staff:
            abort(403)
        with session_scope() as db_sess:
            store = Store(
                name=form.name.data,
                address=form.address.data,
                lat=form.lat.data,
                lng=form.lng.data,
            )
            db_sess.add(store)
            db_sess.commit()
            flash(f'Магазин «{store.name}» добавлен.')
        return redirect(url_for('stores'))
    with session_scope() as db_sess:
        shops = db_sess.query(Store).all()
        shops = [{'id': s.id, 'name': s.name, 'address': s.address, 'lat': s.lat, 'lng': s.lng} for s in shops]
    return render_template('stores.html', shops=shops, form=form, is_staff=is_staff)


@app.route('/stores/delete/<int:store_id>', methods=['POST'])
@login_required
def store_delete(store_id):
    if current_user.role not in ['admin', 'manager', 'warehouse']:
        abort(403)
    with session_scope() as db_sess:
        store = db_sess.get(Store, store_id)
        if store:
            db_sess.delete(store)
            db_sess.commit()
            flash(f'Магазин «{store.name}» удалён.')
    return redirect(url_for('stores'))


@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


if __name__ == '__main__':
    serve(app, host='127.0.0.1', port=5700)
