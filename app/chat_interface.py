import streamlit as st
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from services.llm import get_llm
from services.planner import generate_workout_plan 

#  Parse workout plan
def parse_workout_plan(workout_plan):
    if isinstance(workout_plan, dict):
        formatted_plan = "🎉 **Here's your personalized Peloton plan:**\n\n"
                    
                    # Iterate through weeks
        for week_key in sorted(workout_plan.keys()):
            if week_key.startswith('week'):
                formatted_plan += f"## 📅 {week_key.title()}\n\n"
                            
                for day in workout_plan[week_key]:
                                # Format date
                    date_str = day['day']
                    formatted_plan += f"### 🗓 {date_str}\n"
                                
                    if not day['activities']:
                        formatted_plan += "🛌 **Rest Day**\n\n"
                        continue
                                
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
        response += f"\n\nHere's your customized plan:\n{workout_plan}"
    return response

def initialize_peloton_chat():

    st.set_page_config(
    page_title="Peloton AI Workouts Planner",
    page_icon="🚴‍♂️"
)
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

# Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.workout_params = {}
        st.session_state.plan_generated = False

    # Add initial greeting message
        st.session_state.messages.append({
        "role": "assistant",
        "content": "👋 Hey, I'm here to help you create a personalized Peloton workout plan. The plan will be tailored to you base on your data and fitness level from Peloton. \n\nLet's get started!\n\nTo build your perfect plan, I'll need to know:\n\n"
                   "1. **Your fitness goals** (e.g., strength, endurance, weight loss)\n"
                   "2. **Available equipment** (bike, tread, weights)\n"
                   "3. **Preferred workout types** (cycling, running, strength, yoga, rowing)\n"
                   "4. **Weekly time commitment**\n\n"
                   "Just answer my questions, and I'll create a plan tailored just for you! 🚴‍♀️💪"
    })

# Initialize LangChain conversation
    if "conversation" not in st.session_state:
        llm = get_llm(temperature=0.8)
        memory = ConversationBufferMemory()
        st.session_state.conversation = ConversationChain(llm=llm, memory=memory)
    
    # Custom prompt for Peloton workouts
        st.session_state.conversation.prompt.template ="""You are Peloton AI chat bot. You goal is to get data from the user to create personalized Peloton workout plans.
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

# Streamlit UI
    st.markdown('<h1 class="peloton-header">🚴‍♂️ Peloton AI Workouts Planner 🏃</h1>', unsafe_allow_html=True)

# Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                st.markdown(f'<div class="assistant-message">{message["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(message["content"])

    if prompt := st.chat_input("What are your fitness goals?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

    # Get AI response
        with st.spinner('Thinking...'):
            response = st.session_state.conversation.invoke(prompt)["response"]
        
        # Check if all parameters are collected and JSON object is returned
        # TODO: Add more validation logic
            if "{" in response:
                try:   
                # Generate workout plan using existing logic
                    workout_plan = generate_workout_plan(
                    user_input=response
                )
                
                    response = parse_workout_plan(workout_plan)
                    st.session_state.plan_generated = True
                except Exception as e:
                    response = f"Error generating plan: {str(e)}"

    # Display AI response
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

initialize_peloton_chat()

