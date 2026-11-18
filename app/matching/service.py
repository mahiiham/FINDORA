from datetime import timedelta
from difflib import SequenceMatcher
from app.extensions import db
from app.models import Item, Match, MatchLog, Notification
from app.utils.file_upload import image_similarity
from app.utils.textsim import text_cosine

WEIGHTS={'description':0.30,'category':0.15,'location':0.15,'date':0.10,'attributes':0.15,'image':0.15}

def _text(a,b):
    a=(a or '').strip(); b=(b or '').strip()
    if not a or not b: return None
    return text_cosine(a,b,(1,2))

def _ratio(a,b):
    if not a or not b: return None
    return SequenceMatcher(None,a.lower().strip(),b.lower().strip()).ratio()

def _image_signal(a,b):
    """Two unrelated photos still share about half of their dHash bits by chance (raw similarity ~0.5),
    so only the part above chance counts: 0.5 -> 0.0 and identical -> 1.0."""
    sim=image_similarity(a,b)
    return None if sim is None else max(0.0,(sim-0.5)/0.5)

def score_pair(lost,found):
    desc=' '.join(filter(None,[lost.title,lost.description,lost.distinguishing_features,lost.brand,lost.model]))
    fdesc=' '.join(filter(None,[found.title,found.description,found.distinguishing_features,found.brand,found.model]))
    parts={
      'description':_text(desc,fdesc),
      'category':1.0 if lost.category_id==found.category_id else 0.0,
      'location':1.0 if lost.location_id==found.location_id else _ratio(lost.location.name,found.location.name),
      'date': max(0.0,1-(abs((lost.date_event-found.date_event).days)/14.0)) if lost.date_event and found.date_event else None,
      'image': _image_signal(lost.image_phash,found.image_phash),
    }
    attrs=[]
    for a,b in [(lost.color,found.color),(lost.brand,found.brand),(lost.model,found.model)]:
        r=_ratio(a,b)
        if r is not None: attrs.append(r)
    parts['attributes']=sum(attrs)/len(attrs) if attrs else None
    available={k:v for k,v in parts.items() if v is not None}
    denom=sum(WEIGHTS[k] for k in available)
    score=sum(WEIGHTS[k]*v for k,v in available.items())/denom if denom else 0.0
    reasons=[]
    if parts['category'] and parts['category']>.9: reasons.append('Same category')
    if parts['description'] and parts['description']>.35: reasons.append('Similar description')
    if parts['location'] and parts['location']>.65: reasons.append('Same or nearby location')
    if parts['date'] and parts['date']>.65: reasons.append('Close date')
    if parts['attributes'] and parts['attributes']>.6: reasons.append('Matching color/brand/model')
    if parts['image'] and parts['image']>.80: reasons.append('AI vision: photos look visually similar')
    return score,parts,reasons

def _log_pair(lost,found,score,parts,reasons,threshold,passed):
    """Remember every scored pair (even those below the threshold) so admins can explain a result."""
    row=MatchLog.query.filter_by(lost_item_id=lost.id,found_item_id=found.id).first() or MatchLog(lost_item_id=lost.id,found_item_id=found.id)
    row.score=score; row.threshold=threshold; row.passed=passed
    row.description_score=parts['description'] or 0; row.category_score=parts['category'] or 0; row.location_score=parts['location'] or 0
    row.date_score=parts['date'] or 0; row.attribute_score=parts['attributes'] or 0; row.image_score=parts['image'] or 0; row.reasons_json=reasons
    db.session.add(row)

def refresh_matches_for_item(item,threshold=0.80):
    opposite='FOUND' if item.item_type=='LOST' else 'LOST'
    q=Item.query.filter(Item.item_type==opposite,Item.status.in_(['ACTIVE','MATCHED','CLAIM_PENDING','VERIFICATION_PENDING']))
    if item.organization_id: q=q.filter((Item.organization_id==item.organization_id)|(Item.organization_id.is_(None)))
    q=q.filter(Item.date_event.between(item.date_event-timedelta(days=30),item.date_event+timedelta(days=30)))
    created=[]
    for other in q.limit(200):
        lost,found=(item,other) if item.item_type=='LOST' else (other,item)
        score,parts,reasons=score_pair(lost,found)
        passed=score>=threshold
        _log_pair(lost,found,score,parts,reasons,threshold,passed)
        if not passed: continue
        m=Match.query.filter_by(lost_item_id=lost.id,found_item_id=found.id).first() or Match(lost_item_id=lost.id,found_item_id=found.id)
        m.score=score; m.description_score=parts['description'] or 0; m.category_score=parts['category'] or 0; m.location_score=parts['location'] or 0; m.date_score=parts['date'] or 0; m.attribute_score=parts['attributes'] or 0; m.image_score=parts['image'] or 0; m.reasons_json=reasons
        db.session.add(m); created.append(m)
        for u in {lost.user_id,found.user_id}:
            if not Notification.query.filter_by(user_id=u,type='MATCH',item_id=item.id).first():
                db.session.add(Notification(user_id=u,type='MATCH',title='Possible match found',message=f'A possible match scored {round(score*100)}%. Verification is required.',item_id=item.id))
    if created and item.status=='ACTIVE': item.status='MATCHED'
    db.session.commit(); return created
