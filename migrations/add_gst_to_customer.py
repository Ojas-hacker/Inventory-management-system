from app import db
from models import Customer

def upgrade():
    # Add GST number column
    db.session.execute('ALTER TABLE customer ADD COLUMN gst_number VARCHAR(15)')
    db.session.commit()

def downgrade():
    # Remove GST number column
    db.session.execute('ALTER TABLE customer DROP COLUMN gst_number')
    db.session.commit()
