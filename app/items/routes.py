from flask import Blueprint,render_template,redirect,url_for,flash,request,send_from_directory,abort,current_app,jsonify
from flask_login import login_required,current_user
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from datetime import timedelta
from app.extensions import db
from app.models import Item,Category,Location,PrivateVerificationDetail,Flag,LocationPing,now
from app.items.forms import ItemForm
from app.items.extra_forms import FlagForm
from app.utils.security import protect_text
from app.utils.file_upload import save_image
from app.utils.audit import audit
from app.utils.geo import haversine_km
from app.utils.risk import risk_rows, suggestions, RECENT_HOURS
from app.utils.ai_helpers import text_similarity_ratio
from app.matching.service import refresh_matches_for_item
bp=Blueprint('items',__name__,url_prefix='/items')
def _choices(form):
 form.category_id.choices=[(x.id,x.name) for x in Category.query.filter_by(is_active=True).order_by(Category.name)]; form.location_id.choices=[(x.id,x.name) for x in Location.query.filter_by(is_active=True).order_by(Location.name)]

DUPLICATE_SIMILARITY_THRESHOLD=0.72

def _warn_if_duplicate(kind,title,description):
    """Non-blocking nudge: if this looks a lot like a report the same person
    already filed in the last 2 weeks, tell them so they don't accidentally
    create two open reports for the same item. Never stops submission."""
    since=now()-timedelta(days=14)
    candidates=Item.query.filter_by(user_id=current_user.id,item_type=kind).filter(Item.status.in_(['ACTIVE','MATCHED'])).filter(Item.created_at>=since).all()
    new_text=f"{title} {description}"
    for cand in candidates:
        if text_similarity_ratio(new_text,f"{cand.title} {cand.description}")>=DUPLICATE_SIMILARITY_THRESHOLD:
            flash(f'Heads up: this looks similar to a {kind.lower()} report you already filed — "{cand.title}". Both will stay active; delete the old one if this was a duplicate.','warning')
            break

TRAIL_HOURS=6

@bp.get('/api/map-data')
@login_required
def map_data():
    """Powers the 'smart location' panel on the report form: aggregated, anonymous risk per campus
    location (never any user data), written high-risk suggestions, and - if the browser shared a
    position - the nearest known location with its risk tip."""
    lat=request.args.get('lat',type=float); lng=request.args.get('lng',type=float)
    rows=risk_rows(RECENT_HOURS); nearest=None; nearest_dist=None
    if lat is not None and lng is not None:
        for r in rows:
            d=haversine_km(lat,lng,r['lat'],r['lng']); r['distance_km']=round(d,3)
            if nearest_dist is None or d<nearest_dist: nearest_dist=d; nearest=r
    return jsonify(locations=rows,nearest_location_id=nearest['id'] if nearest else None,
                   nearest_distance_km=round(nearest_dist,3) if nearest_dist is not None else None,
                   nearest=({k:nearest[k] for k in ('id','name','risk','tip','lost_count','peak_window')} if nearest else None),
                   suggestions=suggestions(rows),window_hours=RECENT_HOURS)

def _purge_pings():
    LocationPing.query.filter(LocationPing.created_at<now()-timedelta(hours=TRAIL_HOURS)).delete(synchronize_session=False)

@bp.post('/api/ping')
@login_required
def ping():
    """Opt-in location trail: remember where the signed-in user was during the last 6 hours so they can
    recall where an item went missing. Only that user can read it; old points are deleted automatically."""
    data=request.get_json(silent=True) or {}
    try: lat=float(data.get('lat')); lng=float(data.get('lng'))
    except (TypeError,ValueError): return jsonify(ok=False,error='Invalid coordinates'),400
    if not (-90<=lat<=90 and -180<=lng<=180): return jsonify(ok=False,error='Invalid coordinates'),400
    acc=data.get('accuracy'); acc=float(acc) if isinstance(acc,(int,float)) else None
    _purge_pings()
    last=LocationPing.query.filter(LocationPing.user_id==current_user.id,LocationPing.created_at>=now()-timedelta(minutes=2)).order_by(LocationPing.created_at.desc()).first()
    if last is not None and haversine_km(lat,lng,last.lat,last.lng)<0.025:
        db.session.commit(); return jsonify(ok=True,stored=False)
    best=None; best_d=None
    for l in Location.query.filter_by(is_active=True).all():
        if l.latitude is None or l.longitude is None: continue
        d=haversine_km(lat,lng,l.latitude,l.longitude)
        if best_d is None or d<best_d: best=l; best_d=d
    place=best if (best is not None and best_d<=0.5) else None
    db.session.add(LocationPing(user_id=current_user.id,lat=lat,lng=lng,accuracy_m=acc,location_id=place.id if place else None)); db.session.commit()
    return jsonify(ok=True,stored=True,place=place.name if place else None)

