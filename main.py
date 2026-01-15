import sqlite3
from groq import Groq
from dotenv import load_dotenv
from database import get_connection
from secret import API_KEY

load_dotenv()
client = Groq(api_key=API_KEY)

class SQLOrchestrator:
    def __init__(self):
        self.model_id = "llama-3.3-70b-versatile"
        self.schema_context = """
        You are an expert SQLite Query Generator. 
        Your goal is to convert natural language questions into valid, executable SQLite code.
        Return ONLY the raw SQL. Do not use markdown blocks (```sql), do not add explanations.

        ### DATABASE SCHEMA
        1. **LOB** (Lines of Business)
        - Columns: ID (INT), LOB_Code (TEXT), Description (TEXT), Owner_SSO (TEXT)
        - Context: The 'Owner_SSO' is the primary executive for this business unit. LOB_Code examples: 'IT', 'HR'.

        2. **CostObject** (Cost Centers/Departments)
        - Columns: ID (INT), CostObject_Code (TEXT), Description (TEXT), Owner_SSO (TEXT), Company (TEXT), LOB_ID (INT)
        - Context: 'LOB_ID' links to LOB(ID).

        3. **Delegate** (Out of Office Logic)
        - Columns: ID (INT), In_SSO (TEXT), Out_SSO (TEXT), Valid_From (TEXT YYYY-MM-DD), Valid_To (TEXT YYYY-MM-DD)
        - Context: 
            - 'Out_SSO' is the person who is away (e.g., the LOB Owner).
            - 'In_SSO' is the temporary replacement.
            - A delegate is valid ONLY if date('now') is between Valid_From and Valid_To.

        4. **Matrix** (Approval Rules)
        - Columns: ID (INT), CostObject_ID (INT), LOB_ID (INT), Approver_SSO (TEXT), Approver_Name (TEXT), Approver_Email (TEXT), Approver_Level (INT), Active_Status (INT), Amount_Limit (REAL)
        - Context: Defines who approves what. 
            - Links to CostObject(ID) and LOB(ID).
            - A rule applies if the Request Amount <= Matrix.Amount_Limit.

        5. **Request_Master** (Incoming Transactions)
        - Columns: ID (INT), Store_Incoming_Request (TEXT JSON), System_DateTime (TEXT)
        - Context: 'Store_Incoming_Request' contains JSON data (e.g., '{"request_id": "REQ-1", "amount": 500}').

        6. **Approver** (Audit Trail)
        - Columns: ID (INT), Request_Master_ID (INT), Matrix_ID (INT), Action_Status (TEXT), Create_DateTime (TEXT)
        - Context: 
            - Links Request_Master(ID) to the Matrix rule used. Statuses: 'Waiting', 'Approved', 'Rejected'.
            - 'Who_Created' is the SSO of the person who actually clicked approve/reject.
            - To find "Delegate Actions", compare Matrix.Approver_SSO != Approver.Who_Created.

        ### CRITICAL BUSINESS RULES
        1. **Case Insensitivity:** The data is clean ('IT', 'HR'), but users are messy. 
        - ALWAYS use `LIKE` for text comparisons to handle capitalization differences.
        - Example: `WHERE LOB_Code LIKE 'it'` matches 'IT'.
        - Do NOT use wildcards (`%`) unless the user asks for "contains".
        2. **Column Priority:** - If user asks for "IT" or "HR", filter on `LOB.LOB_Code`.
        - If user asks for "CC_100", filter on `CostObject.CostObject_Code`.
        3. **Delegation:** Join LOB.Owner_SSO = Delegate.Out_SSO to find backups.
        4. **Dates:** Use `date('now')`.

        ### EXAMPLE QUERIES
        User: "Who approves requests for Cost Center CC_100 over $5000?"
        SQL: SELECT M.Approver_Name, M.Approver_Email FROM Matrix M JOIN CostObject C ON M.CostObject_ID = C.ID WHERE C.CostObject_Code = 'CC_100' AND M.Amount_Limit >= 5000 AND M.Active_Status = 1;

        User: "Show me all LOB owners currently on vacation (have a valid delegate)."
        SQL: SELECT L.LOB_Code, L.Owner_SSO, D.In_SSO FROM LOB L JOIN Delegate D ON L.Owner_SSO = D.Out_SSO WHERE date('now') BETWEEN D.Valid_From AND D.Valid_To;
        """

    def execute_sql(self, query):
        conn = get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query)
            return cursor.fetchall()
        except sqlite3.Error as e:
            return f"Database Error: {e}"
        finally:
            conn.close()

    def start_loop(self):
        print(f"--- SQL Orchestrator Active ({self.model_id}) ---")
        
        while True:
            user_input = input("\nYou: ")
            if user_input.lower() in ['exit', 'quit']: break

            try:
                chat_completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": self.schema_context},
                        {"role": "user", "content": user_input}
                    ],
                    model=self.model_id,
                )
                generated_sql = chat_completion.choices[0].message.content.strip()

                results = self.execute_sql(generated_sql)

                print(f"Agent (SQL): {generated_sql}")
                print(f"Agent (Data): {results}")
                
            except Exception as e:
                print(f"Groq API Error: {e}")
        
        print(f"--- End Of Orchestrator Conversation ---")

if __name__ == "__main__":
    orchestrator = SQLOrchestrator()
    orchestrator.start_loop()

# Show me all requests approved by someone other than the assigned Matrix approver.
# Who needs to approve a request for IT right now?
# Who will be approving for HR next month?
# Show me requests where the Approver is no longer active.
# Find the manager with the lowest level who can approve $50,000 for HR.
# When does the delegation for 'delegate_099' expire?
# Which Cost Centers have NO active approvers assigned?