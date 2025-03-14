from typing import List, Dict
from google.cloud import aiplatform
from google.cloud.aiplatform import GenerativeModel

class LLMInterface:
    def __init__(self, api_key: str):
        self.api_key = api_key
        aiplatform.init()
        self.flash2_model = GenerativeModel("text-bison@002")
        self.gemini_model = GenerativeModel("gemini-pro")
        self.reranker_model = GenerativeModel("textembedding-gecko@002")

    def paraphrase_question(self, question: str) -> str:
        """Paraphrase the user question using Flash-2."""
        prompt = f"""
        Paraphrase the following question to improve retrieval:
        Question: {question}
        Paraphrased version:
        """
        response = self.flash2_model.predict(prompt)
        return response.text

    def rerank_passages(self, question: str, passages: List[str]) -> List[Dict]:
        """Rerank passages using Google's reranker."""
        scores = self.reranker_model.get_relevance_scores(
            query=question,
            passages=passages
        )
        
        ranked_results = [
            {"passage": passage, "score": float(score)}
            for passage, score in zip(passages, scores)
        ]
        ranked_results.sort(key=lambda x: x["score"], reverse=True)
        return ranked_results

    def generate_answer(self, question: str, context: List[str]) -> Dict:
        """Generate final answer using Gemini Pro."""
        prompt = f"""
        Answer the following question using only the provided context. 
        If the answer cannot be found in the context, say so.
        
        Context:
        {' '.join(context)}
        
        Question: {question}
        
        Provide a detailed answer with citations to the relevant parts of the context.
        """
        
        response = self.gemini_model.predict(prompt)
        
        return {
            "answer": response.text,
            "citations": self._extract_citations(response.text, context)
        }

    def _extract_citations(self, answer: str, context: List[str]) -> List[Dict]:
        """Extract citations from the generated answer."""
        citations = []
        for passage in context:
            if passage in answer:
                citations.append({
                    "text": passage,
                    "relevance": 1.0  # This could be improved with more sophisticated matching
                })
        return citations
