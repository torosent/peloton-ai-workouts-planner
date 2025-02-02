import datetime
import json
import os
from langchain_openai import AzureChatOpenAI
from langchain.prompts import PromptTemplate
from services.peloton import PelotonAPI
from services.llm import get_llm

def get_workout_prompt():
    return PromptTemplate(
        input_variables=["user_input", "workouts", "history", "profile","today_date"],
        template="""
        You are an experianced Peloton and fitness trainer task with creating a personalized weekly workout plan for users starting today {today_date}.
        Based on:
        - user's input: {user_input}, 
        - workouts that user can take: {workouts}, 
        - workout history: {history}, 
        - profile:  {profile}, 
        Create a personalized weekly workout plan for 4 weeks unless the user's input specify otherwise. Include up to 5 activities in a day and make sure the workouts are aligned with the user's goals and offer good training value.
        Make sure to include a variety of classes to keep the user engaged and motivated and have rest day at least once a week. Rest day should have the title Rest Day. 
        Output is in json format ordered by days. The json output should have "week with a number" as the key and the value should be a list of week days with the following key:
        - "day" : the day of the week. use exact date.
        every day should have the following keys
        - "activities" : a list of dictionaries with the following keys
        - "title" : the title of the activity
        - "description" : the description of the activity
        - "category" : the category of the activity
        - "duration" : the duration of the activity in minutes
        - "instructor" : the name of the instructor
        - "intensity" : the intensity of the activity
        - "url" : the url of the activity
        - 'extra_info' : a detailed explanation on why this workout is beneficial for the user's goals.
        """
    )

def generate_workout_plan(username, password, user_input: str):
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

    user_input_json = json.loads(user_input.lower())
    suggested_activities = user_input_json.get("suggested_activities", [])

    instructors = {}
    workouts = []
    if "cycling" in suggested_activities:
        cycling_workouts, cycling_instructors = retrieve_recent_workouts(client, "cycling")
        workouts.extend(cycling_workouts)
        instructors.update({instr["id"]: instr["name"] for instr in cycling_instructors})
    if "strength" in suggested_activities:
        strength_workouts, strength_instructors = retrieve_recent_workouts(client, "strength")
        workouts.extend(strength_workouts)
        instructors.update({instr["id"]: instr["name"] for instr in strength_instructors})
    if "running" in suggested_activities:
        running_workouts, running_instructors = retrieve_recent_workouts(client, "running")
        workouts.extend(running_workouts)
        instructors.update({instr["id"]: instr["name"] for instr in running_instructors})
    if "yoga" in suggested_activities:
        yoga_workouts, yoga_instructors = retrieve_recent_workouts(client, "yoga")
        workouts.extend(yoga_workouts)
        instructors.update({instr["id"]: instr["name"] for instr in yoga_instructors})
    if "rowing" in suggested_activities:
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
    'user_input':user_input,
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