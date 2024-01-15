from flask import Flask, request, render_template
from sentence_transformers import SentenceTransformer, util
from pymongo import MongoClient
import params

app = Flask(__name__)

# Load the sentence transformer model for encoding sentences.
# This is a one-time operation at the start of the application.
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')


@app.route('/', methods=['GET', 'POST'])
def index():
    # Default question to be used when the page loads for the first time
    query = "Where can I find training?"

    last_used_question = ""

    if request.method == 'POST':
        # If the method is POST, i.e., the form has been submitted,
        # get the submitted question from the form data.
        query = request.form['question']
        last_used_question = query

    # Encode the submitted question into a vector using the loaded model
    query_vector = model.encode(query).tolist()

    # Connect to MongoDB using the connection string and database details from params
    mongo_client = MongoClient(params.mongodb_conn_string)
    result_collection = mongo_client[params.database][params.collection]

    desired_answers = 5  # Number of desired answers to fetch

    # Define the aggregation pipeline for vector search in MongoDB
    # It uses the vector index to find the most relevant documents based on the query vector
    pipeline_vector = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "queryVector": query_vector,
                "path": "sentenceVector",
                "numCandidates": 75,
                "limit": 15
            }
        },
        {
            "$limit": desired_answers
        }
    ]

    # Define the aggregation pipeline for lexical search in MongoDB
    # It uses a text index to perform a text search on the documents
    pipeline_lexical = [
        {
            '$search': {
                'index': 'lexical',
                'text': {
                    'query': query,
                    'path': 'sentence'
                }
            }
        }, {
            '$limit': desired_answers
        }
    ]

    # Execute the aggregation pipelines and fetch results
    results_vector = result_collection.aggregate(pipeline_vector)
    results_lexical = result_collection.aggregate(pipeline_lexical)

    # Process and store the results from the vector search
    answer_list_vector = []
    for result in results_vector:
        answer = {
            'pdf': result['pdf'],
            'page': result['page'],
            'sentence': result['sentence'],
            'type': result['type']
        }
        answer_list_vector.append(answer)

    # Process and store the results from the lexical search
    answer_list_lexical = []
    for result in results_lexical:
        answer = {
            'pdf': result['pdf'],
            'page': result['page'],
            'sentence': result['sentence'],
            'type': result['type']
        }
        answer_list_lexical.append(answer)

    # Render the HTML template with the query and the results
    return render_template('index.html', query=query, answers_vector=answer_list_vector, answers_lexical=answer_list_lexical, last_used_question=last_used_question)


# Run the Flask app in debug mode if this script is the main program
if __name__ == '__main__':
    app.run(debug=True)
