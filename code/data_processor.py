import json
import datetime
import os
import shutil
from dotenv import load_dotenv
from openai import OpenAI
from langchain.docstore.document import Document
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain.prompts import ChatPromptTemplate

# Load environment variables
load_dotenv()
openai_key = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=openai_key)

# Constants
CHROMA_PATH = "chroma"

def process_data(file_path):
    """
    Processes data from a JSON file and returns a list of langchain Document objects.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    documents = []
    for category in data["categories"]:
        for sub_category in category["subcategories"]:
            temp_documents = [
                Document(
                    page_content=article["content"]['body'],
                    metadata={
                        "title": article["doc_title"],
                        "subcategory_title": sub_category["subcategory_title"],
                        "category_title": category["title"],
                        "category_text": category["content"],
                        "scraped_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                ) for article in sub_category["documents"]
            ]
            documents.extend(temp_documents)

    return documents

def summarize_content(content):
    """Summarize content using OpenAI API"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Summarize this content. Only return the summarized text with no additional words or explanations: {content}"}
        ]
    )
    return response.choices[0].message.content.strip()

def add_summary_to_documents(documents):
    """Adds a summary as a new key to each document in the documents list"""
    summarized_documents = []
    for doc in documents:
        summary = summarize_content(doc.page_content)
        doc_with_summary = Document(
            page_content=doc.page_content,
            metadata={**doc.metadata, "summary": summary}
        )
        summarized_documents.append(doc_with_summary)
    return summarized_documents

def save_to_chroma(documents: list[Document]):
    """Save the data to Chroma using summaries for embeddings"""
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)

    texts = [doc.metadata["summary"] for doc in documents]
    metadatas = [
        {
            **doc.metadata,
            "full_content": doc.page_content,
            "summary": doc.metadata["summary"]
        }
        for doc in documents
    ]

    db = Chroma.from_texts(
        texts=texts,
        metadatas=metadatas,
        embedding=OpenAIEmbeddings(),
        persist_directory=CHROMA_PATH
    )
    #db.persist()
    print(f"Saved {len(documents)} documents to {CHROMA_PATH}.")

def query_chroma_and_generate_response(query_text: str, k: int = 4):
    """Query Chroma and generate a response using the full text context"""
    embedding_function = OpenAIEmbeddings()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
    
    results = db.similarity_search_with_relevance_scores(query_text, k=k)
    
    if len(results) == 0 or results[0][1] < 0.7:
        return "Unable to find matching results."

    context_text = "\n\n---\n\n".join([doc.metadata['full_content'] for doc, _score in results])
    
    PROMPT_TEMPLATE = """
    Answer the question based only on the following context:

    {context}

    ---

    Answer the question based on the above context: {question}
    """
    
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=query_text)
    
    model = ChatOpenAI()
    response_text = model.invoke(prompt)
    
    sources = [doc.metadata.get("title", "Unknown source") for doc, _score in results]
    formatted_response = f"Response: \n{response_text}\n\nSources:\n" + "\n".join(sources)
    
    return formatted_response

if __name__ == "__main__":
    # Process data
    documents = process_data("data/web_scrape_output_with_content.json")
    print('Done processing data')
    
    # Add summary to each document
    print("Adding summaries to documents...")
    summarized_documents = add_summary_to_documents(documents)

    # Save the data to Chroma
    save_to_chroma(summarized_documents)
    print("Summarization and saving to Chroma complete.")

    # Example query
    query = "How can I renew my visa?"
    response = query_chroma_and_generate_response(query)
    print(response)