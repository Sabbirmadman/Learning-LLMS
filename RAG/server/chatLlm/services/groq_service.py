from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv
from chatLlm.services.retriever_service import RetrieverService
from vectordb import vector_db
from langgraph.graph import END
load_dotenv()


class StreamingCallbackHandler:
    def __init__(self, queue):
        self.queue = queue
        self.generated_text = ""
        self.ignore_llm = False  # Add this attribute
        self.ignore_chat_model = False  # Add this attribute
        self.raise_error = False
        self.answer_started = False

    def on_llm_new_token(self, token, **kwargs):
        if token is not None:
            self.generated_text += token
            self.queue.put(token)

    def on_llm_end(self, response, **kwargs):
        self.queue.put(END)

    def on_llm_error(self, error, **kwargs):
        self.queue.put({"error": str(error)})

    def on_chat_model_start(self, serialized, messages, **kwargs):
        # This method is called when the chat model starts generating
        pass

    def on_chat_model_end(self, response, **kwargs):
        # This method is called when the chat model finishes generating
        pass


class GroqChatService:
    def __init__(self, user_id):
        self.chat_model = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model_name=os.getenv("GROQ_MODEL_NAME", "llama-3.3-70b-specdec"),
            temperature=float(os.getenv("GROQ_TEMPERATURE", "0.7")),
            streaming=True
        )
        self.retriever_service = RetrieverService(vector_db, user_id)
        self.chain = None
        self.user_id = user_id

    def _create_chain(self, chat_history=None, streaming_callback=None, scrape_ids=None):
        # Get retriever with top_k from environment or default to 4
        top_k = int(os.getenv("RETRIEVAL_TOP_K", 4))
        retriever = self.retriever_service.get_reranking_retriever(
            k=top_k, scrape_ids=scrape_ids)

        # Configure callbacks
        callbacks = [streaming_callback] if streaming_callback else None

        # Configure prompt
        prompt_template = """You are a helpful assistant answering questions based on the provided context.

        Context: {context}
        Question: {question}
        Chat History: {chat_history}

        Instructions:
        - Use markdown formatting for your response
        - Do not repeat the question
        - Start with "ANSWER: "
        - Reference context when possible
        - For math equations, use LaTeX formatting with $...$ or $$...$$
        - For code examples referencing math variables, use plain text (d_k instead of $d_k$)
        - For explaining code with math notation, keep math notation outside code blocks

        Your response:"""

        qa_prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question", 'chat_history']
        )

        # Configure model with callbacks if needed
        chat_model = self.chat_model.with_config(
            {"callbacks": callbacks}) if callbacks else self.chat_model

        # Format chat history for the chain
        formatted_history = []
        if chat_history:
            for message in chat_history:
                if message["role"] == "user":
                    formatted_history.append(
                        {"role": "user", "content": message["content"]})
                elif message["role"] == "assistant":
                    formatted_history.append(
                        {"role": "assistant", "content": message["content"]})

        # Create chain with modern approach
        return ConversationalRetrievalChain.from_llm(
            llm=chat_model,
            retriever=retriever,
            return_source_documents=True,
            verbose=True,
            chain_type="stuff",
            combine_docs_chain_kwargs={"prompt": qa_prompt}
        )

    def generate_response(self, query: str, chat_history=None, scrape_ids=None) -> str:
        try:
            self.chain = self._create_chain(
                chat_history, scrape_ids=scrape_ids)

            # Debug: Check retriever results before invoking chain
            initial_k = int(os.getenv("RETRIEVAL_INITIAL_K", 8))
            retriever = self.retriever_service.get_reranking_retriever(
                k=initial_k, scrape_ids=scrape_ids)
            retrieved_docs = retriever.invoke(query)
            print(
                f"Retrieved {len(retrieved_docs)} documents for query: '{query}'")
            for i, doc in enumerate(retrieved_docs):
                print(
                    f"Doc {i+1} content preview: {doc.page_content[:100]}...")

            # Pass chat history directly in the request instead of using memory
            result = self.chain.invoke({
                "question": query,
                "chat_history": self._format_chat_history_for_chain(chat_history)
            })

            print(f"Context used in response: {result.get('context', 'None')}")
            return result["answer"]
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return "I apologize, but I encountered an error while processing your request."

    def _format_chat_history_for_chain(self, chat_history):
        if not chat_history:
            return []

        formatted_history = []
        for message in chat_history:
            if message["role"] == "user":
                formatted_history.append((message["content"], ""))
            elif message["role"] == "assistant" and formatted_history:
                # Update the last tuple's second element
                last_user_msg, _ = formatted_history[-1]
                formatted_history[-1] = (last_user_msg, message["content"])

        return formatted_history

    def generate_streaming_response(self, query: str, chat_history=None, streaming_callback=None, scrape_ids=None):
        try:
            self.chain = self._create_chain(
                chat_history, streaming_callback, scrape_ids=scrape_ids)
            return self.chain.invoke({
                "question": query,
                "chat_history": self._format_chat_history_for_chain(chat_history)
            })
        except Exception as e:
            print(f"Error generating streaming response: {str(e)}")
            if streaming_callback:
                error_msg = "I apologize, but I encountered an error while processing your request."
                for char in error_msg:
                    streaming_callback.on_llm_new_token(char)
            return {"answer": "I apologize, but I encountered an error while processing your request."}
