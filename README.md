# NBCU Orchestration Agent

This project is a SQL-based agent designed to query and analyze approval requests, delegation rules, and cost center data.

## Setup & Installation

**1. Install Dependencies**
Make sure you are in your project folder (and your virtual environment is active), then run:
```bash
pip install -r requirements.txt
```

**2. Configure Secrets**
Create a new file named `secret.py` in the root directory. Inside, add your Groq API key:
```python
API_KEY = "your_groq_api_key_here"
```

**3. Initialize the Database**
Before running the agent, you must create the database schema:
```bash
python create_db.py
```

## How to Run

Start the agent with the main script:
```bash
python main.py
```

## Usage Examples

Once the agent is running, you can ask questions in natural language. Here are some examples to try:

* "Show me all requests approved by someone other than the assigned Matrix approver."
* "Who needs to approve a request for IT right now?"
* "Who will be approving for HR next month?"
* "Show me requests where the Approver is no longer active."
* "Find the manager with the lowest level who can approve $50,000 for HR."
* "When does the delegation for 'delegate_099' expire?"
* "Which Cost Centers have NO active approvers assigned?"

### Exiting
To end the conversation and close the script, simply type:
* `quit`
* `exit`
