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
from langchain_core.messages import HumanMessage, AIMessage
import uuid
from groq import Groq

# Load environment variables
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
env_path = os.path.join(project_root, '.env')

# Load the .env file
load_dotenv(dotenv_path=env_path)
openai_key = os.getenv("OPENAI_API_KEY")
groq_key = os.getenv("GROQ_API_KEY")

# Constants
CHROMA_PATH = "chroma"

# Chat session history
chat_sessions = {}

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
    client = OpenAI(api_key=openai_key)
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
    # Clear out the database first.
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)

    # Create a new DB from the documents.
    db = Chroma.from_documents(
        documents, OpenAIEmbeddings(), persist_directory=CHROMA_PATH
    )
    print(f"Saved {len(documents)} chunks to {CHROMA_PATH}.")

def query_chroma_and_generate_response(query_text: str, session_id: str = None, k: int = 2):
    embedding_function = OpenAIEmbeddings()
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
    
    results = db.similarity_search_with_relevance_scores(query_text, k=k)
    
    if len(results) == 0 or results[0][1] < 0.7:
        return {
            "query_type": "chat",
            "response": "I'm sorry, but I couldn't find any relevant information to answer your question."
        }

    context_text = "\n\n---\n\n".join([doc.metadata['summary'] for doc, _score in results])
    return context_text

def get_chat_completion(messages: list, model_name: str = "llama-3.1-70b-versatile"):
    """
    Generates a chat completion using Groq's chat completion API, allowing for message history.
    
    Args:
        messages (list): A list of dictionaries representing the message history in the conversation.
                         Each dictionary should have 'role' and 'content' keys.
        model_name (str): The model to be used for generating the response. Default is "llama3-8b-8192".
    
    Returns:
        str: The assistant's response message content.
    """
    try:
        client = Groq()
        chat_completion = client.chat.completions.create(
            messages=messages,
            model=model_name,
        )
        # Extract and return the response content
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"Error generating chat completion: {e}")
        return None

def run_chat_session(user_message: str):
    """
    Runs a chat session with the given user message.
    
    Args:
        user_message (str): The user's message to start the chat session.
    
    Returns:
        str: The assistant's response message content.
    """
    print("Initializing chat session...")
    message_history = [
         {
            "role": "system",
            "content": """You are a virtual assistant for Irembo, the Rwandan government's e-services platform. Your primary role is to help citizens navigate and use the various services available on the Irembo website. Here are your key responsibilities:

            1. Guide users through the process of accessing different government services on Irembo.
            2. Provide information about required documents, fees, and procedures for specific services.
            3. Assist with troubleshooting common issues users might encounter while using the platform.
            4. Offer clear, step-by-step instructions for completing online applications and forms.
            5. Explain the status of ongoing service requests and how to track them.
            6. Direct users to the appropriate departments or contact points for complex issues beyond your scope.

            You will be provided with relevant, up-to-date context for each user query to ensure your responses are accurate and helpful. Always maintain a professional, friendly, and patient demeanor, as you are representing the Rwandan government. If you're unsure about any information, it's better to acknowledge your uncertainty and suggest where the user might find more accurate details.

            Important: You **must** strictly return all responses in the following JSON format. Do not include any extra explanations or text outside of the JSON format.

            {
            "data": "Your response here",
            "op_type": "new/renew/chat",
            "redir_url": "new/renew/chat"
            }

            For any query related to student permits, set `op_type` to either "new" or "renew" based on whether the user is asking about a new or renewal process for the permit. For all other queries, use `chat` for both `op_type` and `redir_url`.

            Example 1:
            Query: How do I renew my student permit?
            Response:
            {
            "data": "To renew your student permit, you need to provide your current permit, a valid passport, and proof of enrollment. The fee is 10,000 RWF, and processing takes 7 business days.",
            "op_type": "renew",
            "redir_url": "renew"
            }

            Example 2:
            Query: What is the fee for a birth certificate?
            Response:
            {
            "data": "The fee for obtaining a birth certificate is 2,000 RWF, and it can be processed within 3 business days.",
            "op_type": "chat",
            "redir_url": "chat"
            }

            Strictly follow this format for all outputs. If the response doesn't match the JSON structure, reformat it accordingly before returning."""
        }
    ]

    # Retrieve relevant context
    context = query_chroma_and_generate_response(user_message)
    
    # Append user message and context to the history
    message_history.append({"role": "user", "content": f"Context: {context}\n\nQuestion: {user_message}"})
    
    # Get assistant response
    assistant_response = get_chat_completion(message_history)
    print("RESPONSE")
    
    print(assistant_response)
    # if assistant_response:
        # Append assistant's response to the message history
    message_history.append({"role": "assistant", "content": assistant_response})
    response_json = json.loads(assistant_response)
    print("before return")
    return response_json
    # else:
        # return "Failed to generate a response."

# # Example usage:
# if __name__ == "__main__":
#     user_query = input("User: ")
#     response = run_chat_session(user_query)
#     print(f"Assistant: {response}")