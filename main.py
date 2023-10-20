from flask import Flask, render_template
import firebase_admin
from firebase_admin import credentials, db, firestore
from firebase import Firebase
import uuid

# Initialize Flask
app = Flask(__name__)

# Initialize Firebase
crud = Firebase()

# Generate random document id
def generate_document_id():
        # Generate a random unique identifier
        unique_id = str(uuid.uuid4())
        return f"reviews-{unique_id}"

@app.route('/')
def display_reviews():
    result = crud.get("reviews")

    document_id = generate_document_id()

    # Add a document to a collection with a specific ID
    data = {"userID": 5432, "carID": 3333}
    crud.add('reviews', data=data, document_id= document_id)


    return render_template('test.html', reviews=result)

if __name__ == '__main__':
    app.run(debug=True)
