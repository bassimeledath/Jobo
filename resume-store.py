import nest_asyncio
nest_asyncio.apply()
from llama_parse import LlamaParse
from dotenv import load_dotenv
from llama_index.vector_stores import AstraDBVectorStore
from llama_index import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
)
import os

load_dotenv()

LLAMA_PARSE_API_KEY = os.environ.get("LLAMA_PARSE_API_KEY")
ASTRA_DB_APPLICATION_TOKEN = os.environ.get("ASTRA_DB_APPLICATION_TOKEN")
ASTRA_DB_API_ENDPOINT = os.environ.get("ASTRA_DB_API_ENDPOINT")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Parse text from PDF using LlamaParse TODO
def llamaparse_text_from_pdf(file_path):
    parser = LlamaParse(
        api_key=LLAMA_PARSE_API_KEY,  # can also be set in your env as LLAMA_CLOUD_API_KEY
        result_type="markdown",  # "markdown" and "text" are available
        verbose=True
    )
    documents = parser.load_data(file_path)
    return documents

# Create a query engine from index of the resume
def create_resume_query_engine(documents, collection_name):
    astra_db_store = AstraDBVectorStore(
        token=ASTRA_DB_APPLICATION_TOKEN,
        api_endpoint=ASTRA_DB_API_ENDPOINT,
        collection_name=collection_name,
        embedding_dimension=1536,
    )
    storage_context = StorageContext.from_defaults(vector_store=astra_db_store) 
    index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)
    return index.as_query_engine()

def main():
    bassim = llamaparse_text_from_pdf("db/resume-bassim.pdf")
    bassim_query_eng = create_resume_query_engine(bassim, "bassim_resume")

if __name__ == "__main__":
    main()
