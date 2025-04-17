from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
import threading

class VectorDBHandler:
    def __init__(self, persist_directory):
        print("Initializing VectorDBHandler...")
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        model_kwargs = {'device': 'cpu'}
        encode_kwargs = {'normalize_embeddings': False}
        self.embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs
        )
        self.db = Chroma(
            persist_directory=persist_directory,
            embedding_function=self.embeddings
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1200,
            chunk_overlap=300,
            length_function=len,
            add_start_index=True,
        )

    def process_markdown(self, markdown_content, url, scrape_id, user_id):
        try:
            chunks = self.text_splitter.split_text(markdown_content)
            texts = []
            metadatas = []
            for i, chunk in enumerate(chunks):
                texts.append(chunk)
                metadatas.append({
                    "url": url,
                    "chunk_index": i,
                    "scrape_id": scrape_id,
                    "user_id": user_id
                })
    
            self.db.add_texts(texts=texts, metadatas=metadatas)
            print(f"Successfully processed and saved embeddings for {url} with {len(chunks)} chunks")
    
        except Exception as e:
            print(f"Error processing markdown for {url}: {str(e)}")

    def process_scraped_content(self, scraped_content):
        threads = []
        for content in scraped_content:
            if content['content_type'] == 'MARKDOWN':
                thread = threading.Thread(
                    target=self.process_markdown,
                    args=(content['content'], content['link'], content['scrape'].id)
                )
                threads.append(thread)
                thread.start()

        for thread in threads:
            thread.join()

    def delete_embeddings(self, scrape_id):
        try:
            self.db.delete(where={"scrape_id": scrape_id})
            return True
        except Exception as e:
            print(f"Error deleting embeddings: {str(e)}")
            return False

    def delete_by_id(self, id_type, id_value):
        """
        Delete embeddings by ID type and value
        id_type: 'scrape_id' or 'file_id'
        id_value: the actual ID value
        """
        try:
            # Delete embeddings where id_type matches id_value
            self.db.delete(where={id_type: id_value})
            print(f"Successfully deleted embeddings for {id_type}: {id_value}")
            return True
        except Exception as e:
            print(f"Error deleting embeddings for {id_type} {id_value}: {str(e)}")
            return False
        

class VectorDBSingleton:
    _instance = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls, persist_directory="vectordb"):
        if cls._instance is None:
            with cls._lock:
                print("Initializing VectorDBHandler (singleton)...")
                if cls._instance is None:
                    cls._instance = VectorDBHandler(persist_directory)
        return cls._instance
