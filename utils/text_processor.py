import os
import hashlib
from typing import List, Tuple
import nltk
from nltk.tokenize import sent_tokenize
nltk.download('punkt')

class TextProcessor:
    def __init__(self, chunk_size: int = 5):
        self.chunk_size = chunk_size

    def process_directory(self, directory_path: str) -> List[Tuple[str, str, List[str]]]:
        """Process all text files in a directory and its subdirectories."""
        processed_files = []
        
        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.endswith('.txt'):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Calculate content hash
                    content_hash = hashlib.sha256(content.encode()).hexdigest()
                    
                    # Process chunks
                    chunks = self.chunk_text(content)
                    
                    processed_files.append((file, content_hash, chunks))
                    
        return processed_files

    def chunk_text(self, text: str) -> List[str]:
        """Chunk text by sentences or paragraphs."""
        if '\n\n' in text:  # If text contains paragraphs
            chunks = text.split('\n\n')
        else:
            sentences = sent_tokenize(text)
            chunks = []
            current_chunk = []
            
            for sentence in sentences:
                current_chunk.append(sentence)
                if len(current_chunk) >= self.chunk_size:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = []
                    
            if current_chunk:  # Add remaining sentences
                chunks.append(' '.join(current_chunk))
                
        return [chunk.strip() for chunk in chunks if chunk.strip()]
