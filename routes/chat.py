from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app import db
from models import Conversation, Message, Citation
from utils.llm_interface import LLMInterface
from utils.vector_store import VectorStore

chat_bp = Blueprint('chat', __name__)

llm = LLMInterface(api_key=app.config["GOOGLE_API_KEY"])
vector_store = VectorStore(
    api_key=app.config["VECTOR_DB_API_KEY"],
    host=app.config["VECTOR_DB_HOST"]
)

@chat_bp.route('/')
@login_required
def index():
    conversations = Conversation.query.filter_by(user_id=current_user.id).order_by(Conversation.created_at.desc()).all()
    return render_template('chat.html', conversations=conversations)

@chat_bp.route('/api/ask', methods=['POST'])
@login_required
def ask():
    # Check quota
    if not current_user.is_paid and current_user.questions_asked >= app.config["FREE_QUOTA"]:
        return jsonify({
            "error": "Free quota exceeded. Please upgrade to continue."
        }), 403
    
    if current_user.is_paid and current_user.questions_asked >= app.config["PAID_QUOTA"]:
        return jsonify({
            "error": "Monthly quota exceeded. Please wait for reset."
        }), 403

    data = request.json
    question = data.get('question')
    conversation_id = data.get('conversation_id')
    
    try:
        # Create new conversation if needed
        if not conversation_id:
            conversation = Conversation(user_id=current_user.id, title=question[:50])
            db.session.add(conversation)
            db.session.commit()
            conversation_id = conversation.id
        
        # Process question
        paraphrased = llm.paraphrase_question(question)
        
        # Vector search
        results = vector_store.hybrid_search(paraphrased)
        
        # Rerank results
        reranked = llm.rerank_passages(question, [r["text"] for r in results])
        
        # Generate answer
        response = llm.generate_answer(question, [r["passage"] for r in reranked[:3]])
        
        # Save message and citations
        message = Message(
            conversation_id=conversation_id,
            content=response["answer"],
            is_user=False
        )
        db.session.add(message)
        
        for citation in response["citations"]:
            cite = Citation(
                message_id=message.id,
                source_text=citation["text"],
                relevance_score=citation["relevance"]
            )
            db.session.add(cite)
        
        # Update question count
        current_user.questions_asked += 1
        db.session.commit()
        
        return jsonify({
            "answer": response["answer"],
            "citations": response["citations"],
            "conversation_id": conversation_id
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@chat_bp.route('/api/conversations/<int:conversation_id>')
@login_required
def get_conversation(conversation_id):
    conversation = Conversation.query.get_or_404(conversation_id)
    if conversation.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
        
    messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.created_at).all()
    return jsonify({
        "messages": [{
            "content": msg.content,
            "is_user": msg.is_user,
            "citations": [
                {"text": c.source_text, "score": c.relevance_score}
                for c in msg.citations
            ]
        } for msg in messages]
    })
