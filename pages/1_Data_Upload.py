import streamlit as st
import pandas as pd
import numpy as np
import os
import io
import json
import base64
import ast
from utils import fetch_internal_api_data, get_csv_download_link, get_json_download_link

# Page configuration
st.set_page_config(
    page_title="Data Upload - Review Aspect Analyzer",
    page_icon="📤",
    layout="wide"
)

# App title and description
st.title("Data Upload")
st.markdown("""
Upload your review data to start the analysis. You can upload a CSV file directly,
import from our internal API, or send data programmatically via our API.
""")

# Create tabs for different upload methods
tabs = st.tabs(["CSV Upload", "Import from API", "API Integration"])

# Tab 1: CSV Upload
with tabs[0]:
    st.header("Upload CSV File")
    
    # Instructions
    st.markdown("""
    ### CSV Format Requirements
    Your CSV file should include the following columns:
    - `review_id`: Unique identifier for each review
    - `review_text`: The full text of the review
    - `category`: Product/service category the review belongs to
    - `aspects`: Comma-separated list of aspects mentioned in the review
    
    Example row: `101,Great product with excellent battery life,Electronics,battery,price,design`
    """)
    
    # Use example data option
    if st.checkbox("Use example data instead"):
        st.markdown("Using example data with pre-defined reviews and aspects.")
        from utils import generate_example_csv
        example_data = generate_example_csv()
        
        # Create a download link for the example data
        st.download_button(
            label="Download Example CSV",
            data=example_data.getvalue(),
            file_name="example_reviews.csv",
            mime="text/csv"
        )
        
        # Process the example data
        example_data.seek(0)  # Reset position to start of stream
        df = pd.read_csv(example_data)
        
        st.success("✅ Example data loaded successfully!")
        
        # Display data
        st.subheader("Data Preview")
        st.dataframe(df.head())
        
        # Process aspects
        if 'aspects' in df.columns:
            df['aspects_list'] = df['aspects'].str.split(',')
        
        # Option to save to session state for analysis
        if st.button("Use Example Data for Analysis"):
            st.session_state['uploaded_data'] = df
            st.success("✅ Example data saved for analysis!")
            
            # Set redirection in session state
            if 'redirect_to' not in st.session_state:
                st.session_state['redirect_to'] = '/Analytics_Charts'
            
            # Auto-navigation
            st.info("You will be automatically redirected to the Analytics page.")
            st.markdown("<meta http-equiv='refresh' content='2; url=/Analytics_Charts'>", unsafe_allow_html=True)
            st.markdown("[Click here if not redirected](/Analytics_Charts)")
    
    else:
        # File uploader
        uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])
        
        if uploaded_file is not None:
            # Process the uploaded file
            from utils import process_csv
            df = process_csv(uploaded_file)
            
            if df is None:
                st.error("Failed to process the uploaded file. Please ensure it follows the required format.")
            else:
                st.success("✅ File uploaded and processed successfully!")
                
                # Display data preview
                st.subheader("Data Preview")
                st.dataframe(df.head())
                
                # Display raw data sample with expander
                with st.expander("View Raw Data Sample"):
                    st.dataframe(df.head(10))
                
                # Option to save to session state for analysis
                if st.button("Use This Data for Analysis"):
                    st.session_state['uploaded_data'] = df
                    st.success("✅ Data saved for analysis!")
                    
                    # Set redirection in session state
                    if 'redirect_to' not in st.session_state:
                        st.session_state['redirect_to'] = '/Analytics_Charts'
                    
                    # Auto-navigation button
                    st.info("You will be automatically redirected to the Analytics page.")
                    st.markdown("<meta http-equiv='refresh' content='2; url=/Analytics_Charts'>", unsafe_allow_html=True)
                    st.markdown("[Click here if not redirected](/Analytics_Charts)")

