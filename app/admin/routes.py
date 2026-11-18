from datetime import datetime,timezone,timedelta
from flask import Blueprint,render_template,redirect,url_for,flash,request,current_app
from flask_login import login_required,current_user
from sqlalchemy.orm import joinedload
from app.extensions import db
from app.models import User,Item,Claim,Category,Location,Organization,AuditLog,Match,MatchLog,Flag,Ticket,TicketMessage,now
from app.claims.forms import ReviewForm
from app.admin.forms import MasterDataForm, OrganizationForm, LocationForm
from app.support.forms import ReplyForm, AdminContactForm
from app.utils.decorators import admin_required
from app.utils.security import reveal_text
from app.utils.ai_helpers import verification_confidence
from app.notifications.services import notify
from app.utils.audit import audit
from app.utils.textsim import ENGINE
bp=Blueprint('admin',__name__,url_prefix='/admin')

def _threshold(): return current_app.config['MATCH_THRESHOLD']

def _best_scores():
    """Highest AI score ever computed for each report (matched or not) - used to justify outcomes."""
    best={}
    for col in (MatchLog.lost_item_id,MatchLog.found_item_id):
        for iid,sc in db.session.query(col,db.func.max(MatchLog.score)).group_by(col).all():
            if sc is not None and sc>best.get(iid,-1): best[iid]=sc
    return best

@bp.get('')
@login_required
@admin_required
def dashboard():
    avg_score=db.session.query(db.func.avg(MatchLog.score)).scalar() or 0
    stats={'users':User.query.filter_by(role='USER').count(),'lost reports':Item.query.filter_by(item_type='LOST').count(),'found reports':Item.query.filter_by(item_type='FOUND').count(),
           'open reports':Item.query.filter(Item.status.in_(['ACTIVE','MATCHED','CLAIM_PENDING'])).count(),'ai matches':Match.query.count(),'pairs rejected':MatchLog.query.filter_by(passed=False).count(),
           'pending claims':Claim.query.filter_by(status='PENDING').count(),'returned':Item.query.filter_by(status='RETURNED').count(),'open tickets':Ticket.query.filter_by(status='OPEN').count(),
           'open flags':Flag.query.filter_by(status='OPEN').count(),'avg ai score':f"{round(avg_score*100)}%",'threshold':f"{round(_threshold()*100)}%"}
    return render_template('admin/dashboard.html',stats=stats,
        pending=Claim.query.filter_by(status='PENDING').order_by(Claim.created_at.desc()).limit(6).all(),
        tickets=Ticket.query.filter_by(status='OPEN').order_by(Ticket.updated_at.desc()).limit(5).all(),
        recent_items=Item.query.order_by(Item.created_at.desc()).limit(6).all(),best=_best_scores(),threshold=_threshold())

@bp.get('/users')
@login_required
@admin_required
def users(): return render_template('admin/users.html',users=User.query.order_by(User.created_at.desc()).all())

@bp.get('/items')
@login_required
@admin_required
def items():
    q=Item.query.options(joinedload(Item.user),joinedload(Item.category),joinedload(Item.location)); t=request.args.get('type',''); st=request.args.get('status',''); term=request.args.get('q','').strip()
    if t in ['LOST','FOUND']: q=q.filter_by(item_type=t)
    if st: q=q.filter_by(status=st)
    if term: q=q.filter(db.or_(Item.title.ilike(f'%{term}%'),Item.description.ilike(f'%{term}%')))
    return render_template('admin/items.html',items=q.order_by(Item.created_at.desc()).all(),best=_best_scores(),threshold=_threshold(),f_type=t,f_status=st,f_q=term)

@bp.get('/items/<int:item_id>')
@login_required
@admin_required
def item_detail(item_id):
    it=Item.query.get_or_404(item_id)
    private=reveal_text(it.private_detail.protected_details) if it.private_detail else ''
    logs=MatchLog.query.filter(db.or_(MatchLog.lost_item_id==it.id,MatchLog.found_item_id==it.id)).order_by(MatchLog.score.desc()).all()
    return render_template('admin/item_detail.html',item=it,private=private,logs=logs,threshold=_threshold(),
        claims=Claim.query.filter_by(item_id=it.id).order_by(Claim.created_at.desc()).all(),tickets=Ticket.query.filter_by(item_id=it.id).order_by(Ticket.updated_at.desc()).all())