@bp.get('/api/trail')
@login_required
def trail():
    _purge_pings(); db.session.commit()
    risk={r['id']:r['risk'] for r in risk_rows(RECENT_HOURS)}
    stops=[]
    for p in LocationPing.query.filter_by(user_id=current_user.id).order_by(LocationPing.created_at.asc()).all():
        iso=p.created_at.isoformat()+'Z' if p.created_at.tzinfo is None else p.created_at.isoformat()
        if stops and stops[-1]['location_id']==p.location_id:
            stops[-1]['to']=iso; stops[-1]['n']+=1
        else:
            stops.append({'location_id':p.location_id,'place':p.location.name if p.location else 'Off campus / unknown','from':iso,'to':iso,'lat':p.lat,'lng':p.lng,'n':1,'risk':risk.get(p.location_id)})
    stops.reverse()
    return jsonify(stops=stops,hours=TRAIL_HOURS)

@bp.post('/api/trail/clear')
@login_required
def trail_clear():
    LocationPing.query.filter_by(user_id=current_user.id).delete(synchronize_session=False); db.session.commit()
    return jsonify(ok=True)

@bp.get('')
def list_items():
    q=Item.query.options(joinedload(Item.category),joinedload(Item.location))   # one query instead of two per card
    s=request.args.get('q','').strip(); t=request.args.get('type',''); cat=request.args.get('category',''); loc=request.args.get('location',''); color=request.args.get('color','').strip(); brand=request.args.get('brand','').strip(); status=request.args.get('status','')
    if s: q=q.filter(or_(Item.title.ilike(f'%{s}%'),Item.description.ilike(f'%{s}%')))
    if t in ['LOST','FOUND']: q=q.filter_by(item_type=t)
    if cat.isdigit(): q=q.filter_by(category_id=int(cat))
    if loc.isdigit(): q=q.filter_by(location_id=int(loc))
    if color: q=q.filter(Item.color.ilike(f'%{color}%'))
    if brand: q=q.filter(Item.brand.ilike(f'%{brand}%'))
    if status: q=q.filter_by(status=status)
    page=q.order_by(Item.created_at.desc()).paginate(page=request.args.get('page',1,type=int),per_page=current_app.config['ITEMS_PER_PAGE'],error_out=False)
    lost_by_cat=dict(db.session.query(Item.category_id,db.func.count(Item.id)).filter_by(item_type='LOST').group_by(Item.category_id).all())
    found_by_cat=dict(db.session.query(Item.category_id,db.func.count(Item.id)).filter_by(item_type='FOUND').group_by(Item.category_id).all())
    categories=Category.query.filter_by(is_active=True).order_by(Category.name).all()
    category_stats=[{'cat':c,'lost':lost_by_cat.get(c.id,0),'found':found_by_cat.get(c.id,0)} for c in categories]
    category_stats.sort(key=lambda x:x['lost']+x['found'],reverse=True)
    return render_template('items/list.html',page=page,categories=categories,locations=Location.query.filter_by(is_active=True).all(),category_stats=category_stats)
