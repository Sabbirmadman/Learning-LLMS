from django.apps import AppConfig

class VectordbConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'vectordb'
    
    def ready(self):
        # Import and initialize the singleton when Django starts
        print("Pre-initializing VectorDB for faster responses...")
        from .vectorDbHandeller import VectorDBSingleton
        VectorDBSingleton.get_instance()
        print("VectorDB initialization complete and ready for use")