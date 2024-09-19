from flask import Flask, request, jsonify, g
from PyPDF2 import PdfReader
import spacy, time

# Load the NER model (consider using environment variables for external loading)
nlp = spacy.load('ner_model')

# Create a base class for API resources
class APIResource:
    def __init__(self, app):
        self.app = app

    def get(self):
        raise NotImplementedError("Method not implemented")

    @classmethod
    def register(cls, app, url):
        @app.route(url, methods=['POST'])
        def wrapper():
            resource = cls(app)
            return resource.post()

        return wrapper

# Create a specific resource class for handling PDF uploads
class UploadPDFResource(APIResource):
    def post(self):
        if 'pdf' not in request.files:
            return jsonify({"error": "No PDF file part"}), 400

        pdf = request.files['pdf']

        if pdf.filename == '':
            return jsonify({"error": "No file selected"}), 400

        if pdf.filename.endswith('.pdf'):
            # Extract text from the PDF
            pdf_text = self.extract_text_from_pdf(pdf)

            # Process the extracted text using the NER model
            doc = nlp(pdf_text)
            entities = [(ent.text, ent.label_) for ent in doc.ents]

            return jsonify({'entities': entities})
        else:
            return jsonify({"error": "Invalid file type. Only PDF files are allowed."}), 400

    def extract_text_from_pdf(self, pdf_file):
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text

# Create the Flask app instance
app = Flask(__name__)

# Register the API resource with the app
UploadPDFResource.register(app, '/upload-pdf')

# Logging request time (consider using a dedicated logging library)
@app.before_request
def start_timer():
    g.start_time = time.time()

@app.after_request
def log_request_time(response):
    if hasattr(g, 'start_time'):
        duration = time.time() - g.start_time
        response.headers['X-Response-Time'] = f'{duration:.3f}s'
        app.logger.info(f"Request to {request.path} took {duration:.3f} seconds")
    return response

if __name__ == '__main__':
    app.run(debug=True)