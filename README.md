# CoMo - Continuous Monitoring

## Overview
CoMo (Continuous Monitoring) is a Streamlit application developed by HeyThatsMyLand (HTML) that enables users to extract, process, and search property information from public notices in Maharashtra newspapers. The application leverages Google's Gemini AI to perform OCR, translation, and structured data extraction from notice images.

## Features
- **OCR Processing**: Extract text from scanned public notice images
- **Language Detection & Translation**: Identify and translate non-English (Hindi/Marathi) text to English
- **Structured Data Extraction**: Parse property details, seller information, advocate details, and notice metadata
- **Simple Search**: Find properties using a general address search query
- **Advanced Search**: Search for properties using specific criteria like building name, locality, etc.
- **Database Management**: Save, load, and manage your property database
- **Pre-populated Sample Data**: Comes with sample property data so you can start using the app immediately

## Installation and Setup

### Prerequisites
- Python 3.8+
- Google Gemini API Key
- Internet connection

### Installation Steps

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/como-streamlit.git
cd como-streamlit

# Create a data directory (if it doesn't exist)
mkdir -p data
```

2. **Create a virtual environment**
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# For Windows:
venv\Scripts\activate
# For macOS/Linux:
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Get a Google Gemini API Key**
   - Visit the [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create an API key if you don't have one
   - Keep this key secure as you'll need it when using the application

### Running the Application Locally

```bash
streamlit run app.py
```

The application will start and open in your default web browser at http://localhost:8501

## Deployment on Streamlit Cloud

1. **Push your code to GitHub**
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

2. **Project Structure**
   Your directory structure should look like this:
   ```
   como-streamlit/
   ├── app.py                  # Main application file
   ├── requirements.txt        # Dependencies
   ├── README.md               # Documentation
   └── data/
       └── sample_database.json # Pre-populated database
   ```

3. **Deploy on Streamlit Cloud**
   - Visit [Streamlit Cloud](https://streamlit.io/cloud)
   - Sign in with GitHub
   - Click "New app"
   - Select your repository, branch, and main file path ("app.py")
   - Set the "Requirements" path to "requirements.txt"
   - Add your Google Gemini API key as a secret in the advanced settings (name: API_KEY)
   - Click "Deploy"

3. **Access Your App**
   - Once deployed, you'll get a unique URL for your application
   - Share this URL with others to let them use your application

## Using the Application

### 1. Home
- The homepage provides an overview of the application and its features
- Ensure your Google Gemini API Key is configured before proceeding

### 2. Upload & Process
- Upload public notice images in JPG/JPEG/PNG format
- Click "Process Selected Files" to extract property information
- Alternatively, paste notice text directly for processing
- Save the processed data to your database

### 3. Search
- Use Simple Search for general address queries
- Use Advanced Search to search by specific property attributes
- View detailed information about matching properties

### 4. Database
- View statistics about your property database
- Save your database as a JSON file for backup or sharing
- Load an existing database from a JSON file
- Delete individual properties or clear the entire database

## Important Notes

- Processing images requires API calls to Google Gemini, which may have usage limitations based on your API key
- The accuracy of extracted information depends on the quality of the input images
- For best results, ensure that the public notice images are clear and readable

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Authors
- Vedant Nevatia
- Pranav Jain

© 2025 HeyThatsMyLand