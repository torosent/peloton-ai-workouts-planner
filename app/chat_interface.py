import streamlit as st
from streamlit_cookies_controller import CookieController
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_message_histories import ChatMessageHistory

# Project-specific imports:
from services.llm import get_llm
from services.planner import generate_workout_plan

# --- Helper Functions ---

def parse_workout_plan(workout_plan):
    """
    Parse the workout_plan (dict or other format) into a human-readable string.
    """
    response = ""
    if isinstance(workout_plan, dict):
        formatted_plan = "🎉 **Here's your personalized Peloton plan:**\n\n"
        for week_key in sorted(workout_plan.keys()):
            if week_key.startswith('week'):
                formatted_plan += f"## 📅 {week_key.title()}\n\n"
                for day in workout_plan[week_key]:
                    date_str = day.get('day', 'Unknown day')
                    formatted_plan += f"### 🗓 {date_str}\n"
                    if not day.get('activities'):
                        formatted_plan += "🛌 **Rest Day**\n\n"
                        continue
                    for activity in day.get('activities', []):
                        formatted_plan += (
                            f"#### 🏋️ {activity.get('title', '')}\n"
                            f"- **Duration**: {activity.get('duration', '')} min\n"
                            f"- **Instructor**: {activity.get('instructor', '')}\n"
                            f"- **Intensity**: {activity.get('intensity', '')}\n"
                            f"- **Description**: {activity.get('description', '')}\n"
                            f"- [Take Class Now]({activity.get('url', '')})\n"
                            f"- **Why This Workout**: {activity.get('extra_info', '')}\n\n"
                        )
        response = formatted_plan
    else:
        response += f"\n\nHere's your customized plan:\n{workout_plan}"
    return response

def save_workout_plan(workout_plan):
    """
    Save or persist the user's final workout plan. TODO: Save to database
    """
    print(workout_plan)

def get_session_history(session_id: str):
    store = st.session_state.global_history_store
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

# --- In-Memory Chat History via RunnableWithMessageHistory ---
if "global_history_store" not in st.session_state:
    st.session_state.global_history_store = {}

# Initialize the Peloton AI Workouts Planner with Streamlit
def initialize_peloton_chat():
    """
    Save or persist the user's final workout plan. Currently, it just prints to the console.
    """
    # Set page title and icon
    st.set_page_config(
        page_title="Peloton AI Workouts Planner",
        page_icon="🚴‍♂️",
      #  layout="wide",
    )

    # Replace inline CSS styling with loading external css file:
    with open('/Users/home/projects/peloton-workout-agent/static/styles.css', 'r') as f:
        css = f.read()
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

    st.markdown('<h1 class="peloton-header">🚴‍♂️ AI Workouts Planner 🏃</h1>', unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.workout_params = {}
        st.session_state.plan_generated = False
        st.session_state.messages.append({
            "role": "assistant",
            "content": (
                "👋 Hey, I'm here to help you create a personalized Peloton workout plan. "
                "The plan will be tailored to you based on your data and fitness level from Peloton.\n\n"
                "Let's get started!\n\nTo build your perfect plan, I'll need to know:\n\n"
                "1. **Your fitness goals** (e.g., strength, endurance, weight loss)\n"
                "2. **Available equipment** (bike, tread, weights)\n"
                "3. **Preferred workout types** (cycling, running, strength, yoga, rowing)\n"
                "4. **Weekly time commitment**\n\n"
                "Just answer my questions, and I'll create a plan tailored just for you! 🚴‍♀️💪"
            )
        })

    if "conversation" not in st.session_state:
        llm = get_llm(temperature=0.8).with_structured_output(method="json_mode")
        # Define a prompt template.
        # We escape the JSON keys with double curly braces so they are interpreted literally.

        # Replace inline prompt template with file import:
        with open('/Users/home/projects/peloton-workout-agent/prompts/chat_prompt_template.txt', 'r') as f:
            prompt_text = f.read()

        prompt_template = ChatPromptTemplate.from_template(prompt_text)
        # Compose the chain as prompt_template | llm.
        chain = prompt_template | llm

        # Wrap the chain with RunnableWithMessageHistory.
        from langchain_core.runnables.history import RunnableWithMessageHistory
        st.session_state.conversation = RunnableWithMessageHistory(
            chain,
            get_session_history=get_session_history,
            input_messages_key="input",
            output_messages_key="content",
            history_messages_key="history"
        )

    # Display previous messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                st.markdown(f'<div class="assistant-message">{message["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(message["content"])

    # Chat input: capture new messages
    if prompt_text := st.chat_input("What are your fitness goals?"):
        st.session_state.messages.append({"role": "user", "content": prompt_text})
        with st.chat_message("user"):
            st.markdown(prompt_text)
        with st.spinner("Thinking..."):
            result = st.session_state.conversation.invoke(
                {"input": prompt_text},
                config={"configurable": {"session_id": "default"}}
            )
            # Extract only the text from the result. If the result is a dict with a "content" key, use that.
            if result["done_collecting"] == False:
                response_text = result["content"]
            else:
                workout_plan = generate_workout_plan(None, None, user_input=result)
                st.session_state.workout_plan = workout_plan
                response_text = parse_workout_plan(workout_plan)
        st.session_state.messages.append({
            "role": "assistant",
            "content": response_text
        })
        # After displaying the workout plan, ask if the user wants to save or modify the plan.
        if result["done_collecting"]:
            st.session_state.messages.append({
                "role": "assistant",
                "content": "Would you like to modify the plan?"
            })
        st.rerun()

initialize_peloton_chat()
