from flask import Flask, render_template, redirect, url_for, request, session, flash, abort
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from flask_mail import Mail
from datetime import timedelta
from data import db_session
from data.cart import Cart
from data.users import User
from data.product import Products
from data.product_image import ProductImage
from form.users import LoginForm, RegistrationForm
from form.product import NewProductsForm, Supply
from waitress import serve
from contextlib import contextmanager
from services.otp_service import create_otp, verify_otp
from services.rate_limit import check_rate, set_rate
from utils.mail_utils import send_otp_email
import os
import uuid

# открываем сессию бд и закрываем её после использования
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
# папка куда сохраняются фото товаров
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}

app.config.update(
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_PORT=os.getenv("MAIL_PORT"),
    MAIL_USE_TLS=True,
    MAIL_USERNAME= os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_DEFAULT_SENDER='no-reply@mpit.su'
)

mail = Mail(app)

def save_photo(file):
    # генерируем уникальное имя файла чтобы не было конфликтов
    ext = file.filename.rsplit('.', 1)[-1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return filename


login_manager = LoginManager()
login_manager.init_app(app)

# создаём файл бд и все таблицы если их ещё нет
db_session.global_init("db/blogs.sqlite")

CATEGORIES = ['Электроника', 'Одежда', 'Книги']


def cart_count():
    # для незалогиненных возвращаем 0
    if not current_user.is_authenticated:
        return 0
    with session_scope() as db_sess:
        items = db_sess.query(Cart).filter(Cart.user_id == current_user.id).all()
        return sum(item.quantity for item in items)



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
    return render_template('index.html', featured=[], cart_count=cart_count())


@app.route('/catalog')
def catalog():
    with session_scope() as db_sess:
        products = db_sess.query(Products).all()
        # собираем словарь product_id -> url фото для удобного доступа в шаблоне
        images = {img.product_id: url_for('static', filename=f'uploads/{img.filename}')
                  for img in db_sess.query(ProductImage).all()}
    is_staff = current_user.is_authenticated and current_user.role in ['admin', 'manager', 'warehouse']
    return render_template('catalog.html', products=products, images=images,
                           is_staff=is_staff, cart_count=cart_count())


@app.route('/product/<int:product_id>')
def product(product_id):
    with session_scope() as db_sess:
        item = db_sess.get(Products, product_id)
        if item is None:
            return render_template('404.html'), 404
        image = db_sess.query(ProductImage).filter_by(product_id=product_id).first()
        image_url = url_for('static', filename=f'uploads/{image.filename}') if image else None
        return render_template('product.html', product=item, image_url=image_url, cart_count=cart_count())


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
        # если товар уже в корзине увеличиваем количество, иначе добавляем новую запись
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
        # сначала удаляем связанные записи чтобы не было ошибок целостности бд
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
                return render_template('add_product.html', form=form, cart_count=cart_count())
            product = Products(
                name=form.name.data,
                price=form.price.data,
                quantity=form.quantity.data
            )
            db_sess.add(product)
            # flush нужен чтобы получить product.id до commit и привязать к нему фото
            db_sess.flush()
            if form.photo.data and form.photo.data.filename:
                filename = save_photo(form.photo.data)
                img = ProductImage(product_id=product.id, filename=filename)
                db_sess.add(img)
            db_sess.commit()
            flash(f'Товар «{product.name}» добавлен.')
            return redirect(url_for('catalog'))
    return render_template('add_product.html', form=form, cart_count=cart_count())


@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    if request.method == 'POST':
        session.pop('cart', None)
        flash('Заказ оформлен!')
        return redirect(url_for('index'))
    return render_template('checkout.html', total=0, cart_count=cart_count())


# flask-login вызывает это при каждом запросе чтобы загрузить объект пользователя из куки
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
    return render_template('login.html', form=form, cart_count=cart_count())


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        with session_scope() as db_sess:
            if db_sess.query(User).filter(User.email == form.email.data).first():
                return render_template('register.html', title='Регистрация',
                                       form=form, message='Такой пользователь уже есть')
            user = User(
                name=form.name.data,
                email=form.email.data,
                # если передана неизвестная роль назначаем обычного пользователя
                role=form.role.data if form.role.data in ['user', 'manager', 'warehouse', 'support', 'courier'] else 'user'
            )
            user.set_password(form.password.data)
            db_sess.add(user)
            db_sess.commit()
            login_user(user)
            return redirect(url_for('account'))
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/account')
@login_required
def account():
    return render_template('account.html', user=current_user, cart_count=cart_count())


@app.route('/stores')
def stores():
    shops = [
        {'name': 'МойМагазин Центральный', 'address': 'Москва, ул. Тверская, 1',      'lat': 55.758400, 'lng': 37.612151},
        {'name': 'МойМагазин Север',       'address': 'Москва, Ленинградский пр., 80', 'lat': 55.803118, 'lng': 37.530887},
        {'name': 'МойМагазин Юг',          'address': 'Москва, Варшавское ш., 129',    'lat': 55.645300, 'lng': 37.621564},
    ]
    return render_template('stores.html', shops=shops, cart_count=cart_count())


@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


if __name__ == '__main__':
    serve(app, host='127.0.0.1', port=8000)
