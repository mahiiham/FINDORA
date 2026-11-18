from flask import Blueprint, render_template, redirect, url_for, flash, abort, jsonify, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Claim, Message, Match, MatchMessage
from app.messaging.forms import MessageForm
from app.utils.ai_helpers import redact_personal_info
from app.utils.audit import audit
from app.notifications.services import notify

bp = Blueprint('messaging', __name__, url_prefix='/messages')


def _guard(claim):
    """Only the claimant, the report owner, or an admin may access this thread.
    Nobody else — including other logged-in users — can view or send messages."""
    if current_user.role == 'ADMIN':
        return
    if current_user.id not in (claim.claimant_id, claim.item.user_id):
        abort(403)


def _alias(claim, user_id):
    """Findora never reveals real names/emails/phone numbers in chat. Each side only
    ever sees a role label, keeping communication seamless but anonymous until the
    platform's own verified return process is complete."""
    if user_id == claim.claimant_id:
        return 'Claimant'
    if user_id == claim.item.user_id:
        return 'Reporter'
    return 'Admin'


@bp.route('/claim/<int:claim_id>', methods=['GET', 'POST'])
@login_required
def thread(claim_id):
    claim = Claim.query.get_or_404(claim_id)
    _guard(claim)
    if claim.status not in ('PENDING', 'APPROVED'):
        flash('Chat is only available while a claim is pending review or approved.', 'warning')
        return redirect(url_for('claims.detail', claim_id=claim.id))
    form = MessageForm()
    if form.validate_on_submit():
        clean, was_redacted = redact_personal_info(form.body.data.strip())
        msg = Message(claim_id=claim.id, sender_id=current_user.id, body=clean, was_redacted=was_redacted)
        db.session.add(msg)
        other_id = claim.item.user_id if current_user.id == claim.claimant_id else claim.claimant_id
        notify(other_id, 'MESSAGE', 'New message', 'You have a new anonymized message about a claim.', claim.item_id, claim.id, link=url_for('messaging.thread', claim_id=claim.id))
        audit('MESSAGE_SENT', 'Claim', claim.id, {'redacted': was_redacted})
        db.session.commit()
        if was_redacted:
            flash('Your message was sent, but personal contact details were automatically hidden for your safety.', 'warning')
        return redirect(url_for('messaging.thread', claim_id=claim.id))
    messages = Message.query.filter_by(claim_id=claim.id).order_by(Message.created_at.asc()).all()
    return render_template('messaging/thread.html', claim=claim, form=form, messages=messages,
                            alias=lambda uid: _alias(claim, uid))


@bp.get('/claim/<int:claim_id>/poll')
@login_required
def poll(claim_id):
    claim = Claim.query.get_or_404(claim_id)
    _guard(claim)
    after = request.args.get('after', 0, type=int)
    rows = Message.query.filter(Message.claim_id == claim.id, Message.id > after).order_by(Message.created_at.asc()).all()
    return jsonify([{
        'id': m.id,
        'alias': _alias(claim, m.sender_id),
        'mine': m.sender_id == current_user.id,
        'body': m.body,
        'was_redacted': m.was_redacted,
        'created_at': m.created_at.strftime('%H:%M')
    } for m in rows])



# ---------------------------------------------------------------------------
# User <-> user chat that starts as soon as the AI proposes a match (no claim needed)
# ---------------------------------------------------------------------------
def _match_guard(m):
    """Only the owner of the LOST report, the finder of the matching FOUND report, or an admin."""
    if current_user.role == 'ADMIN':
        return
    if current_user.id not in (m.lost_item.user_id, m.found_item.user_id):
        abort(403)


def _match_alias(m, user_id):
    if user_id == m.lost_item.user_id:
        return 'Owner (lost item)'
    if user_id == m.found_item.user_id:
        return 'Finder'
    return 'Admin'


@bp.route('/match/<int:match_id>', methods=['GET', 'POST'])
@login_required
def match_thread(match_id):
    m = Match.query.get_or_404(match_id)
    _match_guard(m)
    form = MessageForm()
    if form.validate_on_submit():
        clean, was_redacted = redact_personal_info(form.body.data.strip())
        db.session.add(MatchMessage(match_id=m.id, sender_id=current_user.id, body=clean, was_redacted=was_redacted))
        for uid, item in ((m.lost_item.user_id, m.lost_item), (m.found_item.user_id, m.found_item)):
            if uid != current_user.id:
                notify(uid, 'MESSAGE', 'New message about a possible match', 'Someone replied in an anonymized chat about your report.', item.id, None, link=url_for('messaging.match_thread', match_id=m.id))
        audit('MATCH_MESSAGE_SENT', 'Match', m.id, {'redacted': was_redacted})
        db.session.commit()
        if was_redacted:
            flash('Your message was sent, but personal contact details were automatically hidden for your safety.', 'warning')
        return redirect(url_for('messaging.match_thread', match_id=m.id))
    messages = MatchMessage.query.filter_by(match_id=m.id).order_by(MatchMessage.created_at.asc()).all()
    return render_template('messaging/match_thread.html', match=m, form=form, messages=messages, alias=lambda uid: _match_alias(m, uid))


@bp.get('/match/<int:match_id>/poll')
@login_required
def match_poll(match_id):
    m = Match.query.get_or_404(match_id)
    _match_guard(m)
    after = request.args.get('after', 0, type=int)
    rows = MatchMessage.query.filter(MatchMessage.match_id == m.id, MatchMessage.id > after).order_by(MatchMessage.created_at.asc()).all()
    return jsonify([{'id': r.id, 'alias': _match_alias(m, r.sender_id), 'mine': r.sender_id == current_user.id, 'body': r.body,
                     'was_redacted': r.was_redacted, 'created_at': r.created_at.strftime('%H:%M')} for r in rows])
