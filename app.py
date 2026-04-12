from flask import Flask, render_template, redirect, url_for, request, session, flash

app = Flask(__name__)
app.secret_key = 'dev-secret-key'



PRODUCTS = []

CATEGORIES = ['Электроника', 'Одежда', 'Книги']

USERS = {}  # email -> {password, name}


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
def cart_add(product_id):
    cart = session.get('cart', {})
    key = str(product_id)
    cart[key] = cart.get(key, 0) + 1
    session['cart'] = cart
    flash('Товар добавлен в корзину.')
    return redirect(request.referrer or url_for('catalog'))


@app.route('/cart/remove/<int:product_id>', methods=['POST'])
def cart_remove(product_id):
    cart = session.get('cart', {})
    cart.pop(str(product_id), None)
    session['cart'] = cart
    return redirect(url_for('cart'))


@app.route('/cart/clear', methods=['POST'])
def cart_clear():
    session.pop('cart', None)
    return redirect(url_for('cart'))


@app.route('/checkout', methods=['GET', 'POST'])
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


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        user = USERS.get(email)
        if user and user['password'] == password:
            session['user'] = email
            flash('Вы вошли в систему.')
            return redirect(url_for('index'))
        flash('Неверный email или пароль.')
    return render_template('login.html', cart_count=cart_count())


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        if email in USERS:
            flash('Email уже зарегистрирован.')
        elif not name or not email or not password:
            flash('Заполните все поля.')
        else:
            role = request.form.get('role', 'customer')
            position = request.form.get('position', '')
            USERS[email] = {'password': password, 'name': name, 'role': role, 'position': position}
            session['user'] = email
            flash('Регистрация прошла успешно.')
            return redirect(url_for('index'))
    return render_template('register.html', cart_count=cart_count())


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))


@app.route('/account')
def account():
    email = session.get('user')
    if not email:
        return redirect(url_for('login'))
    user = USERS.get(email, {})
    return render_template('account.html', user=user, email=email, cart_count=cart_count())


@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(debug=True)
 