from llama_index.schema import TextNode
import pandas as pd
import os
from llama_index.vector_stores import AstraDBVectorStore
from llama_index import (
    VectorStoreIndex,
    StorageContext,
)
from dotenv import load_dotenv

load_dotenv()

ASTRA_DB_APPLICATION_TOKEN = os.environ.get("ASTRA_DB_APPLICATION_TOKEN")
ASTRA_DB_API_ENDPOINT = os.environ.get("ASTRA_DB_API_ENDPOINT")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Create job vector store
# Load data
df = pd.read_csv("db/clean_jobs.csv")
# Remove jobs with no description and job URL
df_clean = df.dropna(subset=['description', 'job_url'])
# Fill the missing metadata fields with an empty string
df_clean = df_clean.fillna("None")
# Drop the search_key column
df_clean.drop('search_key', axis=1, inplace=True)
# Remove duplicated entries
df_clean.drop_duplicates(inplace=True)

# Convert jobs to nodes
nodes = []
for i in range(len(df_clean)):
    text = ' '.join(df_clean[['title', 'company', 'location', 'job_type', 'description']].iloc[i].values)
    metadata = df_clean.iloc[i].drop('description')
    cur_node = TextNode(
        text=(text),
        metadata=zip(metadata.index.values, metadata.values),
    )
    nodes.append(cur_node)
# Initialize an Astra db called jobo_jobs
astra_db_store = AstraDBVectorStore(
    token=ASTRA_DB_APPLICATION_TOKEN,
    api_endpoint=ASTRA_DB_API_ENDPOINT,
    collection_name="jobo_jobs",
    embedding_dimension=1536,
)
# Ingest nodes in vector store
storage_context = StorageContext.from_defaults(vector_store=astra_db_store) 
index = VectorStoreIndex(nodes, storage_context=storage_context)