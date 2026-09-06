from langchain_huggingface import HuggingFaceEmbeddings
import config
def get_embedding_function():
    return HuggingFaceEmbeddings(model_name= config.EMBEDDING_MODEL_NAME)
    