@bp.get('/match-log')
@login_required
@admin_required
def match_log():
    view=request.args.get('view','all'); q=MatchLog.query.options(joinedload(MatchLog.lost_item).joinedload(Item.user),joinedload(MatchLog.lost_item).joinedload(Item.category),joinedload(MatchLog.found_item).joinedload(Item.user),joinedload(MatchLog.found_item).joinedload(Item.category))
    if view=='rejected': q=q.filter_by(passed=False)
    elif view=='matched': q=q.filter_by(passed=True)
    counts={'all':MatchLog.query.count(),'matched':MatchLog.query.filter_by(passed=True).count(),'rejected':MatchLog.query.filter_by(passed=False).count()}
    return render_template('admin/match_log.html',rows=q.order_by(MatchLog.score.desc()).limit(300).all(),view=view,counts=counts,threshold=_threshold(),engine=ENGINE)

@bp.get('/claims')
@login_required
@admin_required
def claims(): return render_template('admin/claims.html',claims=Claim.query.options(joinedload(Claim.claimant),joinedload(Claim.item).joinedload(Item.category),joinedload(Claim.item).joinedload(Item.user)).order_by(Claim.created_at.desc()).all(),best=_best_scores(),threshold=_threshold())

@bp.route('/claims/<int:claim_id>/review',methods=['GET','POST'])
@login_required
@admin_required
def review_claim(claim_id):
    c=Claim.query.get_or_404(claim_id); form=ReviewForm(); private=reveal_text(c.item.private_detail.protected_details) if c.item.private_detail else '' ; response=reveal_text(c.verification_response_protected); confidence=verification_confidence(response,private)
    logs=MatchLog.query.filter(db.or_(MatchLog.lost_item_id==c.item_id,MatchLog.found_item_id==c.item_id)).order_by(MatchLog.score.desc()).all()
    if form.validate_on_submit():
        decision=request.form.get('decision')
        if decision not in ['approve','reject']: flash('Invalid decision.','danger')
        else:
            c.status='APPROVED' if decision=='approve' else 'REJECTED'; c.reviewed_by=current_user.id; c.reviewed_at=datetime.now(timezone.utc); c.review_reason=form.reason.data; c.item.status='CLAIM_APPROVED' if decision=='approve' else 'ACTIVE'; notify(c.claimant_id,'CLAIM_DECISION',f'Claim {c.status.lower()}',f'Your claim was {c.status.lower()}.',c.item_id,c.id); notify(c.item.user_id,'CLAIM_DECISION',f'Claim {c.status.lower()}',f'An admin {c.status.lower()} the claim.',c.item_id,c.id); audit(f'CLAIM_{c.status}','Claim',c.id); db.session.commit(); flash(f'Claim {c.status.lower()}.','success'); return redirect(url_for('admin.claims'))
    return render_template('admin/review_claim.html',claim=c,form=form,private=private,response=response,confidence=confidence,logs=logs,threshold=_threshold())

@bp.get('/tickets')
@login_required
@admin_required
def tickets():
    st=request.args.get('status',''); q=Ticket.query
    if st in ['OPEN','ANSWERED','CLOSED']: q=q.filter_by(status=st)
    return render_template('admin/tickets.html',tickets=q.order_by(Ticket.updated_at.desc()).all(),status=st)

@bp.route('/tickets/<int:ticket_id>',methods=['GET','POST'])
@login_required
@admin_required
def ticket(ticket_id):
    t=Ticket.query.get_or_404(ticket_id); form=ReplyForm()
    if form.validate_on_submit() and t.status!='CLOSED':
        db.session.add(TicketMessage(ticket_id=t.id,sender_id=current_user.id,from_admin=True,body=form.body.data.strip())); t.status='ANSWERED'
        notify(t.user_id,'SUPPORT','The admin replied',f'Ticket #{t.id}: {t.subject}',t.item_id,link=url_for('support.thread',ticket_id=t.id)); audit('TICKET_REPLIED','Ticket',t.id); db.session.commit()
        return redirect(url_for('admin.ticket',ticket_id=t.id))
    logs=[]
    if t.item_id: logs=MatchLog.query.filter(db.or_(MatchLog.lost_item_id==t.item_id,MatchLog.found_item_id==t.item_id)).order_by(MatchLog.score.desc()).all()
    return render_template('admin/ticket.html',ticket=t,form=form,logs=logs,threshold=_threshold())

@bp.post('/tickets/<int:ticket_id>/close')
@login_required
@admin_required
def ticket_close(ticket_id):
    t=Ticket.query.get_or_404(ticket_id); t.status='CLOSED'; audit('TICKET_CLOSED','Ticket',t.id); db.session.commit(); flash('Ticket closed.','success'); return redirect(url_for('admin.tickets'))