@bp.route('/create/<kind>',methods=['GET','POST'])
@login_required
def create(kind):
    kind=kind.upper()
    if kind not in ['LOST','FOUND']: abort(404)
    form=ItemForm(); _choices(form)
    if form.validate_on_submit():
        try: image,phash=save_image(form.image.data)
        except ValueError as e: flash(str(e),'danger'); return render_template('items/form.html',form=form,kind=kind)
        _warn_if_duplicate(kind,form.title.data.strip(),form.description.data.strip())
        dlat=request.form.get('detected_lat',type=float); dlng=request.form.get('detected_lng',type=float)
        if dlat is None or dlng is None or not (-90<=dlat<=90 and -180<=dlng<=180): dlat=dlng=None
        
        it = Item(
            user_id=current_user.id,
            organization_id=current_user.organization_id,
            category_id=form.category_id.data,
            location_id=form.location_id.data,
            item_type=kind,
            title=form.title.data.strip(),
            description=form.description.data.strip(),
            color=(form.color.data or '').strip() or None,
            brand=(form.brand.data or '').strip() or None,
            model=(form.model.data or '').strip() or None,
            date_event=form.date_event.data,
            time_event=form.time_event.data,
            image_path=image,
            image_phash=phash,
            reported_lat=dlat,
            reported_lng=dlng,
            distinguishing_features=(form.distinguishing_features.data or '').strip() or None,
            value_level=form.value_level.data,
            storage_location=(form.storage_location.data or '').strip() or None
        )

        db.session.add(it); db.session.flush(); db.session.add(PrivateVerificationDetail(item_id=it.id,protected_details=protect_text(form.private_details.data.strip()))); audit('REPORT_CREATED','Item',it.id,{'type':kind}); db.session.commit(); refresh_matches_for_item(it,current_app.config['MATCH_THRESHOLD']); flash('Report created and matching completed.','success'); return redirect(url_for('items.detail',item_id=it.id))
    return render_template('items/form.html',form=form,kind=kind)
@bp.get('/<int:item_id>')
def detail(item_id): return render_template('items/detail.html',item=Item.query.get_or_404(item_id))
@bp.get('/uploads/<path:name>')
def upload(name): return send_from_directory(current_app.config['UPLOAD_FOLDER'],name)
@bp.post('/<int:item_id>/delete')
@login_required
def delete(item_id):
    it=Item.query.get_or_404(item_id)
    if current_user.id!=it.user_id and current_user.role!='ADMIN': abort(403)
    db.session.delete(it); audit('REPORT_DELETED','Item',item_id); db.session.commit(); flash('Report deleted.','success'); return redirect(url_for('main.dashboard'))

@bp.route('/<int:item_id>/edit',methods=['GET','POST'])
@login_required
def edit(item_id):
    it=Item.query.get_or_404(item_id)
    if current_user.id!=it.user_id and current_user.role!='ADMIN': abort(403)
    form=ItemForm(obj=it); _choices(form)
    if form.validate_on_submit():
        it.category_id=form.category_id.data; it.location_id=form.location_id.data; it.title=form.title.data.strip(); it.description=form.description.data.strip(); it.color=form.color.data.strip() or None; it.brand=form.brand.data.strip() or None; it.model=form.model.data.strip() or None; it.date_event=form.date_event.data; it.time_event=form.time_event.data; it.distinguishing_features=form.distinguishing_features.data.strip() or None; it.value_level=form.value_level.data; it.storage_location=form.storage_location.data.strip() or None
        if form.image.data and getattr(form.image.data,'filename',''):
            try: it.image_path,it.image_phash=save_image(form.image.data)
            except ValueError as e: flash(str(e),'danger'); return render_template('items/form.html',form=form,kind=it.item_type,item=it)
        if it.private_detail: it.private_detail.protected_details=protect_text(form.private_details.data.strip())
        else: db.session.add(PrivateVerificationDetail(item_id=it.id,protected_details=protect_text(form.private_details.data.strip())))
        audit('REPORT_EDITED','Item',it.id); db.session.commit(); refresh_matches_for_item(it,current_app.config['MATCH_THRESHOLD']); flash('Report updated.','success'); return redirect(url_for('items.detail',item_id=it.id))
    if request.method=='GET':
        form.private_details.data=''
    return render_template('items/form.html',form=form,kind=it.item_type,item=it)

@bp.route('/<int:item_id>/flag',methods=['GET','POST'])
@login_required
def flag(item_id):
    it=Item.query.get_or_404(item_id); form=FlagForm()
    if form.validate_on_submit():
        existing=Flag.query.filter_by(item_id=it.id,reporter_id=current_user.id,status='OPEN').first()
        if existing: flash('You already flagged this report.','warning')
        else:
            db.session.add(Flag(item_id=it.id,reporter_id=current_user.id,reason=form.reason.data.strip())); it.status='FLAGGED'; audit('REPORT_FLAGGED','Item',it.id); db.session.commit(); flash('Report flagged for admin review.','success')
        return redirect(url_for('items.detail',item_id=it.id))
    return render_template('items/flag.html',form=form,item=it)
