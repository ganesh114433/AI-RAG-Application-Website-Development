from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app import db
from models import Document
from utils.text_processor import TextProcessor
from utils.vector_store import VectorStore

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_paid:
        return "Unauthorized", 403
    documents = Document.query.order_by(Document.processed_at.desc()).all()
    return render_template('admin.html', documents=documents)

@admin_bp.route('/admin/process', methods=['POST'])
@login_required
def process_documents():
    if not current_user.is_paid:
        return jsonify({"error": "Unauthorized"}), 403
        
    directory = request.form.get('directory')
    chunk_size = int(request.form.get('chunk_size', 5))
    
    processor = TextProcessor(chunk_size=chunk_size)
    vector_store = VectorStore(
        api_key=app.config["VECTOR_DB_API_KEY"],
        host=app.config["VECTOR_DB_HOST"]
    )
    
    try:
        # Process files
        processed_files = processor.process_directory(directory)
        
        for filename, content_hash, chunks in processed_files:
            # Check if already processed
            if Document.query.filter_by(content_hash=content_hash).first():
                continue
                
            # Create document record
            doc = Document(
                filename=filename,
                content_hash=content_hash,
                chunk_count=len(chunks)
            )
            db.session.add(doc)
            
            # Upload to vector store
            metadata = [{"file": filename, "index": i} for i in range(len(chunks))]
            vector_store.upload_documents(chunks, metadata)
            
        db.session.commit()
        return jsonify({"message": "Processing complete"})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
