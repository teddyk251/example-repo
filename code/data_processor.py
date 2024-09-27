import json
from langchain.docstore.document import Document
import datetime

with open("data/web_scrape_output_with_content.json", "r", encoding="utf-8") as f:
    data = json.load(f)

documents = []

for category in data["categories"]:
    for sub_category in category["subcategories"]:
        temp_document = [Document(
            page_content=article["content"]['body'],
            metadata={
                "title": article["doc_title"],
                "subcategory_title": sub_category["subcategory_title"],
                "category_title": category["title"],
                "category_text": category["content"],
                "scraped_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        ) for article in sub_category["documents"]]
        
        documents.extend(temp_document)

print(documents[0])