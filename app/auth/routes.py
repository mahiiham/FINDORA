from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app.extensions import db, limiter
from app.models import User, Organization
from app.auth.forms import RegisterForm, LoginForm
from app.utils.audit import audit

bp=Blueprint('auth',__name__)
@bp.route('/register',methods=['GET','POST'])
def register():
    if current_user.is_authenticated: return redirect(url_for('main.dashboard'))
    form=RegisterForm(); form.organization_id.choices=[(0,'No organization')]+[(o.id,o.name) for o in Organization.query.filter_by(is_active=True).order_by(Organization.name)]
    if form.validate_on_submit():
        if User.query.filter(db.func.lower(User.email)==form.email.data.lower()).first():
            flash('An account with that email already exists.','danger'); return render_template('auth/register.html',form=form)
        u=User(name=form.name.data.strip(),email=form.email.data.lower().strip(),phone=form.phone.data.strip() if form.phone.data else None,organization_id=form.organization_id.data or None); u.set_password(form.password.data); db.session.add(u); db.session.flush(); audit('REGISTER','User',u.id); db.session.commit(); login_user(u); flash('Welcome to Findora.','success'); return redirect(url_for('main.dashboard'))
    return render_template('auth/register.html',form=form)
@bp.route('/login',methods=['GET','POST'])
@limiter.limit('8 per minute')
def login():
    if current_user.is_authenticated: return redirect(url_for('main.dashboard'))
    form=LoginForm()
    if form.validate_on_submit():
        u=User.query.filter(db.func.lower(User.email)==form.email.data.lower()).first()
        if not u or not u.check_password(form.password.data) or not u.is_active:
            flash('Invalid email or password.','danger'); return render_template('auth/login.html',form=form)
        login_user(u,remember=form.remember.data); audit('LOGIN','User',u.id); db.session.commit(); return redirect(request.args.get('next') or url_for('main.dashboard'))
    if request.method=='POST': flash('Please enter your email and password.','warning')
    return render_template('auth/login.html',form=form)
@bp.post('/logout')
@login_required
def logout():
    audit('LOGOUT','User',current_user.id); db.session.commit(); logout_user(); return redirect(url_for('main.index'))
