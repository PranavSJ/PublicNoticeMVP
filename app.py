import streamlit as st
import os
import json
import time
import enum
import tempfile
from typing import List, Dict, Any, Optional
import requests
from PIL import Image
from io import BytesIO
from langdetect import detect, DetectorFactory
from pydantic import BaseModel, field_validator
from google import genai
import pandas as pd
import numpy as np

# Set page configuration
st.set_page_config(
    page_title="HeyThatsMyLand - Continuous Monitoring",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize langdetect with seed for reproducible results
DetectorFactory.seed = 0

# Define enums for data validation
class usage_type(enum.Enum):
    RESIDENTIAL = "Residential"
    COMMERCIAL = "Commercial"
    INDUSTRIAL = "Industrial"
    AGRICULTURAL = "Agricultural"
    OTHER = "Other"

class District(enum.Enum):
    AKOLA = "Akola"
    AMRAVATI = "Amravati"
    BULDHANA = "Buldhana"
    YAVATMAL = "Yavatmal"
    WASHIM = "Washim"
    AURANGABAD = "Aurangabad"
    BEED = "Beed"
    JALNA = "Jalna"
    OSMANABAD = "Osmanabad"
    NANDED = "Nanded"
    LATUR = "Latur"
    PARBHANI = "Parbhani"
    HINGOLI = "Hingoli"
    BOMBAY = "Mumbai City / Suburban"
    BOMBAY_SUBURBAN = "Mumbai City / Suburban"
    MUMBAI_CITY = "Mumbai City / Suburban"
    MUMBAI_SUBURBAN = "Mumbai City / Suburban"
    THANE = "Thane"
    PALGHAR = "Palghar"
    RAIGAD = "Raigad"
    RATNAGIRI = "Ratnagiri"
    SINDHUDURG = "Sindhudurg"
    BHANDARA = "Bhandara"
    CHANDRAPUR = "Chandrapur"
    GADCHIROLI = "Gadchiroli"
    GONDIA = "Gondia"
    NAGPUR = "Nagpur"
    WARDHA = "Wardha"
    AHMEDNAGAR = "Ahmednagar"
    DHULE = "Dhule"
    JALGAON = "Jalgaon"
    NANDURBAR = "Nandurbar"
    NASHIK = "Nashik"
    SANGLI = "Sangli"
    SATARA = "Satara"
    SOLAPUR = "Solapur"
    KOLHAPUR = "Kolhapur"
    PUNE = "Pune"
    NA = "n/a"

class City(enum.Enum):
    MUMBAI = "Mumbai"
    PUNE = "Pune"
    NAGPUR = "Nagpur"
    THANE = "Thane"
    PIMPRI_CHINCHWAD = "Pimpri-Chinchwad"
    NASHIK = "Nashik"
    KALYAN_DOMBIVLI = "Kalyan-Dombivli"
    VASAI_VIRAR = "Vasai-Virar"
    AURANGABAD = "Aurangabad"
    NAVI_MUMBAI = "Navi Mumbai"
    SOLAPUR = "Solapur"
    MIRA_BHAYANDAR = "Mira-Bhayandar"
    JALGAON = "Jalgaon"
    DHULE = "Dhule"
    AMRAVATI = "Amravati"
    NANDED_WAGHALA = "Nanded-Waghala"
    KOLHAPUR = "Kolhapur"
    ULHASNAGAR = "Ulhasnagar"
    SANGLI = "Sangli"
    MALEGAON = "Malegaon"
    AKOLA = "Akola"
    LATUR = "Latur"
    BHIWANDI_NIZAMPUR = "Bhiwandi-Nizampur"
    AHMEDNAGAR = "Ahmednagar"
    CHANDRAPUR = "Chandrapur"
    PARBHANI = "Parbhani"
    ICHALKARANJI = "Ichalkaranji"
    JALNA = "Jalna"
    AMBARNATH = "Ambernath"
    BHUSAWAL = "Bhusawal"
    PANVEL = "Panvel"
    BADLAPUR = "Badlapur"
    BOISAR = "Boisar"
    GONDIA = "Gondia"
    SATARA = "Satara"
    BARSHI = "Barshi"
    YAVATMAL = "Yavatmal"
    ACHALPUR = "Achalpur"
    OSMANABAD = "Osmanabad"
    NANDURBAR = "Nandurbar"
    WARDHA = "Wardha"
    UDGIR = "Udgir"
    HINGANGHAT = "Hinganghat"
    NA = "n/a"

# Define Pydantic models for data validation and structure
class Address(BaseModel):
    flat_or_apartment_numbers: str
    office_or_shop_numbers: str
    floor_numbers: str
    building_wing_or_tower_or_number: str
    building_number_on_street: str
    plot_number: str
    bungalow_or_house_number: str
    gut_or_gat_number: str
    survey_or_cs_or_cts_number: str
    building_name: str
    society_or_complex_name: str
    street_or_road_or_marg: str
    sub_locality_or_city_divsion: str
    locality_or_area_or_neighbourhood: str
    village: str
    taluka: str
    district_and_or_sub_district: District
    city: City
    state: str
    pin_code: str

    # Assigns n/a if value is not 1/36 districts
    @field_validator("district_and_or_sub_district", mode="before")
    def validate_district(cls, value):
        for district in District:
            if value.lower() == district.value.lower():
                return district
        return District.NA

    # Assigns n/a if value is not 1/43 cities
    @field_validator("city", mode="before")
    def validate_city(cls, value):
        for city in City:
            if value.lower() == city.value.lower():
                return city
        return City.NA

class PropertyDetails(BaseModel):
    address: Address
    property_usage_type: usage_type
    type_of_property: str
    area: str

class GeneralNoticeInfo(BaseModel):
    date_of_notice_in_DDMMYY_format: str
    num_days_to_respond: int
    ai_generated_50_word_summary: str

class SellerDetails(BaseModel):
    person_name: str
    person_address: str
    company_name: str
    company_address: str

class AdvocateDetails(BaseModel):
    advocate_name: str
    firm_name: str
    advocate_or_firm_phone_number: str
    advocate_or_firm_email: str
    advocate_or_firm_address: str

class PublicNotice(BaseModel):
    property_details: PropertyDetails
    general_notice_info: GeneralNoticeInfo
    seller_details: SellerDetails
    advocate_details: AdvocateDetails

# Function to load the sample database
def load_sample_database():
    sample_db_path = Path(__file__).parent / "data" / "sample_database.json"
    
    # Check if the file exists
    if sample_db_path.exists():
        try:
            with open(sample_db_path, "r") as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading sample database: {e}")
            return {}
    else:
        # If file doesn't exist in the deployed environment, try a relative path
        alternative_path = Path("data") / "sample_database.json"
        if alternative_path.exists():
            try:
                with open(alternative_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                st.error(f"Error loading sample database: {e}")
                return {}
        else:
            # Provide hard-coded sample data as a fallback
            return {
                "sample1.jpg": {
                    "property_details": {
                        "address": {
                            "flat_or_apartment_numbers": "Flat No. 202",
                            "office_or_shop_numbers": "n/a",
                            "floor_numbers": "n/a",
                            "building_wing_or_tower_or_number": "n/a",
                            "building_number_on_street": "n/a",
                            "plot_number": "n/a",
                            "bungalow_or_house_number": "n/a",
                            "gut_or_gat_number": "n/a",
                            "survey_or_cs_or_cts_number": "n/a",
                            "building_name": "Kashi Building",
                            "society_or_complex_name": "Rajasthan Housing Society Limited",
                            "street_or_road_or_marg": "n/a",
                            "sub_locality_or_city_divsion": "J.B. Nagar",
                            "locality_or_area_or_neighbourhood": "Andheri East",
                            "village": "Andheri",
                            "taluka": "n/a",
                            "district_and_or_sub_district": "Mumbai City / Suburban",
                            "city": "Mumbai",
                            "state": "Maharashtra",
                            "pin_code": "n/a"
                        },
                        "property_usage_type": "Residential",
                        "type_of_property": "Flat",
                        "area": "n/a"
                    }
                }
            }

# Function to initialize session state variables
def init_session_state():
    if 'api_key' not in st.session_state:
        st.session_state.api_key = ""
    if 'client' not in st.session_state:
        st.session_state.client = None
    if 'model_id' not in st.session_state:
        st.session_state.model_id = "gemini-2.0-flash"
    if 'processed_data' not in st.session_state:
        # Load sample database by default
        st.session_state.processed_data = load_sample_database()
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    if 'processing_status' not in st.session_state:
        st.session_state.processing_status = None
    if 'current_tab' not in st.session_state:
        st.session_state.current_tab = "Home"
    if 'upload_progress' not in st.session_state:
        st.session_state.upload_progress = 0
    if 'database_initialized' not in st.session_state:
        st.session_state.database_initialized = True

# Function to set up the API client
def setup_client():
    if st.session_state.api_key and not st.session_state.client:
        try:
            st.session_state.client = genai.Client(api_key=st.session_state.api_key)
            return True
        except Exception as e:
            st.error(f"Error setting up the API client: {e}")
            return False
    return bool(st.session_state.client)

# OCR function using Gemini
def conduct_ocr(image_data) -> str:
    if not setup_client():
        st.error("API client not configured. Please check your API key.")
        return "OCR failed"
    
    try:
        image = Image.open(BytesIO(image_data))
        ocr_prompt = """
        Perform OCR to extract all text from this scanned Public Notice in a Maharashtra Newspaper.
        Remove unnecessary whitespace before and after the text, and return the text.
        """
        response = st.session_state.client.models.generate_content(
            model=st.session_state.model_id, 
            contents=[image, ocr_prompt]
        )
        return response.text
    except Exception as e:
        st.error(f"Error conducting OCR: {e}")
        return "OCR failed"

# Language detection and translation
def detect_and_translate(text):
    if not setup_client():
        st.error("API client not configured. Please check your API key.")
        return text
    
    try:
        # Detect the language of the text
        if detect(text) != 'en':
            # Text is not in English; call the translation function
            trans_prompt = f"""
                  I have performed OCR to extract all text from a scanned Public Notice in a
                  Maharashtra Newspaper, it is attached below. It is in Hindi or Marathi , and
                  may use Legalese. Translate it to english maintaining 100% of the meaning.
                  Do not editorialize. Translate exactly as written and return the text.

                  Rules:
                  1. "गृहनिर्माण संस्था मर्यादित लिमिटेडच्या" translates to "Housing Society Limited".

                  {text}
            """
            trans_response = st.session_state.client.models.generate_content(
                model=st.session_state.model_id, 
                contents=[trans_prompt]
            )
            return trans_response.text
        else:
            # Text is already in English; return it as is
            return text
    except Exception as e:
        st.error(f"Error detecting language: {e}")
        return text

# Extract structured data using Gemini
def extract_structured_data(text: str) -> Dict:
    if not setup_client():
        st.error("API client not configured. Please check your API key.")
        return {}
    
    # PROMPT
    prompt = f"""
    A. GOAL:

    I have used OCR to extract text from a Public Notice in a Maharashtra Newspaper, it is in the section "FINAL_EXTRACTED_TEXT" below.
    Acting as an experienced regional real estate lawyer, I need you to extract and parse structured data from the text.
    Note, you must strictly adhere to the specified JSON response schema.

    B. RULES:

    1. Since public notices may contain multiple addresses, here are rules about how to store each address:
        (1-a) Main property address i.e. where the title investigation is occuring will be mentioned - to be stored in "property_details.address" as an Address object.
              If any address components are not clearly and explicitly mentioned, leave it as "n/a" instead of using components of other addresses.
        (1-b) The seller's (person) address if they live elsewhere may be mentioned - to be stored in "seller_details.person_address" as a single string.
        (1-c) The seller's (company) registered office address may be mentioned - to be stored in "seller_details.company_address" as a single string.
        (1-d) The advocate (person or law firm) address will be mentioned - to be stored in "advocate_details.advocate_or_firm_address" as a single string.
        (1-e) Any other address is not to be stored or extracted.
        (1-f) Be extremely careful not to confuse any of the addresses you see in the text.
    2. If a Public Notice includes multiple units (flats, shops, offices, etc.), capture data for all units without fail.
       Some fields in the JSON response apply to each unit individually, while others are common. Carefully analyze the notice to assign values correctly.
       For example, if flats #101 and #201 are listed, "property_details.address.flat_or_apartment_numbers" should be "Flat No. 101, Flat No. 201". If both are in the same building
       "Pitale Prasad," "property_details.address.building_name" should be "Pitale Prasad". Ensure accurate field assignment based on shared or unit-specific details.
    3. The following are examples of local governance bodies, and therefore should be excluded from your parsing - Pune Municipal Corporation, BMC, Gram Panchayats, Nagar Parishad,
       Nagar Palika, Municipality, Zilla Parishad etc.
    4. If pin code IS NOT explicitly mentioned for the Main property i.e. in "property_details.address", but IS mentioned for others (advocate / seller address), do not confuse,
       leave "property_details.address.pin_code" as "n/a".
    5. If you see a pattern like "Plot bearing S. No. 240, H. No. 3,4,5,6,7,8" follow these 2 rules:
        (5-a) The "H. No." refers to Hissa number not House number, and should be placed in "property_details.survey_or_cs_or_cts_number" and not in "property_details.address.bungalow_or_house_number".
        (5-b) The "Plot bearing S. No. 240" refers to a plot number and should be placed in "property_details.address.plot_number".


    C. DESCRIPTIONS OF ADDRESS CLASS PROPERTIES:

    flat_or_apartment_numbers: Identifier(s) of an individual unit within a residential building or area. Can contain multiple values if there are multiple units.
                               (Examples: "Flat No. 202", "2", "Apt. 2a", "3A", "61 A", "C-602", "Flat No. 2 and Flat No. 3", "Flt. 5", "Flat #1, Apt#2")
    office_or_shop_numbers: Identifier(s) of an individual unit within a commercial building or area. Can contain multiple values if there are multiple units.
                            (Examples: "Shop No. 5", "Shop No. 1, 2, 3 & 4; Office No. 102", "Tenement No. 398/49", "Office #101", "Office 12")
    floor_numbers: Identifier(s) of the floor number where the unit(s) are located within a building. Can contain multiple values if there are multiple units.
                            (Examples: "5th floor", "First floor","Ground flr", "Ground", "floor 3")
    building_wing_or_tower_or_number: Identifier of a single building amongst many within a society or building complex. Can contain multiple values if there are multiple units.
                            (Examples: "Tower D", "B-3", "A", "C wing", "2", "Bldg. 5")
    building_number_on_street: Identitifer of a building on a specific street. Can contain multiple values if there are multiple units.
                               (Examples: ["57" from "57, Linking Road"], ["46" from "46, Embassy Apt, LG Marg"], ["9" from "9 Cannaught Rd"], ["FJ-11" from "Building No. FJ-11"])
    plot_number: Identitifer of a residential or industrial plot of land or factory or shed. Can contain multiple values if needed.
                 (Examples: "Final Plot No. 123-B1", "Final Plot Nos. 10", "Plot 5-C", "Plot No:40", "Plot bearing S. No. 185B", "Plot bearing S. No. 120")
    bungalow_or_house_number: Identitifer of a bungalow or house. Do not confuse this with survey numbers. Can contain multiple values if needed.
                 (Examples: "Bungalow 12", "House 819", "House No.331-334-335")
    gut_or_gat_number: It is a unique land identification number assigned by the state's revenue department, usually for rural parcels of land.
                       (Examples: "Gat No. 100", "Gut No. 339")
    survey_or_cs_or_cts_number: It is an umbrella term for a variety of official identifiers of a parcel of land.
                                (Examples: "Survey Number 60/AA", "Old Survey Number 5/121", "New Survey Number 12", "S. No 1A/294", "Svy. No 250 (part)", "C.S. No. 46/1",
                                            "Survey No. 112, Hissa No. 3", "S. No. 112, H. No. 1,2,3,5,8", "Survey No. 121 (Hissa No. 5)", "City Survey No. 1176 (part)",
                                            "Cadastral Survey No. 3", "Chain and Triangulation Survey No. 1A", "C. Survey. No. 2016/57")
    building_name: Name of a residential / commerical / industrial building. Can contain multiple values if needed.
                  (Examples: "Jeevan Niwas", "Prasad", "Lodha Supremus", "Sangita", "Nul Naka Ghar", "Sun-n-Sea", "Vivarea", "Gokul")
    society_or_complex_name:  Name of a residential / commerical / industrial society or complex containing multiple buildings, plots, wings, houses, or offices.
                              (Examples: "Ganjawala CHS Ltd.", "Rajdoot Co-op. Hsng. Soc", "Peninsula Corporate Park", "Sindh Co-operative Housing Society", "Kanjirapole CHS",
                                         "Tarapur M.I.D.C", "Pravin Rita CHSL")
    street_or_road_or_marg: Name or Identifier of a thoroughfare such as a street, road, lane, marg of the property.
                            (Examples: "Laxmibai Jagmohandas Marg", "J.P. Road", "Hughes Rd.", "5th Street", "BMC Street No. 23-23B", "17th Road", "Venus Lane", "Chimbai Ln")
    sub_locality_or_city_divsion: Name of Sub-locality, sub-area, or neighbourhood, or divisions within city limits. Be sure not to confuse this with "locality_or_area_or_neighbourhood".
                                  (Examples: "Versova", "Kala Ghoda", "Pali Hill", "Phase 2", "Bhuleshwar Division", "Malabar Hill Div.")
    locality_or_area_or_neighbourhood: Name of Locality, area, or neighbourhood. Be sure not to confuse this with village name.
                                       (Examples: "Andheri (West)", "Goregaon W", "Shivajinagar", "Worli", "Aundh")
    village: Official name of the village in which the property is located. Must be explicitly mentioned, else leave it as "n/a".
             (Examples: "Village - Chatgaon", "Ranga Reddy Guda Village", "Vil-Somatane", "Vlg Ashti")
    taluka: Official name of the taluka in which the property is located. Must be explicitly mentioned, else leave it as "n/a".
            (Examples: "Taluka - Maval", "Andheri Taluka", "Tal-Akot", "Tlk Chikli")
    district_and_or_sub_district: Official name of the district and/ or sub-district in which the property is located. Must be explicitly mentioned, else leave it as "n/a".
                              (Examples: "District - Amravati", "Pune District", "Dist-Latur", "Registration District and Sub-district Mumbai City & Mumbai Suburban", "Sindhudurg Dist.")
    city: Official name of the city in which the property is located.
          (Examples: "Mumbai", "Pune", "Nagpur", "Nashik", "Aurangabad")
    state: Official name of the state in which the property is located.
           (Examples: "MH", "Maharashtra", "M.H", "Telangana", "Bihar", "GJ", "MP")
    pin_code: 6-digit number representing postal code. Edge case: If 2-digit number found, append "4000" to it (edge case example, if "16" found, pin code is "400016").
              (Example: "400030", "411 007", "16", "400 001")

    D. FINAL_EXTRACTED_TEXT:

    {text}
    """
    
    try:
        # Convert pydantic_model to JSON
        jsonified_pydantic = PublicNotice.model_json_schema()

        # Call on Gemini
        response = st.session_state.client.models.generate_content(
            model=st.session_state.model_id,
            contents=[prompt],
            config={'response_mime_type': 'application/json',
                    'response_schema': jsonified_pydantic}
        )

        # Return the parsed response
        return response.parsed
    except Exception as e:
        st.error(f"Error extracting structured data: {e}")
        return {}

# Process a single file
def process_file(file_data, file_name):
    # Step 1: OCR
    with st.spinner(f"Performing OCR on {file_name}..."):
        ocr_text = conduct_ocr(file_data)
        if ocr_text == "OCR failed":
            return None

    # Step 2: Language Detection & Translation
    with st.spinner(f"Translating text if needed..."):
        executable_text = detect_and_translate(ocr_text)

    # Step 3: Extract structured data
    with st.spinner(f"Extracting structured data..."):
        result_json = extract_structured_data(executable_text)
        
    return result_json

# Search function - Simple search
def simple_search(query: str, data: Dict[str, Any], top_n: int = 3) -> List[str]:
    if not data:
        return []
    
    # Prepare search prompt
    prompt = f"""
    Using the provided JSON dictionary of addresses below and the query below, return only the top {top_n} matching addresses
    (keys only) in JSON format without any additional code.
    
    JSON dictionary of addresses: {json.dumps(data)}.
    
    query: "{query}"
    """
    
    try:
        # Call Gemini for semantic search
        response = st.session_state.client.models.generate_content(
            model=st.session_state.model_id, 
            contents=[prompt]
        )
        
        # Extract the keys from the response
        response_text = response.text
        # This part needs to be improved with proper JSON parsing
        # For now, we'll extract filenames that appear in the response
        matching_keys = []
        for key in data.keys():
            if key in response_text:
                matching_keys.append(key)
                
        # Limit to top_n results
        return matching_keys[:top_n]
    except Exception as e:
        st.error(f"Error performing search: {e}")
        return []

# Advanced search function
def advanced_search(criteria: Dict[str, str], data: Dict[str, Any], top_n: int = 3) -> List[str]:
    if not data:
        return []
    
    # Filter out empty criteria
    filtered_criteria = {k: v for k, v in criteria.items() if v and v != "n/a"}
    
    if not filtered_criteria:
        return []
    
    # Prepare search prompt with detailed criteria
    criteria_str = ", ".join([f"{k}: {v}" for k, v in filtered_criteria.items()])
    
    prompt = f"""
    Using the provided JSON dictionary of addresses below and the search criteria below, 
    return only the top {top_n} matching addresses (keys only) in JSON format without any additional code.
    
    JSON dictionary of addresses: {json.dumps(data)}.
    
    Search criteria: {criteria_str}
    
    Find properties that best match these criteria, giving higher weight to exact matches.
    """
    
    try:
        # Call Gemini for search
        response = st.session_state.client.models.generate_content(
            model=st.session_state.model_id, 
            contents=[prompt]
        )
        
        # Extract the keys from the response
        response_text = response.text
        matching_keys = []
        for key in data.keys():
            if key in response_text:
                matching_keys.append(key)
                
        # Limit to top_n results
        return matching_keys[:top_n]
    except Exception as e:
        st.error(f"Error performing advanced search: {e}")
        return []

# Function to create a formatted display of property details
def display_property_details(property_data, file_name=None):
    if not property_data:
        return
    
    property_details = property_data.get("property_details", {})
    if not property_details:
        return
    
    address = property_details.get("address", {})
    
    # Create expandable sections for property details
    if file_name:
        st.subheader(f"Property from {file_name}")
    
    # Create columns for layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Property Details")
        
        # Property type and usage
        usage_type_value = property_details.get("property_usage_type", "")
        if isinstance(usage_type_value, dict) and "value" in usage_type_value:
            usage_type_value = usage_type_value.get("value", "")
        
        # Display property info
        st.markdown(f"**Type:** {property_details.get('type_of_property', 'N/A')}")
        st.markdown(f"**Usage:** {usage_type_value}")
        st.markdown(f"**Area:** {property_details.get('area', 'N/A')}")
        
        # Display address details
        st.markdown("#### Address")
        
        # Extract district and city values
        district_value = "N/A"
        if isinstance(address.get("district_and_or_sub_district"), dict):
            district_value = address.get("district_and_or_sub_district", {}).get("value", "N/A")
        
        city_value = "N/A"
        if isinstance(address.get("city"), dict):
            city_value = address.get("city", {}).get("value", "N/A")
        
        # Format address components
        address_components = []
        
        # Apartment/shop info
        flat_apt = address.get("flat_or_apartment_numbers", "")
        if flat_apt and flat_apt != "n/a":
            address_components.append(flat_apt)
            
        office_shop = address.get("office_or_shop_numbers", "")
        if office_shop and office_shop != "n/a":
            address_components.append(office_shop)
        
        # Floor
        floor = address.get("floor_numbers", "")
        if floor and floor != "n/a":
            address_components.append(f"{floor} Floor")
        
        # Building info
        bldg_wing = address.get("building_wing_or_tower_or_number", "")
        if bldg_wing and bldg_wing != "n/a":
            address_components.append(f"Wing/Tower {bldg_wing}")
        
        bldg_name = address.get("building_name", "")
        if bldg_name and bldg_name != "n/a":
            address_components.append(bldg_name)
        
        society = address.get("society_or_complex_name", "")
        if society and society != "n/a":
            address_components.append(society)
        
        # Street and locality
        street = address.get("street_or_road_or_marg", "")
        if street and street != "n/a":
            address_components.append(street)
        
        bldg_num = address.get("building_number_on_street", "")
        if bldg_num and bldg_num != "n/a":
            address_components.append(f"Building No. {bldg_num}")
        
        locality = address.get("locality_or_area_or_neighbourhood", "")
        if locality and locality != "n/a":
            address_components.append(locality)
        
        sub_locality = address.get("sub_locality_or_city_divsion", "")
        if sub_locality and sub_locality != "n/a":
            address_components.append(sub_locality)
        
        # Village and administrative divisions
        village = address.get("village", "")
        if village and village != "n/a":
            address_components.append(f"Village: {village}")
        
        taluka = address.get("taluka", "")
        if taluka and taluka != "n/a":
            address_components.append(f"Taluka: {taluka}")
        
        if district_value and district_value != "n/a":
            address_components.append(f"District: {district_value}")
        
        if city_value and city_value != "n/a":
            address_components.append(city_value)
        
        state = address.get("state", "")
        if state and state != "n/a":
            address_components.append(state)
        
        pin_code = address.get("pin_code", "")
        if pin_code and pin_code != "n/a":
            address_components.append(pin_code)
        
        # Display complete address
        st.markdown(f"**Complete Address:** {', '.join(address_components)}")
        
        # Display survey details
        survey_num = address.get("survey_or_cs_or_cts_number", "")
        plot_num = address.get("plot_number", "")
        gat_num = address.get("gut_or_gat_number", "")
        
        if survey_num and survey_num != "n/a":
            st.markdown(f"**Survey/CTS Number:** {survey_num}")
        
        if plot_num and plot_num != "n/a":
            st.markdown(f"**Plot Number:** {plot_num}")
        
        if gat_num and gat_num != "n/a":
            st.markdown(f"**Gut/Gat Number:** {gat_num}")
    
    with col2:
        # Display seller and advocate information
        seller_details = property_data.get("seller_details", {})
        advocate_details = property_data.get("advocate_details", {})
        notice_info = property_data.get("general_notice_info", {})
        
        # Seller information
        st.markdown("#### Seller Details")
        
        seller_person = seller_details.get("person_name", "")
        seller_company = seller_details.get("company_name", "")
        
        if seller_person and seller_person != "n/a":
            st.markdown(f"**Person:** {seller_person}")
        
        if seller_company and seller_company != "n/a":
            st.markdown(f"**Company:** {seller_company}")
        
        seller_person_addr = seller_details.get("person_address", "")
        if seller_person_addr and seller_person_addr != "n/a":
            st.markdown(f"**Person Address:** {seller_person_addr}")
        
        seller_company_addr = seller_details.get("company_address", "")
        if seller_company_addr and seller_company_addr != "n/a":
            st.markdown(f"**Company Address:** {seller_company_addr}")
        
        # Advocate information
        st.markdown("#### Advocate Details")
        
        advocate_name = advocate_details.get("advocate_name", "")
        firm_name = advocate_details.get("firm_name", "")
        
        if advocate_name and advocate_name != "n/a":
            st.markdown(f"**Advocate:** {advocate_name}")
        
        if firm_name and firm_name != "n/a":
            st.markdown(f"**Firm:** {firm_name}")
        
        advocate_addr = advocate_details.get("advocate_or_firm_address", "")
        if advocate_addr and advocate_addr != "n/a":
            st.markdown(f"**Address:** {advocate_addr}")
        
        advocate_phone = advocate_details.get("advocate_or_firm_phone_number", "")
        if advocate_phone and advocate_phone != "n/a":
            st.markdown(f"**Phone:** {advocate_phone}")
        
        advocate_email = advocate_details.get("advocate_or_firm_email", "")
        if advocate_email and advocate_email != "n/a":
            st.markdown(f"**Email:** {advocate_email}")
        
        # Notice information
        st.markdown("#### Notice Information")
        
        notice_date = notice_info.get("date_of_notice_in_DDMMYY_format", "")
        if notice_date and notice_date != "n/a":
            st.markdown(f"**Date:** {notice_date}")
        
        days_to_respond = notice_info.get("num_days_to_respond", "")
        if days_to_respond:
            st.markdown(f"**Days to Respond:** {days_to_respond}")
        
        notice_summary = notice_info.get("ai_generated_50_word_summary", "")
        if notice_summary and notice_summary != "n/a":
            st.markdown(f"**Summary:** {notice_summary}")

# Function to save data to file
def save_data_to_file():
    data_to_save = st.session_state.processed_data
    if not data_to_save:
        st.warning("No data to save.")
        return
    
    # Convert the data to JSON format
    try:
        # Handle complex objects like enums by converting to dict first
        serializable_data = {}
        for key, value in data_to_save.items():
            serializable_data[key] = json.loads(json.dumps(value, default=lambda o: o.dict() if hasattr(o, 'dict') else str(o)))
        
        json_str = json.dumps(serializable_data, indent=4)
        
        # Create a downloadable link
        st.download_button(
            label="Download Data as JSON",
            data=json_str,
            file_name="property_database.json",
            mime="application/json"
        )
    except Exception as e:
        st.error(f"Error saving data: {e}")

# Function to load data from file
def load_data_from_file(uploaded_file):
    if uploaded_file is not None:
        try:
            # Read the file content
            content = uploaded_file.read()
            decoded_content = content.decode('utf-8')
            
            # Parse the JSON content
            loaded_data = json.loads(decoded_content)
            
            # Update session state
            st.session_state.processed_data = loaded_data
            st.success(f"Successfully loaded database with {len(loaded_data)} properties.")
        except Exception as e:
            st.error(f"Error loading data: {e}")

# Main app function
def main():
    # Initialize session state
    init_session_state()
    
    # Sidebar for navigation and configuration
    with st.sidebar:
        st.title("HeyThatsMyLand")
        st.subheader("Continuous Monitoring v1.0")
        
        # API key input
        api_key = st.text_input("Google Gemini API Key", 
                               value=st.session_state.api_key, 
                               type="password",
                               help="Enter your Google Gemini API Key here")
        
        if api_key != st.session_state.api_key:
            st.session_state.api_key = api_key
            st.session_state.client = None
            
        # Navigation
        st.subheader("Navigation")
        tabs = ["Home", "Upload & Process", "Search", "Database"]
        selected_tab = st.radio("Go to", tabs, index=tabs.index(st.session_state.current_tab))
        
        if selected_tab != st.session_state.current_tab:
            st.session_state.current_tab = selected_tab
        
        # Display app information
        st.markdown("---")
        st.caption("Developed by Vedant Nevatia & Pranav Jain")
        st.caption("© 2025 HeyThatsMyLand")
    
    # Main content area
    if st.session_state.current_tab == "Home":
        st.title("Welcome to CoMo - Continuous Monitoring")
        st.markdown("""
        This application helps you extract, process, and search property information from public notices in Maharashtra newspapers.
        
        ### Features
        - **Extract data** from scanned public notice images
        - **Process and store** property details in a searchable database
        - **Search properties** by address or specific criteria
        - **View and manage** your property database
        
        ### Getting Started
        1. Enter your Google Gemini API Key in the sidebar
        2. Navigate to "Upload & Process" to process notice images
        3. Use "Search" to find properties in your database
        4. Manage your database in the "Database" section
        
        ### Requirements
        - Google Gemini API Key
        - Public notice images in JPG/PNG format
        """)
        
        # Display sample database info
        if st.session_state.processed_data:
            sample_count = len(st.session_state.processed_data)
            st.success(f"✅ Application is pre-loaded with {sample_count} sample properties. You can search these immediately!")
        
        # Check if API is configured
        if st.session_state.api_key:
            if setup_client():
                st.success("✅ API client is configured. You're ready to use the application.")
            else:
                st.error("❌ API client configuration failed. Please check your API key.")
        else:
            st.warning("⚠️ Please enter your Google Gemini API Key in the sidebar to get started.")
    
    elif st.session_state.current_tab == "Upload & Process":
        st.title("Upload & Process Public Notices")
        
        # Check if API is set up
        if not setup_client():
            st.warning("Please configure your Google Gemini API Key in the sidebar first.")
            return
        
        # File uploader
        uploaded_files = st.file_uploader("Upload public notice images", 
                                         type=["jpg", "jpeg", "png"], 
                                         accept_multiple_files=True)
        
        if uploaded_files:
            # Display a process button
            process_button = st.button("Process Selected Files")
            
            if process_button:
                # Create a progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Process each file
                total_files = len(uploaded_files)
                processed_count = 0
                
                for uploaded_file in uploaded_files:
                    # Update status
                    file_name = uploaded_file.name
                    status_text.text(f"Processing {file_name}... ({processed_count+1}/{total_files})")
                    
                    # Read file data
                    file_data = uploaded_file.read()
                    
                    # Process the file
                    result = process_file(file_data, file_name)
                    
                    if result:
                        # Store the result
                        st.session_state.processed_data[file_name] = result
                        st.success(f"Successfully processed {file_name}")
                    else:
                        st.error(f"Failed to process {file_name}")
                    
                    # Update progress
                    processed_count += 1
                    progress_bar.progress(processed_count / total_files)
                
                # Final status update
                status_text.text(f"Processed {processed_count} out of {total_files} files")
                
                # Option to save the processed data
                if processed_count > 0:
                    st.subheader("Save Processed Data")
                    save_data_to_file()
                    
                    # Show a sample of processed data
                    if st.session_state.processed_data:
                        st.subheader("Sample Processed Data")
                        sample_key = list(st.session_state.processed_data.keys())[0]
                        display_property_details(st.session_state.processed_data[sample_key], sample_key)
        
        # Option to process text directly
        st.markdown("---")
        st.subheader("Or Process Notice Text Directly")
        
        with st.expander("Enter Public Notice Text"):
            notice_text = st.text_area("Paste the text of a public notice here", height=300)
            text_name = st.text_input("Give this notice a name (for database reference)")
            
            if st.button("Process Text") and notice_text and text_name:
                if not text_name.endswith(".txt"):
                    text_name = f"{text_name}.txt"
                
                with st.spinner("Processing text..."):
                    # Skip OCR and translation, go straight to structured data extraction
                    result = extract_structured_data(notice_text)
                    
                    if result:
                        # Store the result
                        st.session_state.processed_data[text_name] = result
                        st.success(f"Successfully processed text as {text_name}")
                        
                        # Display the processed data
                        display_property_details(result, text_name)
                        
                        # Option to save
                        save_data_to_file()
                    else:
                        st.error("Failed to process the text")
    
    elif st.session_state.current_tab == "Search":
        st.title("Search Property Database")
        
        # Check if there's data to search
        if not st.session_state.processed_data:
            st.warning("Your property database is empty. Please process some public notices first or load an existing database.")
            
            # Option to load a database
            st.subheader("Load Database")
            uploaded_db = st.file_uploader("Upload a property database JSON file", type=["json"])
            if uploaded_db:
                load_data_from_file(uploaded_db)
            
            return
        
        # Display search options
        st.subheader("Search Options")
        search_tabs = st.tabs(["Simple Search", "Advanced Search"])
        
        with search_tabs[0]:
            # Simple search
            st.markdown("Enter an address or property description to find matching properties.")
            search_query = st.text_input("Search Query", placeholder="e.g., Flat 202, Khar West, Mumbai")
            
            if st.button("Search", key="simple_search_button"):
                if search_query:
                    with st.spinner("Searching..."):
                        results = simple_search(search_query, st.session_state.processed_data)
                        
                        if results:
                            st.session_state.search_results = results
                            st.success(f"Found {len(results)} matching properties")
                        else:
                            st.info("No matching properties found")
                else:
                    st.warning("Please enter a search query")
        
        with search_tabs[1]:
            # Advanced search
            st.markdown("Search by specific property attributes")
            
            # Create columns for layout
            col1, col2 = st.columns(2)
            
            with col1:
                # First column fields
                flat_apt = st.text_input("Flat/Apartment Number", placeholder="e.g., Flat No. 202")
                office_shop = st.text_input("Office/Shop Number", placeholder="e.g., Shop No. 5")
                building_name = st.text_input("Building Name", placeholder="e.g., Rajdoot")
                society_name = st.text_input("Society/Complex Name", placeholder="e.g., Rajdoot Co-op Housing Society")
                street = st.text_input("Street/Road", placeholder="e.g., Linking Road")
                
            with col2:
                # Second column fields
                locality = st.text_input("Locality/Area", placeholder="e.g., Khar West")
                city_input = st.text_input("City", placeholder="e.g., Mumbai")
                pin_code = st.text_input("PIN Code", placeholder="e.g., 400052")
                property_type = st.text_input("Property Type", placeholder="e.g., Flat, Shop, Land")
                survey_number = st.text_input("Survey/CTS Number", placeholder="e.g., CTS No. E/525")
            
            # Construct search criteria
            search_criteria = {
                "flat_or_apartment_numbers": flat_apt,
                "office_or_shop_numbers": office_shop,
                "building_name": building_name,
                "society_or_complex_name": society_name,
                "street_or_road_or_marg": street,
                "locality_or_area_or_neighbourhood": locality,
                "city": city_input,
                "pin_code": pin_code,
                "type_of_property": property_type,
                "survey_or_cs_or_cts_number": survey_number
            }
            
            if st.button("Search", key="advanced_search_button"):
                # Check if at least one field is filled
                if any(value for value in search_criteria.values()):
                    with st.spinner("Searching..."):
                        results = advanced_search(search_criteria, st.session_state.processed_data)
                        
                        if results:
                            st.session_state.search_results = results
                            st.success(f"Found {len(results)} matching properties")
                        else:
                            st.info("No matching properties found")
                else:
                    st.warning("Please enter at least one search criterion")
        
        # Display search results
        if st.session_state.search_results:
            st.markdown("---")
            st.subheader("Search Results")
            
            for idx, result_key in enumerate(st.session_state.search_results):
                with st.expander(f"Result {idx+1}: {result_key}"):
                    display_property_details(st.session_state.processed_data[result_key], result_key)
    
    elif st.session_state.current_tab == "Database":
        st.title("Property Database Management")
        
        # Database statistics
        if st.session_state.processed_data:
            num_properties = len(st.session_state.processed_data)
            st.subheader(f"Database Statistics")
            st.info(f"Total Properties: {num_properties}")
            
            # Option to save the database
            st.subheader("Save Database")
            save_data_to_file()
            
            # Option to reset to sample database
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Reset to Sample Database", help="Restore the original sample database"):
                    st.session_state.processed_data = load_sample_database()
                    st.success("Database reset to sample data")
                    st.experimental_rerun()
            
            with col2:
                # Option to clear the database
                if st.button("Clear Database", type="primary", help="Warning: This will delete all property data"):
                    st.session_state.processed_data = {}
                    st.success("Database cleared successfully")
                    st.experimental_rerun()
            
            # Display all properties
            st.subheader("All Properties")
            for property_key in st.session_state.processed_data.keys():
                with st.expander(property_key):
                    display_property_details(st.session_state.processed_data[property_key], property_key)
                    
                    # Option to delete individual property
                    if st.button(f"Delete {property_key}", key=f"delete_{property_key}"):
                        del st.session_state.processed_data[property_key]
                        st.success(f"Deleted {property_key}")
                        st.experimental_rerun()
        else:
            st.warning("Your property database is empty. Please process some public notices first or load an existing database.")
        
        # Option to load a database
        st.subheader("Load Database")
        uploaded_db = st.file_uploader("Upload a property database JSON file", type=["json"])
        if uploaded_db:
            load_data_from_file(uploaded_db)

# Run the app
if __name__ == "__main__":
    main()