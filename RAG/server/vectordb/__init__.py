from .vectorDbHandeller import VectorDBSingleton

# This will be imported when Django starts
vector_db = VectorDBSingleton.get_instance()

__all__ = ["vector_db"]