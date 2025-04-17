from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class RetrieverService:
    def __init__(self, vector_db, user_id):
        self.db = vector_db.db
        self.user_id = user_id
        self.cross_encoder = HuggingFaceCrossEncoder(
            model_name=os.getenv("CROSS_ENCODER_MODEL",
                                 "cross-encoder/ms-marco-MiniLM-L-6-v2"),
            model_kwargs={'device': os.getenv("CROSS_ENCODER_DEVICE", "cpu")}
        )

    def get_reranking_retriever(self, k: int = None, scrape_ids: list = None):
        """
        Get a retriever that performs initial retrieval followed by cross-encoder re-ranking.

        Args:
            k: Number of documents to return after re-ranking
            scrape_ids: Optional list of scrape_ids to filter documents by
        """
        # Use environment variable if k is not provided
        if k is None:
            k = int(os.getenv("RETRIEVAL_TOP_K", 6))

        filter_condition = {"user_id": self.user_id}

        # Add scrape_ids filter if provided
        if scrape_ids:
            filter_condition = {
                "$and": [
                    {"user_id": self.user_id},
                    {"scrape_id": {"$in": scrape_ids}}
                ]
            }

        base_retriever = self.db.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": k * 3,  # Retrieve more documents for re-ranking
                "filter": filter_condition
            }
        )
        reranker = CrossEncoderReranker(model=self.cross_encoder, top_n=k)
        return ContextualCompressionRetriever(
            base_compressor=reranker,
            base_retriever=base_retriever
        )

    # def retrieve_and_rerank(self, query: str, initial_k: int = 12, top_k: int = 4):
    #     """
    #     Retrieve initial documents and then re-rank them using the cross-encoder.
    #     Returns both the initial and re-ranked documents for comparison.
    #     """
    #     # Initial retrieval
    #     base_retriever = self.db.as_retriever(
    #         search_type="similarity",
    #         search_kwargs={"k": initial_k}
    #     )
    #     initial_results = base_retriever.get_relevant_documents(query)

    #     # Re-ranking
    #     reranker = CrossEncoderReranker(model=self.cross_encoder, top_n=top_k)
    #     compression_retriever = ContextualCompressionRetriever(
    #         base_compressor=reranker,
    #         base_retriever=base_retriever
    #     )
    #     reranked_results = compression_retriever.get_relevant_documents(query)

    #     return initial_results, reranked_results
