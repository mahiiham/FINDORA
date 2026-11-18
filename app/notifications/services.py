from app.extensions import db
from app.models import Notification

def notify(user_id,type_,title,message,item_id=None,claim_id=None,link=None):
    """Create an in-app alert. `link` (optional) is a relative URL the alert opens, e.g. a chat or ticket."""
    n=Notification(user_id=user_id,type=type_,title=title,message=message,item_id=item_id,claim_id=claim_id,link=link); db.session.add(n); return n
