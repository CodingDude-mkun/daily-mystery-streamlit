import streamlit as st
from google import genai

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
mysteries = [
   {
        "question": "A man was found dead in a locked room with no windows. The only items in the room were a puddle of water and a rope. What happened?",
        "answer": "The man stood on an ice block to hang himself, and the ice melted."
    },
    {
        "question": "A woman buys a parrot that is supposed to repeat everything it hears. But after weeks, it hasn’t spoken a word. Why?",
        "answer": "The parrot is deaf."
    }
]
client = genai.Client(api_key='AIzaSyAwQOX22INQ78rtf7G3XVSGuop7QieRwjg')


def generate_mystery():
    response = client.models.generate_content(model ='gemini-2.0-flash', contents=prompt)
    return {
        'mystery': response.text.split('Answer:')[0], 
        'answer': response.text.split('Answer:')[1]
    }   if response else 'Err'

st.title("📅 Daily Mystery Challenge")

mystery = generate_mystery()


st.write(f"{mystery['mystery']}")
if st.button("Reveal Answer"):
    st.write(f"**Answer:** {mystery['answer']}")