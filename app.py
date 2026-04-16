from flask import Flask, render_template, redirect, url_for, request, session, flash, abort
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from datetime import timedelta
from data import db_session
from data.cart import Cart
from data.users import User
from data.product import Products
from form.users import LoginForm, RegistrationForm
from form.product import NewProductsForm, Supply
from waitress import serve
from contextlib import contextmanager

@contextmanager
def session_scope():
    session = db_session.create_session()
    try:
        yield session
    finally:
        session.close()
app = Flask(__name__)
app.secret_key = 'dev-secret-key'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

login_manager = LoginManager()
login_manager.init_app(app)

db_session.global_init("db/blogs.sqlite")
PRODUCTS = []

CATEGORIES = ['Электроника', 'Одежда', 'Книги']


def get_cart():
    return session.get('cart', {})


def cart_count():
    if not current_user.is_authenticated:
        return 0

    with session_scope() as db_sess:
        items = db_sess.query(Cart).filter(Cart.user_id == current_user.id).all()

        return sum(item.quantity for item in items)


@contextmanager
def session_scope():
    session = db_session.create_session()
    try:
        yield session
    finally:
        session.close()
# Маршруты

@app.route('/')
def index():
    featured = PRODUCTS[:3]
    return render_template('index.html', featured=featured, cart_count=cart_count())


@app.route('/catalog')
def catalog():
    with session_scope() as db_sess:
        products = db_sess.query(Products).all()

    return render_template('catalog.html', products=products, cart_count=cart_count())



@app.route('/product/<int:product_id>')
def product(product_id):
    item = next((p for p in PRODUCTS if p['id'] == product_id), None)
    if item is None:
        return render_template('404.html'), 404
    return render_template('product.html', product=item, cart_count=cart_count())


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

            result.append({
                'product': product,
                'qty': item.quantity,
                'subtotal': subtotal
            })

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
            item = Cart(
                user_id=current_user.id,
                product_id=product_id,
                quantity=1,
            )
            db_sess.add(item)
        db_sess.commit()
    return redirect(request.referrer or url_for('catalog'))


@app.route('/cart/remove/<int:product_id>', methods=['POST'])
@login_required
def cart_remove(product_id):
    cart = session.get('cart', {})
    cart.pop(str(product_id), None)
    session['cart'] = cart
    return redirect(url_for('cart'))


@app.route('/cart/clear', methods=['POST'])
@login_required
def cart_clear():
    session.pop('cart', None)
    return redirect(url_for('cart'))


@app.route('/supply', methods=['GET', 'POST'])
@login_required
def supply():
    if current_user.role in ['admin', 'manager', 'warehouse']:
        form = Supply()   # ✅ ВОТ ТУТ

        if form.validate_on_submit():
            with session_scope() as db_sess:
                product = db_sess.query(Products).filter(
                    Products.name == form.name.data
                ).first()

                if product:
                    print(product)
                    return render_template('supply.html', form=form)

        return render_template('supply.html', form=form)

    return abort(403)

@app.route('/add_product', methods=['GET' ,'POST'])
@login_required
def add_product():
    if current_user.role in ['admin', 'manager']:
        form = NewProductsForm()
        if form.validate_on_submit():
            with session_scope() as db_sess:
                if db_sess.query(Products).filter(Products.name == form.name.data).first():
                    return render_template('add_product.html', form=form,)
                product = Products(
                    name=form.name.data,
                    price=form.price.data,
                    quantity=form.quantity.data
                )
                db_sess.add(product)
                db_sess.commit()
                return redirect(url_for('add_product'))
        return render_template('add_product.html', form=form)
    else:
        abort(403)

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    if request.method == 'POST':
        session.pop('cart', None)
        flash('Заказ оформлен! (заглушка)')
        return redirect(url_for('index'))
    cart_data = get_cart()
    total = 0
    for pid, qty in cart_data.items():
        p = next((x for x in PRODUCTS if x['id'] == int(pid)), None)
        if p:
            total += p['price'] * qty
    return render_template('checkout.html', total=total, cart_count=cart_count())


@login_manager.user_loader
def load_user(user_id):
    with session_scope() as db_sess:
        return db_sess.get(User,user_id)



@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        with session_scope() as db_sess:
            user = db_sess.query(User).filter(User.email == form.email.data).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember_me.data)
                return redirect("/")
            return render_template('login.html',
                                   message="Неправильный логин или пароль",
                                   form=form)
    return render_template('login.html', form=form,cart_count=cart_count())

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        with session_scope() as db_sess:
            if db_sess.query(User).filter(User.email == form.email.data).first():
                return render_template('register.html', title='Регистрация',
                                       form=form,
                                       message="Такой пользователь уже есть")
            user = User(
                name=form.name.data,
                email=form.email.data,
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
    return render_template(
        'account.html',
        user=current_user,
        cart_count=cart_count()
    )

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404




if __name__ == '__main__':
    serve(app, host = '127.0.0.1', port = 8000)