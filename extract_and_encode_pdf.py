# Import necessary libraries
from PyPDF2 import PdfReader  # For reading PDF files
from sentence_transformers import SentenceTransformer, util  # For sentence embedding
import params  # Custom parameters, likely for configuration
import os  # For interacting with the file system
from pymongo import MongoClient  # For MongoDB operations
from utils import *  # Importing all functions from utils.py
import re  # For regular expression operations

# Establish a connection to a MongoDB database and access a specific collection
mongo_client = MongoClient(params.mongodb_conn_string)
result_collection = mongo_client[params.database][params.collection]

# Clear the MongoDB collection while preserving its structure and indexes
result_collection.delete_many({})

# Specify the directory containing the PDF files to be processed
pdfDir = "PDFs"
for pdf in os.listdir(pdfDir):
    print("Reading:", pdf)
    reader = PdfReader(pdfDir + "/" + pdf)  # Read each PDF file
    number_of_pages = len(reader.pages)  # Count the number of pages in the PDF

    # Load the sentence embedding model
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    # Process each page of the PDF
    for page_number in range(number_of_pages):
        print(page_number + 1)
        page = reader.pages[page_number]  # Access each page
        text = page.extract_text()  # Extract text from the page
        sentences = split_into_sentences(text)  # Split text into sentences

        # Initialize a document to store results for each sentence
        result_doc = {}
        for sentence in sentences:
            # Filter out poorly extracted sentences using regex
            if not re.search("^[a-zA-Z]\s[a-zA-Z]\s", sentence):
                # Convert sentence to vector
                sentence_vector = model.encode(sentence).tolist()
                # Populate result document with details of the sentence
                result_doc['pdf'] = pdf
                result_doc['page'] = page_number
                result_doc['sentence'] = sentence
                result_doc['sentenceVector'] = sentence_vector
                result_doc['type'] = "customerService"
                # Insert the document into MongoDB
                result = result_collection.insert_one(result_doc.copy())
