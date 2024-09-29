import os
import datetime
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain.tools.retriever import create_retriever_tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad.openai_tools import format_to_openai_tool_messages
import re

def extract_json_from_response(response):
    try:
        # Use regex to find content between the first set of curly braces
        json_string = re.search(r"\{.*\}", response, re.DOTALL).group()
        return json_string
    except AttributeError as e:
        # Handle regex matching errors
        print(f"Error: No valid JSON found in the response - {e}")
        return {"error": "Invalid JSON response"}

def load_environment_variables():
    load_dotenv()
    return os.getenv("OPENAI_API_KEY")

def initialize_components(openai_key):
    llm = ChatOpenAI(openai_api_key=openai_key, temperature=0 , model="gpt-4o")
    embeddings = OpenAIEmbeddings(openai_api_key=openai_key)
    return llm, embeddings

def process_data(file_path):
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

def create_or_load_vector_store(embeddings, data_file_path, vector_store_path):
    try:
        vector_store = FAISS.load_local(vector_store_path, embeddings, allow_dangerous_deserialization=True)
        print(f"Vector store loaded from {vector_store_path}")
    except:
        documents = process_data(data_file_path)
        vector_store = FAISS.from_documents(documents, embeddings)
        vector_store.save_local(vector_store_path)
        print(f"Vector store created and saved to {vector_store_path}")
    return vector_store

def setup_retriever_tool(vector_store):
    retriever = vector_store.as_retriever()
    retriever_tool = create_retriever_tool(
        retriever,
        "irembo_search",
        "Search for information about Irembo services. For any questions about Irembo service, you must use this tool!",
    )
    return retriever_tool

def setup_agent(llm, retriever_tool):
    tools = [retriever_tool]
    llm_with_tools = llm.bind_tools(tools)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """
            You are a virtual assistant for Irembo, the Rwandan government's e-services platform. Your primary role is to help citizens navigate and use the various services available on the Irembo website. Here are your key responsibilities:

            1. Guide users through the process of accessing different government services on Irembo.
            2. Provide information about required documents, fees, and procedures for specific services.
            3. Assist with troubleshooting common issues users might encounter while using the platform.
            4. Offer clear, step-by-step instructions for completing online applications and forms.
            5. Explain the status of ongoing service requests and how to track them.
            6. Direct users to the appropriate departments or contact points for complex issues beyond your scope.

            You will be provided with relevant, up-to-date context for each user query to ensure your responses are accurate and helpful. Always maintain a professional, friendly, and patient demeanor, as you are representing the Rwandan government. If you're unsure about any information, it's better to acknowledge your uncertainty and suggest where the user might find more accurate details.

            Important: For each response, only provide a concise one-paragraph summary (3-4 sentences) of the relevant information, requirements, timeline, fees and other relevant 
            information. 
            Important: You must strictly return all responses in the following JSON format. Do not include any extra explanations or text outside of the JSON format. Provide only one JSON object in your response.
            For any query related to student permits , set the value of op_type to either renew or new depending on whether user wants to renew or apply for new student permit.
            For any other query, set the value of op_type to chat.
            The value of redir_url takes on same value as op_type.

            Strictly follow this format for all outputs.
            
            {{
            "data": "Your response here",
            "op_type": "new|renew|chat",
            "redir_url": "new|renew|chat"
            }}
            
        """),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = (
        {
            "input": lambda x: x["input"],
            "agent_scratchpad": lambda x: format_to_openai_tool_messages(x["intermediate_steps"]),
        }
        | prompt
        | llm_with_tools
        | OpenAIToolsAgentOutputParser()
    )

    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False)
    return agent_executor

def get_irembo_assistant_response(user_query, data_file_path="data/web_scrape_output_with_content.json", vector_store_path="faiss"):
    openai_key = load_environment_variables()
    llm, embeddings = initialize_components(openai_key)
    vector_store = create_or_load_vector_store(embeddings, data_file_path, vector_store_path)
    retriever_tool = setup_retriever_tool(vector_store)
    agent_executor = setup_agent(llm, retriever_tool)
    result = agent_executor.invoke({"input": user_query})
    response = result['output']
    response= extract_json_from_response(response)
    response_json = json.loads(response)
    return response_json

# # Example usage
# if __name__ == "__main__":
#     user_query = "How much is a marriage certificate?"
#     response = get_irembo_assistant_response(user_query)
#     print('-----------')
#     print(type(response))
#     print(response)