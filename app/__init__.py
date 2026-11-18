from pathlib import Path
from flask import Flask,render_template,url_for
from app.config import Config
from app.extensions import db,login_manager,csrf,migrate,limiter

def _sqlite_self_heal(app):
    from sqlalchemy import inspect as _inspect, text
    fresh=not _inspect(db.engine).has_table('item')
    db.create_all()   # creates only the tables that are missing
    if fresh:
        app.logger.info('First run: created local SQLite tables. Run "python seed.py" to load the sample data.'); return
    insp=_inspect(db.engine)
    wanted={'item':[('image_phash','VARCHAR(32)'),('reported_lat','FLOAT'),('reported_lng','FLOAT')],'match':[('image_score','FLOAT')],'notification':[('link','VARCHAR(200)')]}
    for table,cols in wanted.items():
        have={c['name'] for c in insp.get_columns(table)}
        for col,typ in cols:
            if col not in have:
                with db.engine.begin() as conn: conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {col} {typ}'))

def create_app(config_object=Config):
    app=Flask(__name__); app.config.from_object(config_object)
    Path(app.config['UPLOAD_FOLDER']).mkdir(parents=True,exist_ok=True); Path(app.instance_path).mkdir(parents=True,exist_ok=True)
    db.init_app(app); login_manager.init_app(app); csrf.init_app(app); migrate.init_app(app,db); limiter.init_app(app)
    login_manager.login_view='auth.login'; login_manager.login_message_category='warning'
    from app.auth.routes import bp as auth; from app.main.routes import bp as main; from app.items.routes import bp as items; from app.matching.routes import bp as matching; from app.claims.routes import bp as claims; from app.admin.routes import bp as admin; from app.notifications.routes import bp as notifications; from app.messaging.routes import bp as messaging; from app.support.routes import bp as support
    for b in [auth,main,items,matching,claims,admin,notifications,messaging,support]: app.register_blueprint(b)

    with app.app_context():
        # Beginner-friendly safety net for the default local SQLite database: create any missing tables
        # and add columns introduced by newer versions, so an older findora.db (or a brand new one) never
        # crashes with "no such table / no such column". Never touches non-SQLite databases.
        if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite'):
            _sqlite_self_heal(app)

    def sticker_url(category_name):
        slug=(category_name or 'other').lower().replace(' ','-')
        if not (Path(app.static_folder)/'stickers'/f'{slug}.png').exists(): slug='other'
        return url_for('static',filename=f'stickers/{slug}.png')
    def item_thumb(item):
        if not item.image_path: return sticker_url(item.category.name if item.category else None)
        name='thumb_'+item.image_path
        if not (Path(app.config['UPLOAD_FOLDER'])/name).exists(): name=item.image_path   # older reports may have no thumbnail
        return url_for('items.upload',name=name)
    def item_photo(item):
        return url_for('items.upload',name=item.image_path) if item.image_path else sticker_url(item.category.name if item.category else None)
    app.jinja_env.globals.update(sticker_url=sticker_url,item_thumb=item_thumb,item_photo=item_photo,CAMPUS_NAME='Meerut Institute of Engineering and Technology')

    @app.context_processor
    def inject_globals():
        from flask_login import current_user
        from app.models import Notification
        from app.models import Ticket
        unread=0; open_tickets=0; my_open_tickets=0
        if getattr(current_user,'is_authenticated',False):
            unread=Notification.query.filter_by(user_id=current_user.id,is_read=False).count()
            if current_user.role=='ADMIN': open_tickets=Ticket.query.filter_by(status='OPEN').count()
            else: my_open_tickets=Ticket.query.filter_by(user_id=current_user.id,status='ANSWERED').count()
        return {'unread_notifications':unread,'open_tickets':open_tickets,'my_open_tickets':my_open_tickets}

    @app.after_request
    def headers(r):
        r.headers['X-Content-Type-Options']='nosniff'; r.headers['X-Frame-Options']='SAMEORIGIN'; r.headers['Referrer-Policy']='strict-origin-when-cross-origin'; return r
    for code in [400,401,403,404,413,429,500]:
        app.register_error_handler(code,lambda e,c=code:(render_template('errors/error.html',code=c,message=('That upload is too large. Please choose a photo under 16 MB.' if c==413 else getattr(e,'description','Something went wrong.'))),c))
    return app
