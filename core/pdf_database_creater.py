from core.pdf_reader import get_md_content
# from pdf_reader import get_md_content
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss
from rank_bm25 import BM25Okapi
from langchain_text_splitters import RecursiveCharacterTextSplitter

from typing import List

# def get_embedding_vector(md_contents: list[dict], embedding_model='all-MiniLM-L6-v2') -> tuple:
#     model = SentenceTransformer(embedding_model)
#     embeddings = []
#     metadatas = []

#     for md_content in md_contents:
#         vector = model.encode(md_content['content'])
#         embeddings.append(vector)
#         metadatas.append(md_content)

#     return embeddings, metadatas

# def create_database_for_pdf(embedding_model='all-MiniLM-L6-v2') -> tuple:
#     md_contents = get_md_content()
#     embeddings, metadatas = get_embedding_vector(md_contents=md_contents, embedding_model=embedding_model)

#     # convert to numpy
#     embedding_matrix = np.stack(embeddings).astype("float32")
#     faiss.normalize_L2(embedding_matrix)

#     # FAISS index
#     dimension = embedding_matrix.shape[1]
#     index = faiss.IndexFlatIP(dimension)
#     index.add(embedding_matrix)
#     print('database created')
#     return index, metadatas 

    
def keyword_search(query, top_k=5, input_path = '', content = None):
    if content is None:
        md_contents = get_md_content(input_path)
    else:
        print("có content")
        md_contents = content
    chuncks = semantic_chunking(md_contents, chunk_size=1000, chunk_overlap=150)
    all_texts = [item["content"] for item in chuncks]
# Tokenize từng document
    tokenized_docs = [doc.split() for doc in all_texts]
    bm25 = BM25Okapi(tokenized_docs)
    tokenized_query = query.split()
    top_docs = bm25.get_top_n(tokenized_query, all_texts, n=top_k)
    # Trả về dict gốc thay vì chỉ text
    return [chuncks[all_texts.index(doc)] for doc in top_docs]

def semantic_chunking(text: str, chunk_size=1500, chunk_overlap=500):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunks = splitter.split_text(text)
    md_chunks = [{'Page': i+1, 'content': chunk} for i, chunk in enumerate(chunks)]
    return md_chunks

def get_embeddings(chunks: List[dict], embedding_model='all-MiniLM-L6-v2'):
    model = SentenceTransformer(embedding_model)
    embeddings = []
    metadatas = []
    for chunk in chunks:
        vector = model.encode(chunk['content'])
        embeddings.append(vector)
        metadatas.append(chunk)
    embedding_matrix = np.stack(embeddings).astype('float32')
    faiss.normalize_L2(embedding_matrix)
    return embedding_matrix, metadatas

def create_faiss_index(embedding_matrix):
    dimension = embedding_matrix.shape[1]
    index = faiss.IndexFlatIP(dimension)  # cosine similarity
    index.add(embedding_matrix)
    print(f"FAISS index created with {index.ntotal} chunks")
    return index

def create_database_for_pdf(input_path = "",embedding_model='all-MiniLM-L6-v2', content = None):
    if content is not None:
        print("có content")
        md_content  = content
    else:
        md_content = get_md_content(input_path)     
    md_chunks = semantic_chunking(md_content, chunk_size=1000, chunk_overlap=150)

    embedding_matrix, metadatas = get_embeddings(md_chunks, embedding_model='all-MiniLM-L6-v2')
    faiss_index = create_faiss_index(embedding_matrix)
    print("Tạo db thành công")
    return faiss_index, metadatas