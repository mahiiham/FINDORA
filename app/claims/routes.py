from datetime import datetime,timezone
from flask import Blueprint,render_template,redirect,url_for,flash,abort
from flask_login import login_required,current_user
from app.extensions import db
from app.models import Item,Claim
from app.claims.forms import ClaimForm
from app.utils.security import protect_text
from app.notifications.services import notify
from app.utils.audit import audit
bp=Blueprint('claims',__name__,url_prefix='/claims')
@bp.route('/item/<int:item_id>',methods=['GET','POST'])
@login_required
def create(item_id):
    item=Item.query.get_or_404(item_id)
    if item.user_id==current_user.id: flash('You cannot claim your own report.','warning'); return redirect(url_for('items.detail',item_id=item.id))
    form=ClaimForm()
    if form.validate_on_submit():
        if Claim.query.filter_by(item_id=item.id,claimant_id=current_user.id,status='PENDING').first():
            flash('You already have an active claim for this item.','warning'); return redirect(url_for('claims.list_claims'))
        c=Claim(item_id=item.id,claimant_id=current_user.id,verification_response_protected=protect_text(form.verification_response.data),status='PENDING'); db.session.add(c); item.status='CLAIM_PENDING'; db.session.flush(); notify(item.user_id,'CLAIM','New claim submitted','A user submitted a claim. Admin verification is required.',item.id,c.id); audit('CLAIM_CREATED','Claim',c.id); db.session.commit(); flash('Claim submitted securely.','success'); return redirect(url_for('claims.list_claims'))
    return render_template('claims/create.html',form=form,item=item)
@bp.get('')
@login_required
def list_claims(): return render_template('claims/list.html',claims=Claim.query.filter_by(claimant_id=current_user.id).order_by(Claim.created_at.desc()).all())
@bp.get('/<int:claim_id>')
@login_required
def detail(claim_id):
    c=Claim.query.get_or_404(claim_id)
    if c.claimant_id!=current_user.id and c.item.user_id!=current_user.id and current_user.role!='ADMIN': abort(403)
    return render_template('claims/detail.html',claim=c)
@bp.post('/<int:claim_id>/returned')
@login_required
def returned(claim_id):
    c=Claim.query.get_or_404(claim_id)
    if c.status!='APPROVED' or (current_user.id not in [c.claimant_id,c.item.user_id] and current_user.role!='ADMIN'): abort(403)
    c.item.status='RETURNED'; notify(c.claimant_id,'RETURNED','Item returned','The item recovery workflow is complete.',c.item_id,c.id); audit('ITEM_RETURNED','Item',c.item_id); db.session.commit(); flash('Item marked returned.','success'); return redirect(url_for('claims.detail',claim_id=c.id))
