import streamlit as st
from pymongo import MongoClient
from datetime import datetime, UTC, timedelta
from google import genai
import urllib.parse

encoded_username = st.secrets.mongodb.username
encoded_password = urllib.parse.quote_plus(st.secrets.mongodb.password)
MONGO_URI = f"mongodb+srv://{encoded_username}:{encoded_password}@devcluster.29wvn4b.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient(MONGO_URI)

db = client["mysteries"]  # Database name
collection = db["mystery"]  # Collection name

# Gemini API Prompt
prompt = """
Generate a unique detective mystery puzzle in the style of Sherlock Holmes or Agatha Christie.  
The mystery should include:
- A crime or unusual event.
- A list of clues that hint at the answer.
- A question prompting the user to solve it.
- A hidden yet logical solution.

Format:
**Mystery:** [Story of the mystery]
**Question:** [What needs to be solved?]
**Clues:** [List 3-5 subtle clues]
**Answer:** [Logical explanation of the solution]
"""

def generate_mystery():
    """Generate a new mystery using Gemini AI."""
    genai_client = genai.Client(api_key=st.secrets.gemini.api_key)
    response = genai_client.models.generate_content(model='gemini-2.0-flash', contents=prompt)

    if response:
        mystery_text = response.text.split('Answer:')
        return {
            "date": datetime.now(UTC).strftime("%Y-%m-%d"),  # Updated to use timezone-aware datetime
            "mystery": mystery_text[0].strip(),
            "answer": mystery_text[1].strip() if len(mystery_text) > 1 else "No answer provided."
        }
    return None

def get_daily_mystery():
    """Check if today's mystery exists in MongoDB; if not, generate and save it."""
    today = datetime.now(UTC).strftime("%Y-%m-%d")  # Updated to use timezone-aware datetime
    existing_mystery = collection.find_one({"date": today})

    if existing_mystery:
        return existing_mystery  # Return the stored mystery

    new_mystery = generate_mystery()
    if new_mystery:
        collection.insert_one(new_mystery)  # Save new mystery to the database
        return new_mystery
    return None

def get_weekly_mysteries():
    """Retrieve mysteries from the last 7 days."""
    end_date = datetime.now(UTC)
    start_date = end_date - timedelta(days=7)
    
    # Convert dates to string format used in database
    end_date_str = end_date.strftime("%Y-%m-%d")
    start_date_str = start_date.strftime("%Y-%m-%d")
    
    # Query for mysteries within date range
    weekly_mysteries = list(collection.find({
        "date": {
            "$gte": start_date_str,
            "$lte": end_date_str
        }
    }).sort("date", -1))  # Sort by date descending
    
    return weekly_mysteries

def toggle_answer():
    """Toggle answer visibility."""
    if 'answerVisible' not in st.session_state:
        st.session_state.answerVisible = {}
    mystery_id = st.session_state.get('current_mystery_id', 'daily')
    st.session_state.answerVisible[mystery_id] = not st.session_state.answerVisible.get(mystery_id, False)

def main():
    st.markdown("""
        <style>
            div[data-testid="stToolbar"] {
                display: none;
            }
            header[data-testid="stHeader"] {
                display: none;
            }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("📅 Daily Mystery Challenge")
    
    # Initialize session state variables
    if 'mystery' not in st.session_state:
        st.session_state.mystery = get_daily_mystery()
    if 'answerVisible' not in st.session_state:
        st.session_state.answerVisible = {}
    if 'view_mode' not in st.session_state:
        st.session_state.view_mode = "daily"

    # Add view selector
    view_mode = st.radio("Select View", ["Today's Mystery", "This Week's Mysteries"], 
                        horizontal=True,
                        key="view_selector")
    
    st.session_state.view_mode = "daily" if view_mode == "Today's Mystery" else "weekly"
    
    if st.session_state.view_mode == "daily":
        if not st.session_state.mystery:
            st.error("Failed to retrieve or generate a mystery. Try again later.")
            return

        st.session_state.current_mystery_id = 'daily'
        # Display the mystery
        st.write(f"{st.session_state.mystery['mystery']}")

        # Toggle answer button for daily view
        st.button(
            'Show Answer' if not st.session_state.answerVisible.get('daily', False) 
            else 'Hide Answer',
            on_click=toggle_answer,
            key='daily_toggle'
        )

        # Show or hide answer for daily view
        if st.session_state.answerVisible.get('daily', False):
            st.write(f"**Answer:** {st.session_state.mystery['answer']}")

    else:  # Weekly view
        weekly_mysteries = get_weekly_mysteries()
        
        if not weekly_mysteries:
            st.warning("No mysteries found for the past week.")
            return
            
        for idx, mystery in enumerate(weekly_mysteries):
            mystery_id = str(mystery['_id'])
            st.session_state.current_mystery_id = mystery_id
            
            with st.expander(f"Mystery for {mystery['date']}", expanded=(idx == 0)):
                st.write(mystery['mystery'])
                
                # Toggle answer button for each mystery
                st.button(
                    'Show Answer' if not st.session_state.answerVisible.get(mystery_id, False) 
                    else 'Hide Answer',
                    on_click=toggle_answer,
                    key=f'toggle_{mystery_id}'
                )
                
                if st.session_state.answerVisible.get(mystery_id, False):
                    st.write(f"**Answer:** {mystery['answer']}")

main()