@bp.route('/users/<int:user_id>/contact',methods=['GET','POST'])
@login_required
@admin_required
def contact_user(user_id):
    u=User.query.get_or_404(user_id); form=AdminContactForm(); item_id=request.args.get('item',type=int)
    if form.validate_on_submit():
        t=Ticket(user_id=u.id,item_id=item_id,kind='ADMIN_CONTACT',subject=form.subject.data.strip(),status='ANSWERED'); db.session.add(t); db.session.flush()
        db.session.add(TicketMessage(ticket_id=t.id,sender_id=current_user.id,from_admin=True,body=form.body.data.strip()))
        notify(u.id,'SUPPORT','The admin sent you a message',t.subject,item_id,link=url_for('support.thread',ticket_id=t.id)); audit('ADMIN_CONTACTED_USER','Ticket',t.id); db.session.commit(); flash('Message sent to the user.','success'); return redirect(url_for('admin.ticket',ticket_id=t.id))
    return render_template('admin/contact_user.html',form=form,user=u,item_id=item_id)

@bp.get('/audit-logs')
@login_required
@admin_required
def audit_logs(): return render_template('admin/audit.html',logs=AuditLog.query.order_by(AuditLog.created_at.desc()).limit(200).all())

@bp.route('/categories',methods=['GET','POST'])
@login_required
@admin_required
def categories():
    form=MasterDataForm()
    if form.validate_on_submit():
        if Category.query.filter(db.func.lower(Category.name)==form.name.data.lower()).first(): flash('Category already exists.','warning')
        else:
            c=Category(name=form.name.data.strip(),description=form.description.data.strip() or None); db.session.add(c); audit('CATEGORY_CREATED','Category',None,{'name':c.name}); db.session.commit(); flash('Category created.','success')
        return redirect(url_for('admin.categories'))
    return render_template('admin/master_data.html',title='Categories',form=form,rows=Category.query.order_by(Category.name).all(),kind='category')

@bp.post('/categories/<int:row_id>/toggle')
@login_required
@admin_required
def category_toggle(row_id):
    row=Category.query.get_or_404(row_id); row.is_active=not row.is_active; audit('CATEGORY_TOGGLED','Category',row.id); db.session.commit(); return redirect(url_for('admin.categories'))

@bp.route('/organizations',methods=['GET','POST'])
@login_required
@admin_required
def organizations():
    form=OrganizationForm()
    if form.validate_on_submit():
        if Organization.query.filter(db.func.lower(Organization.name)==form.name.data.lower()).first(): flash('Organization already exists.','warning')
        else:
            row=Organization(name=form.name.data.strip(),type=form.type.data.strip() or 'Organization',description=form.description.data.strip() or None); db.session.add(row); audit('ORGANIZATION_CREATED','Organization',None,{'name':row.name}); db.session.commit(); flash('Organization created.','success')
        return redirect(url_for('admin.organizations'))
    return render_template('admin/master_data.html',title='Organizations',form=form,rows=Organization.query.order_by(Organization.name).all(),kind='organization')

@bp.post('/organizations/<int:row_id>/toggle')
@login_required
@admin_required
def organization_toggle(row_id):
    row=Organization.query.get_or_404(row_id); row.is_active=not row.is_active; audit('ORGANIZATION_TOGGLED','Organization',row.id); db.session.commit(); return redirect(url_for('admin.organizations'))

@bp.route('/locations',methods=['GET','POST'])
@login_required
@admin_required
def locations():
    form=LocationForm(); form.organization_id.choices=[(0,'None')]+[(o.id,o.name) for o in Organization.query.order_by(Organization.name)]
    if form.validate_on_submit():
        row=Location(name=form.name.data.strip(),description=form.description.data.strip() or None,organization_id=form.organization_id.data or None,latitude=form.latitude.data,longitude=form.longitude.data); db.session.add(row); db.session.commit(); flash('Location created.','success'); return redirect(url_for('admin.locations'))
    return render_template('admin/master_data.html',title='Locations',form=form,rows=Location.query.order_by(Location.name).all(),kind='location')

@bp.post('/locations/<int:row_id>/toggle')
@login_required
@admin_required
def location_toggle(row_id):
    row=Location.query.get_or_404(row_id); row.is_active=not row.is_active; audit('LOCATION_TOGGLED','Location',row.id); db.session.commit(); return redirect(url_for('admin.locations'))

@bp.get('/flags')
@login_required
@admin_required
def flags(): return render_template('admin/flags.html',flags=Flag.query.order_by(Flag.created_at.desc()).all())

@bp.post('/flags/<int:flag_id>/resolve')
@login_required
@admin_required
def resolve_flag(flag_id):
    f=Flag.query.get_or_404(flag_id); f.status='RESOLVED'; f.reviewed_by=current_user.id
    if f.item.status=='FLAGGED': f.item.status='ACTIVE'
    audit('FLAG_RESOLVED','Flag',f.id); db.session.commit(); flash('Flag resolved.','success'); return redirect(url_for('admin.flags'))
