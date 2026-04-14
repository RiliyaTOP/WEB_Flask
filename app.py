from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from datetime import timedelta
from data import db_session
from data.users import User
from form.users import LoginForm, RegistrationForm
from waitress import serve

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
    return sum(get_cart().values())


# Маршруты

@app.route('/')
def index():
    featured = PRODUCTS[:3]
    return render_template('index.html', featured=featured, cart_count=cart_count())


@app.route('/catalog')
def catalog():
    category = request.args.get('category')
    q = request.args.get('q', '').strip().lower()
    products = PRODUCTS
    if category:
        products = [p for p in products if p['category'] == category]
    if q:
        products = [p for p in products if q in p['name'].lower()]
    return render_template('catalog.html', products=products, categories=CATEGORIES,
                           selected_category=category, q=q, cart_count=cart_count())


@app.route('/product/<int:product_id>')
def product(product_id):
    item = next((p for p in PRODUCTS if p['id'] == product_id), None)
    if item is None:
        return render_template('404.html'), 404
    return render_template('product.html', product=item, cart_count=cart_count())


@app.route('/cart')
@login_required
def cart():
    cart_data = get_cart()
    items = []
    total = 0
    for pid, qty in cart_data.items():
        p = next((x for x in PRODUCTS if x['id'] == int(pid)), None)
        if p:
            subtotal = p['price'] * qty
            items.append({'product': p, 'qty': qty, 'subtotal': subtotal})
            total += subtotal
    return render_template('cart.html', items=items, total=total, cart_count=cart_count())


@app.route('/cart/add/<int:product_id>', methods=['POST'])
@login_required
def cart_add(product_id):
    cart = session.get('cart', {})
    key = str(product_id)
    cart[key] = cart.get(key, 0) + 1
    session['cart'] = cart
    flash('Товар добавлен в корзину.')
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
    db_sess = db_session.create_session()
    return db_sess.get(User,user_id)



@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
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
        db_sess = db_session.create_session()
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