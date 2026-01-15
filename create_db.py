import sqlite3
import random
import datetime

# --- Configuration ---
DB_NAME = "approval_system.db"

# Dummy Data Pools
LOBS = ['IT', 'HR', 'Finance', 'Legal', 'Sales', 'Marketing', 'Ops', 'R&D', 'Support', 'Product']
OWNERS = [f'user_{i:03d}' for i in range(1, 21)]  # user_001 to user_020
COMPANIES = ['Acme Corp', 'Globex', 'Soylent Corp', 'Initech', 'Umbrella Corp']
ACTIONS = ['Waiting', 'Approved', 'Rejected']

def get_connection():
    try:
        conn = sqlite3.connect(DB_NAME)
        # Enable foreign keys support in SQLite
        conn.execute("PRAGMA foreign_keys = ON") 
        return conn
    except sqlite3.Error as e:
        print(f"Connection Error: {e}")
        return None

def create_tables():
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        
        # 1. LOB Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS LOB (
                ID INTEGER PRIMARY KEY,
                LOB_Code TEXT NOT NULL,
                Description TEXT,
                Owner_SSO TEXT NOT NULL,
                Create_DateTime TEXT DEFAULT CURRENT_TIMESTAMP,
                Who_Updated TEXT,
                Who_Created TEXT,
                Update_DateTime TEXT
            )
        ''')

        # 2. CostObject Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS CostObject (
                ID INTEGER PRIMARY KEY,
                CostObject_Code TEXT,
                Description TEXT,
                Owner_SSO TEXT,
                Company TEXT,
                LOB_ID INTEGER,
                Create_DateTime TEXT DEFAULT CURRENT_TIMESTAMP,
                Who_Updated TEXT,
                Who_Created TEXT,
                Update_DateTime TEXT,
                FOREIGN KEY (LOB_ID) REFERENCES LOB(ID)
            )
        ''')

        # 3. Delegate Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Delegate (
                ID INTEGER PRIMARY KEY,
                In_SSO TEXT,
                Out_SSO TEXT,
                Valid_From TEXT,
                Valid_To TEXT,
                Create_DateTime TEXT DEFAULT CURRENT_TIMESTAMP,
                Who_Updated TEXT,
                Who_Created TEXT,
                Update_DateTime TEXT
            )
        ''')

        # 4. Request_Master Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Request_Master (
                ID INTEGER PRIMARY KEY,
                Store_Incoming_Request TEXT,
                System_DateTime TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 5. Matrix Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Matrix (
                ID INTEGER PRIMARY KEY,
                CostObject_ID INTEGER,
                LOB_ID INTEGER,
                Approver_SSO TEXT,
                Approver_Name TEXT,
                Approver_Email TEXT,
                Approver_Level INTEGER,
                Active_Status INTEGER, -- 0 or 1
                Amount_Limit REAL,
                Create_DateTime TEXT,
                Who_Updated TEXT,
                Who_Created TEXT,
                Update_DateTime TEXT,
                FOREIGN KEY (CostObject_ID) REFERENCES CostObject(ID),
                FOREIGN KEY (LOB_ID) REFERENCES LOB(ID)
            )
        ''')

        # 6. Approver Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Approver (
                ID INTEGER PRIMARY KEY,
                Request_Master_ID INTEGER,
                Matrix_ID INTEGER,
                Action_Status TEXT,
                Create_DateTime TEXT,
                Who_Updated TEXT,
                Who_Created TEXT,
                Update_DateTime TEXT,
                FOREIGN KEY (Request_Master_ID) REFERENCES Request_Master(ID),
                FOREIGN KEY (Matrix_ID) REFERENCES Matrix(ID)
            )
        ''')

        conn.commit()
        conn.close()
        print("All tables created successfully.")

def populate_data():
    conn = get_connection()
    if not conn:
        return
    cursor = conn.cursor()

    try:
        # --- Clear old data (Reverse order due to FK constraints) ---
        tables = ['Approver', 'Matrix', 'Request_Master', 'Delegate', 'CostObject', 'LOB']
        for table in tables:
            cursor.execute(f"DELETE FROM {table}")
        
        # Check if sqlite_sequence exists before trying to clear it
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sqlite_sequence'")
        if cursor.fetchone():
            for table in tables:
                cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")

        # --- 1. Populate LOB (20 rows) ---
        lob_data = []
        # Only loop through the actual list of names (10 items), not a range of 20
        for i, lob_name in enumerate(LOBS): 
            owner = random.choice(OWNERS)
            lob_data.append((
                lob_name,            
                f"Global {lob_name} Dept", 
                owner, 
                "System", "System"
            ))

        cursor.executemany("""
            INSERT INTO LOB (LOB_Code, Description, Owner_SSO, Who_Created, Who_Updated) 
            VALUES (?, ?, ?, ?, ?)
        """, lob_data)
        print(f"Populated LOB table with {len(lob_data)} clean rows.")

        # Fetch LOB IDs and Owners for FK references
        cursor.execute("SELECT ID, Owner_SSO FROM LOB")
        lob_refs = cursor.fetchall() # List of (id, owner)

        # --- 2. Populate CostObject (50 rows) ---
        co_data = []
        for i in range(1, 51):
            lob_id, _ = random.choice(lob_refs)
            co_data.append((
                f"CC_{i*100}", 
                f"Cost Center {i}", 
                f"owner_{random.randint(21, 40):03d}", # Different owners
                random.choice(COMPANIES), 
                lob_id,
                "System", "System"
            ))
        cursor.executemany("""
            INSERT INTO CostObject (CostObject_Code, Description, Owner_SSO, Company, LOB_ID, Who_Created, Who_Updated)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, co_data)
        print("Populated CostObject table.")

        # Fetch CostObject IDs
        cursor.execute("SELECT ID FROM CostObject")
        co_ids = [row[0] for row in cursor.fetchall()]

        # --- 3. Populate Delegate (30 rows) ---
        delegate_data = []
        if lob_refs:
            lob_owners_to_delegate = random.sample(lob_refs, min(10, len(lob_refs))) 
            for _, owner_sso in lob_owners_to_delegate:
                delegate_data.append((
                    f"delegate_{random.randint(50, 99):03d}", # In_SSO
                    owner_sso, # Out_SSO (The LOB Owner)
                    "2023-01-01", 
                    "2026-12-31",
                    "System", "System"
                ))
            
        for i in range(20):
            delegate_data.append((
                f"delegate_{random.randint(100, 150):03d}",
                f"random_user_{i:03d}", 
                "2023-01-01", 
                "2026-12-31",
                "System", "System"
            ))

        cursor.executemany("""
            INSERT INTO Delegate (In_SSO, Out_SSO, Valid_From, Valid_To, Who_Created, Who_Updated)
            VALUES (?, ?, ?, ?, ?, ?)
        """, delegate_data)
        print("Populated Delegate table.")

        # --- 4. Populate Request_Master (100 rows) ---
        req_data = []
        for i in range(1, 101):
            req_data.append((f'{{"request_id": "REQ-{i}", "amount": {random.randint(100, 5000)}}}',))
        cursor.executemany("INSERT INTO Request_Master (Store_Incoming_Request) VALUES (?)", req_data)
        print("Populated Request_Master table.")

        # --- 5. Populate Matrix (50 rows) ---
        # UPDATED: Randomize Amount_Limit
        matrix_data = []
        limit_tiers = [500.0, 1000.0, 2500.0, 5000.0, 10000.0, 50000.0]  # Defined approval limits
        
        for i in range(1, 51):
            co_id = random.choice(co_ids)
            lob_id, _ = random.choice(lob_refs)
            matrix_data.append((
                co_id, lob_id,
                f"approver_{random.randint(1, 10):03d}", 
                f"Approver Name {i}",
                f"approver{i}@company.com",
                random.randint(1, 5), # Level
                1, # Active
                random.choice(limit_tiers), # Random limit from tiers
                "System", "System"
            ))
        cursor.executemany("""
            INSERT INTO Matrix (CostObject_ID, LOB_ID, Approver_SSO, Approver_Name, Approver_Email, Approver_Level, Active_Status, Amount_Limit, Who_Created, Who_Updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, matrix_data)
        print("Populated Matrix table.")
        
        # Fetch Matrix IDs
        cursor.execute("SELECT ID FROM Matrix")
        matrix_ids = [row[0] for row in cursor.fetchall()]

        # --- 6. Populate Approver (100 rows) ---
        approver_data = []
        for i in range(1, 101):
            approver_data.append((
                i, 
                random.choice(matrix_ids),
                random.choice(ACTIONS),
                datetime.datetime.now().isoformat(),
                "System", "System"
            ))
        cursor.executemany("""
            INSERT INTO Approver (Request_Master_ID, Matrix_ID, Action_Status, Create_DateTime, Who_Created, Who_Updated)
            VALUES (?, ?, ?, ?, ?, ?)
        """, approver_data)
        print("Populated Approver table.")

        conn.commit()
    
    except sqlite3.Error as e:
        print(f"Error populating data: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_tables()
    populate_data()