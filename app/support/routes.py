from flask import Blueprint, render_template, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Item, Ticket, TicketMessage, User
from app.support.forms import TicketForm, ReplyForm
from app.notifications.services import notify
from app.utils.audit import audit

bp = Blueprint('support', __name__, url_prefix='/support')


def _own(ticket):
    if ticket.user_id != current_user.id:
        abort(403)


@bp.route('', methods=['GET', 'POST'])
@login_required
def index():
    """Direct line to the administrator: ask a question, report something directly, or ask why a
    report was not matched. Admins answer from their own console and the user is notified."""
    if current_user.role == 'ADMIN':
        return redirect(url_for('admin.tickets'))
    form = TicketForm()
    mine = Item.query.filter_by(user_id=current_user.id).order_by(Item.created_at.desc()).all()
    form.item_id.choices = [(0, 'None')] + [(i.id, f'{i.item_type.title()}: {i.title}') for i in mine]
    if form.validate_on_submit():
        item_id = form.item_id.data or None
        if item_id and item_id not in [i.id for i in mine]:
            item_id = None
        t = Ticket(user_id=current_user.id, item_id=item_id, kind=form.kind.data, subject=form.subject.data.strip(), status='OPEN')
        db.session.add(t); db.session.flush()
        db.session.add(TicketMessage(ticket_id=t.id, sender_id=current_user.id, from_admin=False, body=form.body.data.strip()))
        for admin in User.query.filter_by(role='ADMIN').all():
            notify(admin.id, 'SUPPORT', 'New message from a user', f'Ticket #{t.id}: {t.subject}', item_id, link=url_for('admin.ticket', ticket_id=t.id))
        audit('TICKET_CREATED', 'Ticket', t.id, {'kind': t.kind})
        db.session.commit()
        flash('Your message was sent to the admin.', 'success')
        return redirect(url_for('support.thread', ticket_id=t.id))
    tickets = Ticket.query.filter_by(user_id=current_user.id).order_by(Ticket.updated_at.desc()).all()
    return render_template('support/index.html', form=form, tickets=tickets)


@bp.route('/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
def thread(ticket_id):
    t = Ticket.query.get_or_404(ticket_id)
    if current_user.role == 'ADMIN':
        return redirect(url_for('admin.ticket', ticket_id=t.id))
    _own(t)
    form = ReplyForm()
    if form.validate_on_submit() and t.status != 'CLOSED':
        db.session.add(TicketMessage(ticket_id=t.id, sender_id=current_user.id, from_admin=False, body=form.body.data.strip()))
        t.status = 'OPEN'
        for admin in User.query.filter_by(role='ADMIN').all():
            notify(admin.id, 'SUPPORT', 'User replied', f'Ticket #{t.id}: {t.subject}', t.item_id, link=url_for('admin.ticket', ticket_id=t.id))
        db.session.commit()
        return redirect(url_for('support.thread', ticket_id=t.id))
    return render_template('support/thread.html', ticket=t, form=form)


@bp.post('/<int:ticket_id>/close')
@login_required
def close(ticket_id):
    t = Ticket.query.get_or_404(ticket_id)
    _own(t)
    t.status = 'CLOSED'
    audit('TICKET_CLOSED', 'Ticket', t.id)
    db.session.commit()
    flash('Conversation marked as resolved.', 'success')
    return redirect(url_for('support.index'))
