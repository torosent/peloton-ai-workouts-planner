import uuid
import streamlit as st
from streamlit_cookies_controller import CookieController

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
    """Persist the workout plan (here, simply printing it)."""
    print(workout_plan)

# --- In-Memory Chat History via RunnableWithMessageHistory ---
# We use ChatMessageHistory from langchain_community.
from langchain_community.chat_message_histories import ChatMessageHistory  # pip install -U langchain-community

if "global_history_store" not in st.session_state:
    st.session_state.global_history_store = {}

def get_session_history(session_id: str):
    store = st.session_state.global_history_store
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

# --- Main Interface using RunnableWithMessageHistory ---
def initialize_peloton_chat():

    # Set page title and icon
    st.set_page_config(
        page_title="Peloton AI Workouts Planner",
        page_icon="🚴‍♂️",
      #  layout="wide",
    )

    # Customized styling
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
        color: #ffffff;
    }
    .stChatInput input {
        background-color: #333333 !important;
        color: white !important;
        border: 1px solid #4CAF50;
    }
    .st-bd {
        background-color: #333333;
    }
    .peloton-header {
        text-align: center;
        padding: 20px;
        font-size: 2.5em;
        color: #4CAF50;
        text-shadow: 2px 2px 4px #000000;
    }
    .assistant-message {
        padding: 1.5rem;
        border-radius: 15px;
        background: rgba(44,83,100,0.9);
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

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
        from langchain_core.prompts import ChatPromptTemplate
        prompt_template = ChatPromptTemplate.from_template(
            (
                "You are Peloton AI chat bot. Your goal is to get data from the user to create personalized Peloton workout plans."
                "The data will help create optimized workout schedules by another service based on their time commitment, goals, and equipment availability."
                "Continue the conversation naturally. Ask follow-up questions to collect: "
                "1. User's fitness goals (strength, endurance, weight loss)"
                "2. Available Peloton equipment (bike, tread, weights)"
                "3. Preferred workout types (cycling, running, strength, yoga)"
                "4. Weekly time commitment\n"
                "You can make assumptions about the user equipment, time and workout types based on the user messages. For example, if the user mentions they have a bike, you can assume they are interested in cycling.\n"
                "Response format:\n"
                "1. If you need more information, ask the user for it and respond with a JSON object\n"
                '{{"content":...}}\n'
                "2. When all information and data is collected, respond with a JSON object with keys:\n"
                '{{"content":...,user_goals": ..., "weekly_time_commitment": ..., "suggested_activities": []}}\n\n'
                "suggested_activities is a list of activities that the user can take (cycling, strength, yoga, running, rowing)\n"
                "Current conversation history:\n{history}\n"
                "Human: {input}\n"
                "Peloton AI Workouts Planner:"
            )
        )
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
            st.markdown(message["content"], unsafe_allow_html=True)

    # if st.session_state.get("plan_generated", False):
    #     col1, col2 = st.columns(2)
    #     with col1:
    #         if st.button("🔄 Modify Plan", use_container_width=True):
    #             with st.chat_message("assistant"):
    #                 st.markdown("Would you like to modify the plan?")
    #     with col2:
    #         if st.button("💾 Save Plan", use_container_width=True):
    #             save_workout_plan(st.session_state.workout_plan)
    #             st.success("✅ Plan saved successfully!")
    #             st.session_state.messages.append({
    #                 "role": "assistant",
    #                 "content": "Your plan has been saved! You can now modify it or start a new plan."
    #             })
    #             st.rerun()

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
            if isinstance(result, dict) and "user_goals" not in result:
                response_text = result["content"]
            else:
                workout_plan = generate_workout_plan(None, None, user_input=result)
                st.session_state.workout_plan = workout_plan
                response_text = parse_workout_plan(workout_plan)
                response_text += "\n\nWould you like to save or modify the plan?"
        st.session_state.messages.append({
            "role": "assistant",
            "content": response_text
        })
        st.rerun()

initialize_peloton_chat()
