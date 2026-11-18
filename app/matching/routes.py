from flask import Blueprint,render_template,abort,current_app
from flask_login import login_required,current_user
from app.models import Item,Match
bp=Blueprint('matching',__name__)
@bp.get('/items/<int:item_id>/matches')
@login_required
def item_matches(item_id):
    item=Item.query.get_or_404(item_id)
    if item.user_id!=current_user.id and current_user.role!='ADMIN': abort(403)
    q=Match.query.filter((Match.lost_item_id==item.id)|(Match.found_item_id==item.id)).order_by(Match.score.desc()).all()
    return render_template('items/matches.html',item=item,matches=q,threshold=current_app.config['MATCH_THRESHOLD'])
