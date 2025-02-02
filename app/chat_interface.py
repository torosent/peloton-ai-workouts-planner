import uuid
import streamlit as st
from streamlit_cookies_controller import CookieController
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from services.llm import get_llm
from services.planner import generate_workout_plan

# Parse the workout plan
def parse_workout_plan(workout_plan):
    """
    Parse the workout_plan (either a dict or another format) into a human-readable string
    that can be displayed in the Streamlit UI.
    """
    # Initialize a default response
    response = ""

    if isinstance(workout_plan, dict):
        formatted_plan = "🎉 **Here's your personalized Peloton plan:**\n\n"
        # Iterate through the workout plan dictionary by week
        for week_key in sorted(workout_plan.keys()):
            if week_key.startswith('week'):
                formatted_plan += f"## 📅 {week_key.title()}\n\n"
                # Iterate through each day within the week
                for day in workout_plan[week_key]:
                    date_str = day['day']
                    formatted_plan += f"### 🗓 {date_str}\n"
                    # If no activities, mark it as a rest day
                    if not day['activities']:
                        formatted_plan += "🛌 **Rest Day**\n\n"
                        continue
                    # Display each activity
                    for activity in day['activities']:
                        formatted_plan += (
                            f"#### 🏋️ {activity['title']}\n"
                            f"- **Duration**: {activity['duration']} min\n"
                            f"- **Instructor**: {activity['instructor']}\n"
                            f"- **Intensity**: {activity['intensity']}\n"
                            f"- **Description**: {activity['description']}\n"
                            f"- [Take Class Now]({activity['url']})\n"
                            f"- **Why This Workout**: {activity['extra_info']}\n\n"
                        )
        response = formatted_plan
    else:
        # If not a dict, provide a fallback message
        response += f"\n\nHere's your customized plan:\n{workout_plan}"

    return response

# Save the workout plan
def save_workout_plan(workout_plan):
    """
    Save or persist the user's final workout plan. Currently, it just prints to the console.
    """
    print(workout_plan)

# Initialize the Peloton AI Workouts Planner with Streamlit
def initialize_peloton_chat():
    """
    Main function to initialize the Peloton AI Workouts Planner with Streamlit.
    Handles user authentication, conversation, workout plan generation, and plan saving.
    """

    # Configure the Streamlit page
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

    # Initialize cookie controller for Peloton credentials
    controller = CookieController()

    col1, col2 = st.columns([5,1])
    with col1:
        st.markdown('<h1 class="peloton-header">🚴‍♂️ AI Workouts Planner 🏃</h1>', unsafe_allow_html=True)
    with col2:
        if st.session_state.get('plan_generated') or controller.get('peloton-chat'):
            if st.button("🚪 Log Out", use_container_width=True):
                # Clear cookies and session state
                controller.remove('peloton-chat')
                st.session_state.messages = []
                st.session_state.workout_params = {}
                st.session_state.plan_generated = False
                if 'workout_plan' in st.session_state:
                    del st.session_state.workout_plan
                st.rerun()
                
    cookie = controller.get('peloton-chat')

    if cookie is None or not cookie.get('username') or not cookie.get('password'):
        # Show login form
        st.markdown("### Please Enter Your Peloton Credentials. \n**The credentials are required to access your Peloton data and are not stored in the server**")
        username = st.text_input("Peloton Username")
        password = st.text_input("Peloton Password", type="password")
        if st.button("Submit and let's start planning!"):
            if username and password:
                controller.set("peloton-chat", {"username": username, "password": password}, secure=True, same_site='strict', max_age=3600)
                st.rerun()
            else:
                st.error("Both username and password are required.")
        st.stop()
    else:
        username = cookie['username']
        password = cookie['password']

    # Skip login for testing
    username = None
    password = None

    # Initialize session state for messages and plan data
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.workout_params = {}
        st.session_state.plan_generated = False

        # Add initial greeting
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

    # Use LangChain conversation with a conversation buffer memory
    if "conversation" not in st.session_state:
        llm = get_llm(temperature=0.8)
        memory = ConversationBufferMemory()
        st.session_state.conversation = ConversationChain(llm=llm, memory=memory)

        # Customize the prompt to specifically gather user data for Peloton plan generation
        st.session_state.conversation.prompt.template = """You are Peloton AI chat bot. You goal is to get data from the user to create personalized Peloton workout plans.
    The data will help create optimized workout schedules by another service based on their time commitment, goals, and equipment availability.
    Start by asking about:
    1. User's fitness goals (strength, endurance, weight loss)
    2. Available Peloton equipment (bike, tread, weights)
    3. Preferred workout types (cycling, running, strength, yoga)
    4. Weekly time commitment
    You can make assumptions about the user equipment, time and workout types based on the user messages. For example, if the user mentions they have a bike, you can assume they are interested in cycling.
    Ask one question at a time. 
    Respond ONLY with the JSON object in the following format when all data is collected. Do not include any additional text or explanations.
    {{
        "user_goals": "User's fitness goals",
        "weekly_time_commitment": "User's weekly time commitment",
        "suggested_activities": [] "array of suggested activities supported by Peloton such as cycling, running, strength, yoga"
    }}

    Current conversation:
    {history}
    Human: {input}
    Peloton AI Workouts Planner:"""

    # Display past messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                st.markdown(f'<div class="assistant-message">{message["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(message["content"])

    # If a plan was already generated, display option to modify or save
    if st.session_state.get('plan_generated', False):
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Modify Plan", use_container_width=True):
                with st.chat_message("assistant"):
                    st.markdown("Would you like to modify the plan?")

                # # Reset messages by removing the plan contents
                # st.session_state.messages = [
                #     msg for msg in st.session_state.messages
                #     if not (
                #         "personalized Peloton plan" in msg["content"]
                #         or "Would you like to modify" in msg["content"]
                #     )
                # ]
                # # Reset conversation chain and plan-generated flag
                # llm = get_llm(temperature=0.8)
                # memory = ConversationBufferMemory()
                # st.session_state.conversation = ConversationChain(llm=llm, memory=memory)
                # st.session_state.plan_generated = False
                # st.rerun()

        with col2:
            if st.button("💾 Save Plan", use_container_width=True):
                save_workout_plan(st.session_state.workout_plan)
                st.success("✅ Plan saved successfully!")
                # Append confirmation message
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "Your plan has been saved! You can now modify it or start a new plan."
                })
                st.rerun()

    # Chat input to capture new user prompts
    if prompt := st.chat_input("What are your fitness goals?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate assistant response
        with st.spinner('Thinking...'):
            response = st.session_state.conversation.invoke(prompt)["response"]

            # Check if user data is collected in a JSON format
            if "{" in response:
                try:
                    # Send user data to services.planner.generate_workout_plan
                    workout_plan = generate_workout_plan(username, password, user_input=response)
                    st.session_state.workout_plan = workout_plan
                    parsed_response = parse_workout_plan(workout_plan)

                    # Add final plan and confirmation prompt
                    st.session_state.messages.extend([
                        {"role": "assistant", "content": parsed_response},
                        {"role": "assistant", "content": "Would you like to make any changes to this plan or save it?"}
                    ])

                    st.session_state.plan_generated = True
                    st.rerun()

                except Exception as e:
                    error_msg = f"Error generating plan: {str(e)}"
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
            else:
                # If not JSON-like, simply append the response
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()

# Run the initialization when this script is executed
initialize_peloton_chat()
