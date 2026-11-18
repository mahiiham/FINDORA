from flask import Blueprint,render_template,redirect,url_for,abort
from flask_login import login_required,current_user
from app.extensions import db
from app.models import Notification
bp=Blueprint('notifications',__name__,url_prefix='/notifications')
@bp.get('')
@login_required
def list_notifications(): return render_template('notifications.html',notifications=Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all())
@bp.post('/<int:nid>/read')
@login_required
def read(nid):
    n=Notification.query.get_or_404(nid)
    if n.user_id!=current_user.id: abort(403)
    n.is_read=True; db.session.commit(); return redirect(url_for('notifications.list_notifications'))
