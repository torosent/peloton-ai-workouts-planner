import datetime
import json
import os
from langchain.prompts import PromptTemplate
from services.peloton import PelotonAPI
from services.llm import get_llm

def get_workout_prompt():
    with open('/Users/home/projects/peloton-workout-agent/prompts/workout_prompt_template.txt', 'r') as f:
        template_content = f.read()
    return PromptTemplate(
        input_variables=["user_input", "workouts", "history", "profile", "today_date"],
        template=template_content
    )

def generate_workout_plan(username, password, user_input):
    """
    Generate a workout plan using Peloton API and GPT-4o.
    """
    
    if username is None or password is None:
        username=os.getenv("PELOTON_USERNAME")
        password=os.getenv("PELOTON_PASSWORD")

    # Authenticate with Peloton API
    client = PelotonAPI(
        username=username,
        password=password
    )
    client.authenticate()

    collected_data = user_input.get("collected_data", [])

    preferred_workouts = collected_data.get("preferred_workouts", [])
    instructors = {}
    workouts = []
    if "cycling" in preferred_workouts:
        cycling_workouts, cycling_instructors = retrieve_recent_workouts(client, "cycling")
        workouts.extend(cycling_workouts)
        instructors.update({instr["id"]: instr["name"] for instr in cycling_instructors})
    if "strength" in preferred_workouts:
        strength_workouts, strength_instructors = retrieve_recent_workouts(client, "strength")
        workouts.extend(strength_workouts)
        instructors.update({instr["id"]: instr["name"] for instr in strength_instructors})
    if "running" in preferred_workouts:
        running_workouts, running_instructors = retrieve_recent_workouts(client, "running")
        workouts.extend(running_workouts)
        instructors.update({instr["id"]: instr["name"] for instr in running_instructors})
    if "yoga" in preferred_workouts:
        yoga_workouts, yoga_instructors = retrieve_recent_workouts(client, "yoga")
        workouts.extend(yoga_workouts)
        instructors.update({instr["id"]: instr["name"] for instr in yoga_instructors})
    if "rowing" in preferred_workouts:
        rowing_workouts, rowing_instructors = retrieve_recent_workouts(client, "caesar")
        workouts.extend(rowing_workouts)
        instructors.update({instr["id"]: instr["name"] for instr in rowing_instructors})
    
    stretching_workouts, stretching_instructors = retrieve_recent_workouts(client, "stretching")
    workouts.extend(stretching_workouts)
    instructors.update({instr["id"]: instr["name"] for instr in stretching_instructors})

    new_workouts = []
    for workout in workouts:
        new_workout = {
            "url": "https://members.onepeloton.com/classes/all?modal=classDetailsModal&classId="+workout["id"],
            "title": workout["title"],
            "instructor": workout["instructor_id"],
            "description": workout["description"],
            "fitness_discipline": workout["fitness_discipline"],
            "duration_in_seconds": workout["duration"],
            "difficulty": workout["difficulty_estimate"],
        }
        new_workouts.append(new_workout)
    for workout in new_workouts:
        workout["instructor"] = instructors.get(workout["instructor"], "Unknown")
    history = client.get_workout_history()
    new_history = []
    for workout in history:
        new_workout = {
            "name": workout.get("name", "Unknown"),
            "taken_at": datetime.datetime.fromtimestamp(workout.get("start_time", 0)).strftime('%Y-%m-%d %H:%M:%S') if workout.get("start_time") else "Unknown",
            "fitness_discipline": workout.get("fitness_discipline", "Unknown"),
            "duration_in_seconds": workout.get("end_time", 0) - workout.get("start_time", 0) if workout.get("end_time") and workout.get("start_time") else 0,
            "difficulty": workout.get("effort_zones", {}).get("total_effort_points", "Unknown") if workout.get("effort_zones") else "Unknown",
            "heart_rate_zones": workout.get("effort_zones", {}).get("heart_rate_zone_durations", "Unknown") if workout.get("effort_zones") else "Unknown",
        }
        new_history.append(new_workout)
    profile = client.get_user_profile()

    # category_names = [cat["name"] for cat in categories]
    llm = get_llm().with_structured_output(method="json_mode")
    chain = get_workout_prompt() | llm
    
    input_data = {
    'user_input':collected_data,
        'workouts':new_workouts,
        'history':new_history,
        'profile':profile,
        'today_date':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
}

    content = chain.invoke(
        input=input_data,
    )
    return content

def retrieve_recent_workouts(client, category):
    return client.get_last_rides(category, limit=50)