# Tab 2: Import from API
with tabs[1]:
    st.header("Import from APIs")
    
    # API selection dropdown
    api_selection = st.selectbox(
        "Select API Source",
        [
            "Review Categories API (Perigon)", 
            "Custom Categories API (Upload)",
            "Review Data API (Coming Soon)"
        ]
    )
    
    # Show different content based on API selection
    if api_selection == "Review Categories API (Perigon)":
        # Expand section about the API
        with st.expander("About the Perigon Categories API"):
            st.markdown("""
            ### Perigon Review Categories API
            
            This app can connect to your internal API endpoint at:
            ```
            https://api.perigon.io/v1/internal/ca/reviewCategory/
            ```
            
            **Authentication**:
            - Uses the SHARED_SECRET as a query parameter
            
            **Pagination Parameters**:
            - page (default: 0) - The page number to retrieve
            - size (default: 20) - Number of items per page
            - sortBy (default: "id") - Field to sort by
            - sortOrder (default: "asc") - Sort order
            
            **Response Structure**:
            ```json
            {
              "total": 123,  // Total number of records
              "data": [      // Array of CAReviewCategoryDto objects
                {
                  "id": 1,
                  "name": "Category Name",
                  "createdAt": "2023-01-01T12:00:00Z",
                  "updatedAt": "2023-01-02T12:00:00Z",
                  "caCategoryId": "cat123",
                  "rulesPath": "/path/to/rules",
                  "aspects": [
                    {"name": "Aspect 1"},
                    {"name": "Aspect 2"}
                  ]
                },
                // more categories...
              ]
            }
            ```
            """)
        
        # API fetch options
        col1, col2 = st.columns(2)
        with col1:
            sort_by = st.selectbox(
                "Sort by field", 
                options=["id", "name", "createdAt", "updatedAt"],
                index=0
            )
        with col2:
            sort_order = st.selectbox(
                "Sort order", 
                options=["asc", "desc"],
                index=0
            )
        
        # Button to fetch data
        if st.button("Fetch Categories from Perigon API"):
            with st.spinner("Fetching data from Perigon API..."):
                # Fetch categories from the API
                categories = fetch_internal_api_data(
                    sort_by=sort_by,
                    sort_order=sort_order
                )
                
                if isinstance(categories, dict) and "error" in categories:
                    st.error(f"Error fetching categories: {categories['error']}")
                    if "details" in categories:
                        st.error(f"Details: {categories['details']}")
                else:
                    # Successfully fetched categories
                    st.success(f"Successfully fetched {len(categories)} categories from the API")
                    
                    # Convert to DataFrame for easier handling
                    categories_df = pd.DataFrame(categories)
                    
                    # Save the data to file for later use (cached)
                    if not categories_df.empty:
                        # Create directory if it doesn't exist
                        os.makedirs("example_data", exist_ok=True)
                        
                        # Save to file
                        categories_df.to_csv("example_data/review_categories.csv", index=False)
                        st.success("✅ Saved categories data to file for analytics")
                        
                        # Show a preview of the data
                        st.subheader("Category Data Preview")
                        st.dataframe(categories_df)
                        
                        # Store in session state for immediate use
                        st.session_state['category_data'] = categories_df
                        
                        # Set redirection in session state
                        if 'redirect_to' not in st.session_state:
                            st.session_state['redirect_to'] = '/Category_Analysis'
                        
                        # Auto-navigation
                        st.info("You will be automatically redirected to the Category Analysis page.")
                        st.markdown("<meta http-equiv='refresh' content='2; url=/Category_Analysis'>", unsafe_allow_html=True)
                        st.markdown("[Click here if not redirected](/Category_Analysis)")
    
    elif api_selection == "Custom Categories API (Upload)":
        st.subheader("Upload Categories CSV/JSON File")
        st.markdown("""
        Upload your own category data in CSV or JSON format. The file should have the following columns:
        - id: Unique identifier for the category
        - name: Category name
        - aspectsCount: Number of aspects in the category
        - aspects: List of aspects (as a string representation of an array)
        """)
        
        # File uploader
        uploaded_file = st.file_uploader("Choose a CSV or JSON file", type=["csv", "json"])
        
        if uploaded_file is not None:
            try:
                # Check file type and process accordingly
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                    file_type = "CSV"
                else:
                    df = pd.read_json(uploaded_file)
                    file_type = "JSON"
                
                # Display success message
                st.success(f"✅ Successfully loaded {file_type} file: {uploaded_file.name}")
                
                # Process aspects column if it exists
                if 'aspects' in df.columns:
                    try:
                        df['aspects_parsed'] = df['aspects'].apply(
                            lambda x: json.loads(x) if isinstance(x, str) and x.strip() else []
                        )
                    except:
                        # Try with ast literal eval as fallback
                        import ast
                        df['aspects_parsed'] = df['aspects'].apply(
                            lambda x: ast.literal_eval(x) if isinstance(x, str) and x.strip() else []
                        )
                
                # Save to file
                os.makedirs("example_data", exist_ok=True)
                filename = f"custom_categories_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
                df.to_csv(f"example_data/{filename}", index=False)
                
                # Show data preview
                st.subheader("Data Preview")
                st.dataframe(df.head(10))
                
                # Store in session state
                st.session_state['category_data'] = df
                
                # Auto navigation
                st.success("Categories data saved successfully. Redirecting to analysis...")
                st.markdown("<meta http-equiv='refresh' content='2; url=/Category_Analysis'>", unsafe_allow_html=True)
                st.markdown("[Click here if not redirected](/Category_Analysis)")
                
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
                st.info("Please ensure your file is in the correct format.")
    
    else:  # Coming Soon option
        st.info("This API source is coming soon. Please check back later.")

