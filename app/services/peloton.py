import requests

class PelotonAPI:
    """
    A class to interact with the Peloton API.

    Attributes:
        BASE_URL (str): The base URL for the Peloton API.
        username (str): The username for Peloton account.
        password (str): The password for Peloton account.
        session (requests.Session): The session object for making requests.
        session_id (str): The session ID after authentication.
        user_id (str): The user ID after authentication.

    Methods:
        authenticate():
            Authenticates the user with the Peloton API.
        
        get_workout_categories():
            Fetches the workout categories available on Peloton.
        
        get_last_rides(category, limit=10):
            Fetches the last rides for a given category.
        
        get_workout_history(limit=18):
            Fetches the workout history of the authenticated user.
        
        get_user_profile():
            Fetches the profile information of the authenticated user.
    """
    BASE_URL = "https://api.onepeloton.com"

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({"peloton-platform": "web"})
        self.session_id = None
        self.user_id = None

    def authenticate(self):
        url = f"{self.BASE_URL}/auth/login"
        payload = {"username_or_email": self.username, "password": self.password}
        response = self.session.post(url, json=payload)
        if response.status_code == 200:
            data = response.json()
            self.session_id = data["session_id"]
            self.user_id = data["user_id"]
            self.session.cookies.set("peloton_session_id", self.session_id)
        else:
            raise Exception("Authentication failed.")

    def get_workout_categories(self):
        url = f"{self.BASE_URL}/api/browse_categories?library_type=on_demand"
        response = self.session.get(url)
        if response.status_code == 200:
            return response.json().get("browse_categories", [])
        else:
            raise Exception("Failed to fetch categories.")


    def get_last_rides(self, category, limit=10):
        url = f"{self.BASE_URL}/api/v2/ride/archived"
        response = self.session.get(url, params={"limit": limit, "browse_category": category, "content_format": "audio,video", "sort_by": "original_air_time","page": 0})
        if response.status_code == 200:
            workouts = response.json().get("data", [])
            instructors = response.json().get("instructors", [])
            return workouts, instructors
        else:
            raise Exception("Failed to fetch rides.")

    def get_workout_history(self, limit=18):
        url = f"{self.BASE_URL}/api/user/{self.user_id}/workouts"
        response = self.session.get(url, params={"limit": limit})
        if response.status_code == 200:
            return response.json().get("data", [])
        else:
            raise Exception("Failed to fetch history.")

    def get_user_profile(self):
        url = f"{self.BASE_URL}/api/me"
        response = self.session.get(url)
        if response.status_code == 200:
            return {
                "weight": response.json().get("weight"),
                "height": response.json().get("height"),
                "age": response.json().get("age"),
                "gender": response.json().get("gender", "unspecified"),
            }
        else:
            raise Exception("Failed to fetch profile.")
