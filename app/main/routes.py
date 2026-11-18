from flask import Blueprint,render_template,jsonify,redirect,url_for
from sqlalchemy.orm import joinedload
from flask_login import login_required,current_user
from app.extensions import db
from app.models import Item,Match,Claim,Notification,User,Ticket
bp=Blueprint('main',__name__)
from app.main.forms import ProfileForm
@bp.get('/')
def index():
    return render_template('index.html',
        recent=Item.query.filter(Item.status.in_(['ACTIVE','MATCHED'])).order_by(Item.created_at.desc()).limit(6).all(),
        returned=Item.query.filter_by(status='RETURNED').order_by(Item.updated_at.desc()).limit(4).all(),
        stats={'active':Item.query.filter(Item.status.in_(['ACTIVE','MATCHED'])).count(),'returned':Item.query.filter_by(status='RETURNED').count(),'matches':Match.query.count()})
@bp.get('/dashboard')
@login_required
def dashboard():
    """User interface home: my reports (with photos), my claims, claims on my reports, AI matches,
    past locations and unread notifications."""
    if current_user.role=='ADMIN': return redirect(url_for('admin.dashboard'))
    uid=current_user.id
    my_items=Item.query.options(joinedload(Item.category),joinedload(Item.location)).filter_by(user_id=uid).order_by(Item.created_at.desc()).all()
    my_ids=[i.id for i in my_items]
    matches=Match.query.filter(db.or_(Match.lost_item_id.in_(my_ids),Match.found_item_id.in_(my_ids))).order_by(Match.score.desc()).limit(6).all() if my_ids else []
    my_claims=Claim.query.filter_by(claimant_id=uid).order_by(Claim.created_at.desc()).all()
    received=Claim.query.join(Item,Claim.item_id==Item.id).filter(Item.user_id==uid).order_by(Claim.created_at.desc()).all()
    history=[]
    for i in my_items:
        lat,lng,exact=(i.reported_lat,i.reported_lng,True) if i.reported_lat is not None and i.reported_lng is not None else (i.location.latitude,i.location.longitude,False)
        history.append({'id':i.id,'title':i.title,'type':i.item_type,'place':i.location.name,'lat':lat,'lng':lng,'exact':exact,'when':i.created_at.strftime('%d %b %Y, %H:%M'),'event':i.date_event.strftime('%d %b %Y')})
    stats={'lost':sum(1 for i in my_items if i.item_type=='LOST'),'found':sum(1 for i in my_items if i.item_type=='FOUND'),'matches':len(matches),'claims':len(my_claims),'returned':sum(1 for i in my_items if i.status=='RETURNED')}
    notifications=Notification.query.filter_by(user_id=uid,is_read=False).order_by(Notification.created_at.desc()).limit(5).all()
    tickets=Ticket.query.filter_by(user_id=uid).order_by(Ticket.updated_at.desc()).limit(4).all()
    from app.utils.risk import risk_rows, suggestions
    risk=suggestions(risk_rows())
    return render_template('dashboard.html',risk=risk,my_items=my_items,matches=matches,my_claims=my_claims,received=received,history=history,stats=stats,notifications=notifications,tickets=tickets)

@bp.get('/how-we-protect-you')
def security():
    return render_template('security.html')

@bp.get('/health')
def health():
    try: db.session.execute(db.text('SELECT 1')); return jsonify(status='ok')
    except Exception: return jsonify(status='degraded'),503

@bp.route('/profile',methods=['GET','POST'])
@login_required
def profile():
    form=ProfileForm(obj=current_user)
    if form.validate_on_submit():
        existing=User.query.filter(db.func.lower(User.email)==form.email.data.lower(),User.id!=current_user.id).first()
        if existing:
            from flask import flash
            flash('That email is already in use.','danger')
        else:
            current_user.name=form.name.data.strip(); current_user.email=form.email.data.lower().strip(); current_user.phone=form.phone.data.strip() if form.phone.data else None; db.session.commit()
            from flask import flash
            flash('Profile updated.','success')
    return render_template('profile.html',form=form)
