import streamlit as st
import streamlit.components.v1 as components
from pymongo import MongoClient
from datetime import datetime, UTC, timedelta
from google import genai
import urllib.parse
from streamlit.runtime.caching import cache_data
import pytz

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

def get_user_timezone():
    """Get user's local timezone."""
    if 'timezone' not in st.session_state:
        # Default to UTC if timezone not set
        st.session_state.timezone = pytz.UTC
        
        # Create an invisible component for timezone detection with zero layout impact
        components.html(
            """
            <script>
                (() => {
                    const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
                    window.parent.postMessage({tzinfo: timezone}, '*');
                })();
            </script>
            """,
            height=0,
            width=0
        )
            
    return st.session_state.timezone

def convert_to_local_date(utc_date_str):
    """Convert UTC date string to local date string."""
    utc_date = datetime.strptime(utc_date_str, "%Y-%m-%d")
    local_date = utc_date.replace(tzinfo=pytz.UTC).astimezone(get_user_timezone())
    return local_date.strftime("%Y-%m-%d")

@cache_data
def get_daily_mystery():
    """Check if today's mystery exists in MongoDB; if not, generate and save it."""
    # Get UTC date for database query
    utc_today = datetime.now(UTC).strftime("%Y-%m-%d")
    existing_mystery = collection.find_one({"date": utc_today})

    if existing_mystery:
        # Convert date to local timezone for display
        existing_mystery['display_date'] = convert_to_local_date(existing_mystery['date'])
        return existing_mystery

    new_mystery = generate_mystery()
    if new_mystery:
        collection.insert_one(new_mystery)
        new_mystery['display_date'] = convert_to_local_date(new_mystery['date'])
        return new_mystery
    return None

@cache_data
def get_weekly_mysteries():
    """Retrieve mysteries from the last 7 days."""
    end_date = datetime.now(UTC)
    start_date = end_date - timedelta(days=7)
    
    end_date_str = end_date.strftime("%Y-%m-%d")
    start_date_str = start_date.strftime("%Y-%m-%d")
    
    weekly_mysteries = list(collection.find({
        "date": {
            "$gte": start_date_str,
            "$lte": end_date_str
        }
    }).sort("date", -1))
    
    # Convert dates to local timezone for display
    for mystery in weekly_mysteries:
        mystery['display_date'] = convert_to_local_date(mystery['date'])
    
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
            .current-date {
                position: fixed;
                top: 10px;
                right: 10px;
                padding: 5px 10px;
                background-color: #f0f2f6;
                border-radius: 5px;
                font-size: 0.9em;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # Display current date in local timezone
    local_now = datetime.now(get_user_timezone())
    st.markdown(
        f'<div class="current-date">{local_now.strftime("%B %d, %Y")}</div>',
        unsafe_allow_html=True
    )
    
    st.title("📅 Daily Mystery Challenge")
    
    # Initialize timezone detection
    timezone = get_user_timezone()
    
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
        # Show local date
        st.caption(f"Mystery for {st.session_state.mystery['display_date']}")

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
            
            with st.expander(f"Mystery for {mystery['display_date']}", expanded=(idx == 0)):
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
