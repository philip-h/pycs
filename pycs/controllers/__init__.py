from pycs.extensions import db

def commit_change():
    db.session.commit()
