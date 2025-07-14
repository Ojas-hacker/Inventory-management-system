from app import app, db
from sqlalchemy import text

def add_gst_column():
    with app.app_context():
        try:
            # Check if the column already exists
            inspector = db.inspect(db.engine)
            columns = [column['name'] for column in inspector.get_columns('customer')]
            
            if 'gst_number' not in columns:
                # For SQLite, we'll use direct SQL with text() since ALTER TABLE is limited
                with db.engine.connect() as conn:
                    conn.execute(text('ALTER TABLE customer ADD COLUMN gst_number VARCHAR(15)'))
                    conn.commit()
                print("Successfully added gst_number column to customer table.")
            else:
                print("gst_number column already exists in the customer table.")
        except Exception as e:
            print(f"Error during migration: {e}")
            db.session.rollback()

if __name__ == '__main__':
    add_gst_column()