# Tab 3: API Integration
with tabs[2]:
    st.header("API Integration")
    
    st.markdown("""
    ### Upload data programmatically via our API
    
    You can send data to this application programmatically using our REST API. 
    This allows you to integrate with your existing systems and automate data analysis.
    
    **Base URL**: `http://localhost:5001`
    
    #### Upload CSV data via API:
    
    ```bash
    curl -X POST -H "X-API-Key: YOUR_API_KEY" \\
         -F "file=@your_file.csv" \\
         http://localhost:5001/api/upload
    ```
    
    #### API Endpoints
    
    | Method | Endpoint | Description |
    |--------|----------|-------------|
    | POST | `/api/upload` | Upload review data (CSV) |
    | POST | `/api/upload/review_categories/csv` | Upload category data (CSV) |
    | POST | `/api/upload/review_categories/json` | Upload category data (JSON) |
    | GET | `/api/analytics/categories` | Get category analytics |
    | GET | `/api/analytics/reviews` | Get review analytics |
    
    #### Authentication
    All API requests require the `X-API-Key` header. Contact the administrator to get your API key.
    """)
    
    # Show API Key (for demo purposes)
    st.warning("For demonstration purposes, your API key is: 8d84126c-4184-4c1f-a7f1-efd247bee990")
    
    # Add some example code
    with st.expander("Python Example Code"):
        st.code("""
import requests

# API configuration
api_key = "YOUR_API_KEY"
base_url = "http://localhost:5001"

# Upload a CSV file
def upload_csv(file_path):
    headers = {
        "X-API-Key": api_key
    }
    
    with open(file_path, 'rb') as f:
        files = {
            'file': (file_path, f, 'text/csv')
        }
        
        response = requests.post(
            f"{base_url}/api/upload",
            headers=headers,
            files=files
        )
        
    return response.json()

# Get analytics
def get_analytics():
    headers = {
        "X-API-Key": api_key
    }
    
    response = requests.get(
        f"{base_url}/api/analytics/reviews",
        headers=headers
    )
    
    return response.json()

# Example usage
csv_path = "reviews.csv"
result = upload_csv(csv_path)
print(result)

analytics = get_analytics()
print(analytics)
        """, language="python")
    
    with st.expander("JavaScript Example Code"):
        st.code("""
// Using fetch API in JavaScript
const apiKey = "YOUR_API_KEY";
const baseUrl = "http://localhost:5001";

// Upload a CSV file
async function uploadCSV(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${baseUrl}/api/upload`, {
        method: 'POST',
        headers: {
            'X-API-Key': apiKey
        },
        body: formData
    });
    
    return response.json();
}

// Get analytics
async function getAnalytics() {
    const response = await fetch(`${baseUrl}/api/analytics/reviews`, {
        method: 'GET',
        headers: {
            'X-API-Key': apiKey
        }
    });
    
    return response.json();
}

// Example usage (in an async function)
async function example() {
    const fileInput = document.querySelector('input[type="file"]');
    const file = fileInput.files[0];
    
    const uploadResult = await uploadCSV(file);
    console.log(uploadResult);
    
    const analytics = await getAnalytics();
    console.log(analytics);
}
        """, language="javascript")

# Footer
st.markdown("---")
st.caption("Review Aspect Analyzer Tool - Data Upload")