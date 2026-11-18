"""Loss-risk analysis for campus locations (aggregated, anonymous - never contains user data)."""
from collections import Counter
from datetime import timedelta
from flask import current_app
from app.extensions import db
from app.models import Item, Location, now

RECENT_HOURS = 6


def _window(hour):
    start = (hour // 2) * 2
    return f'{start:02d}:00-{(start + 2) % 24:02d}:00'


def risk_rows(hours=RECENT_HOURS):
    """One row per active location that has coordinates: lost counts, recent counts, risk level
    (high / medium / low), the busiest 2-hour window and a plain-language tip."""
    since = now() - timedelta(hours=hours)
    # NOTE: the "recent" comparison is done by the database (SQLite returns naive datetimes, so comparing in Python would fail)
    recent = Counter(dict(db.session.query(Item.location_id, db.func.count(Item.id)).filter(Item.item_type == 'LOST', Item.created_at >= since).group_by(Item.location_id).all()))
    counts, hrs = Counter(), {}
    for loc_id, t_event, created in db.session.query(Item.location_id, Item.time_event, Item.created_at).filter(Item.item_type == 'LOST').all():
        counts[loc_id] += 1
        # stored times are UTC; shift to local time (default India, UTC+5:30) when the user did not type a time
        hour = t_event.hour if t_event is not None else ((created + timedelta(minutes=current_app.config.get('UTC_OFFSET_MIN', 330))).hour if created else None)
        if hour is not None: hrs.setdefault(loc_id, Counter())[_window(hour)] += 1
    top = max(counts.values()) if counts else 0
    rows = []
    for l in Location.query.filter_by(is_active=True).order_by(Location.name).all():
        if l.latitude is None or l.longitude is None: continue
        c = counts.get(l.id, 0)
        ratio = (c / top) if top else 0
        risk = 'high' if (c >= 2 and ratio >= 0.66) else 'medium' if (c >= 1 and ratio >= 0.33) else 'low'
        peak = None
        if l.id in hrs:
            win, n = hrs[l.id].most_common(1)[0]
            if n >= 2: peak = win
        tip = {'high': f'High-risk spot: {c} lost reports here' + (f', mostly {peak}' if peak else '') + '. Keep your belongings with you.',
               'medium': f'Medium risk: {c} lost report(s) here' + (f' (busiest {peak})' if peak else '') + '. Double-check your bag before leaving.',
               'low': 'Low risk: very few items are reported lost here.'}[risk]
        rows.append({'id': l.id, 'name': l.name, 'lat': l.latitude, 'lng': l.longitude, 'lost_count': c, 'recent_count': recent.get(l.id, 0),
                     'risk': risk, 'peak_window': peak, 'tip': tip})
    return rows


def suggestions(rows, limit=3):
    """Top locations a person should be careful around (high first, then medium), most lost reports first."""
    ranked = [r for r in rows if r['risk'] in ('high', 'medium')]
    ranked.sort(key=lambda r: (r['risk'] != 'high', -r['lost_count'], -r['recent_count']))
    return ranked[:limit]
