# Peloton AI Workouts Planner

This AI agent generates a personalized weekly workout plan using Peloton’s API and GPT-4o. The agent will create a plan tailored to your workout history, physical attributes, and fitness goals. The agent will also adjust the plan over time according to your workout history and progress. 

## TODO
- [ ] Add prompt options with categories such as cycling, running, rowing, etc.
- [ ] Add persistent data store.
- [ ] Add cron jobs to analyze progress and adjust the plan.
- [ ] Integrate a robust framework to operate at scale such as Azure Durable Task Scheduler, ensuring every task is executed consistently over time.

> **Note:** This project is a proof of concept. A real AI agent would be able to schedule workouts, but the current APIs do not support this functionality.

## Project Structure

- **app/chat_interface.py**  
  Entry point for the Streamlit chat.
- **app/services/peloton.py**  
  Interacts with the Peloton API.
- **app/services/planner.py**  
  Calls the Peloton API, processes user data, and invokes GPT-4 for plan creation.
- **requirements.txt**  
  Python dependencies.
- **.env**  
  Specifies environment variables (see below).

## Setup

1. Clone or download the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a .env file with the following variables:

| Variable                | Type   | Description                           |
|-------------------------|--------|---------------------------------------|
| AZURE_OPENAI_ENDPOINT   | string | The endpoint for Azure OpenAI (GPT-4o).|
| AZURE_OPENAI_API_KEY    | string | Azure OpenAI API key.                 |
| PELOTON_USERNAME        | string | Your Peloton account username.        |
| PELOTON_PASSWORD        | string | Your Peloton account password.        |

4. Run the server locally:
```bash
streamlit run app/chat_interface.py
```

## Example Prompts

Here are some example prompts you can use to specify your fitness goals:

- "I want to lose weight and tone my body."
- "I am training for a marathon and need a running plan."
- "I want to increase my flexibility and core strength."
- "I need a balanced workout plan that includes both cardio and strength training."
- "I want to improve my cycling performance."

3. Obtain your personalized workout plan in a calendar view.

## Legal Disclaimer

This project is not affiliated with, endorsed by, or in any way associated with Peloton Interactive, Inc. The use of Peloton’s API is for educational and proof-of-concept purposes only. All trademarks, service marks, and company names are the property of their respective owners. Use this project at your own risk. The authors are not responsible for any misuse or damage caused by this project.
