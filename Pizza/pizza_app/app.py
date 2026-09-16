from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user,
)

from config import Config
from extensions import db, login_manager
from models import User, PizzaOrder
from forms import RegistrationForm, LoginForm, PizzaOrderForm


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        db.create_all()

    register_routes(app)
    return app


def register_routes(app):
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("list_orders"))
        return redirect(url_for("login"))

    # ---------- Auth ----------

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for("list_orders"))

        form = RegistrationForm()
        if form.validate_on_submit():
            user = User(username=form.username.data.strip(), email=form.email.data.strip().lower())
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash("Account created successfully. Please log in.", "success")
            return redirect(url_for("login"))

        return render_template("register.html", form=form)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("list_orders"))

        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data.strip()).first()
            if user is None or not user.check_password(form.password.data):
                flash("Invalid username or password.", "danger")
                return render_template("login.html", form=form)

            login_user(user, remember=form.remember_me.data)
            flash(f"Welcome back, {user.username}!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("list_orders"))

        return render_template("login.html", form=form)

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("You have been logged out.", "info")
        return redirect(url_for("login"))

    # ---------- Pizza Orders ----------

    @app.route("/orders")
    @login_required
    def list_orders():
        orders = (
            PizzaOrder.query.filter_by(user_id=current_user.id)
            .order_by(PizzaOrder.created_at.desc())
            .all()
        )
        return render_template("orders.html", orders=orders)

    @app.route("/orders/new", methods=["GET", "POST"])
    @login_required
    def new_order():
        form = PizzaOrderForm()
        if form.validate_on_submit():
            order = PizzaOrder(
                user_id=current_user.id,
                size=form.size.data,
                crust=form.crust.data,
                toppings=form.toppings.data.strip(),
                quantity=form.quantity.data,
                notes=form.notes.data.strip(),
            )
            db.session.add(order)
            db.session.commit()
            flash("Order submitted.", "success")
            return redirect(url_for("list_orders"))

        return render_template("order_form.html", form=form, title="New Pizza Order")

    def _get_owned_order_or_404(order_id):
        order = db.session.get(PizzaOrder, order_id)
        if order is None:
            abort(404)
        if order.user_id != current_user.id:
            abort(403)
        return order

    @app.route("/orders/<int:order_id>/edit", methods=["GET", "POST"])
    @login_required
    def edit_order(order_id):
        order = _get_owned_order_or_404(order_id)
        form = PizzaOrderForm(obj=order)

        if form.validate_on_submit():
            order.size = form.size.data
            order.crust = form.crust.data
            order.toppings = form.toppings.data.strip()
            order.quantity = form.quantity.data
            order.notes = form.notes.data.strip()
            db.session.commit()
            flash("Order updated.", "success")
            return redirect(url_for("list_orders"))

        return render_template("order_form.html", form=form, title="Edit Pizza Order")

    @app.route("/orders/<int:order_id>/delete", methods=["POST"])
    @login_required
    def delete_order(order_id):
        order = _get_owned_order_or_404(order_id)
        db.session.delete(order)
        db.session.commit()
        flash("Order deleted.", "info")
        return redirect(url_for("list_orders"))

    # ---------- Error handlers ----------

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("error.html", code=403, message="You don't have access to that."), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("error.html", code=404, message="That page doesn't exist."), 404


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
