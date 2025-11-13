# Project Golf – Electronic Voting System
A secure Electronic Voting System developed by Team Project Golf for CSC-131 (Fall 2025). The application is built with Flask (Python) and MySQL following the Waterfall Model to ensure a structured, documentation-driven development process.

## Project Overview

# Voter-Facing Pages
Home Page: Introduces the project and its goals.
Registration / Login page
Voting Page / Ballot Window: Users can cast one vote per election and modify their vote before the deadline.
Results Page: Displays election results only after voting closes, with vote counts and statistics.
User Dashboard: Overview of active elections and available user actions.

## Administrator-Facing Pages
Admin Login Page: Secure login for administrators.
Event Creation Page: Allows administrators to create polls, surveys, elections, and competitions.
User Management Page: Enables administrators to view all registered users and their respective roles. Administrators cannot generate or edit votes.

## Group and Informational Pages
About Page: Includes team member bios with education, skills, experience, and awards.
Credits Page: Displays tasks and roles completed by each team member, optionally with headshots.
Contact Page: Provides a form for users to send messages to the team, including name, email, phone number, and message fields.
Footer with Social Media Links: Clickable links to GitHub, LinkedIn, Facebook, Twitter, and Instagram accounts.

## Core Functional Requirements
User Registration/Login: Secure account creation and authentication.
Ballot Management: Cast one vote per election and modify before the deadline.
Result Visualization: Display results only after voting closes.
Admin Functions: Create events and view registered users; cannot vote or modify ballots.
Vote Validation: Prevent multiple votes from the same user.
Reporting: Automatically collate and generate visual reports/results for each event after voting ends.
Security: Ensure only authorized users can access the features relevant to their role.


## Waterfall Development Model
This project strictly follows the Waterfall model, ensuring each phase is fully documented and approved before moving forward:
1. Requirements Analysis – Define system requirements and constraints.
2. System Design – Create ER diagrams, database schema, UI wireframes.
3. Implementation – Develop Flask backend, MySQL database, and frontend templates.
4. Integration and Testing – Unit testing, database testing, and functional verification.
5. Deployment – Deploy final system on a local or cloud environment.
6. Maintenance – Post-deployment fixes and documentation updates.

## Team Members and Roles
Name: Jang Singh & Derek, Role: Project Manager & Documentation Lead, Responsibilities: Schedule, organize meetings, manage GitHub, prepare documentation
Name: Ceaser, Role: Analyst, Responsibilities: Project documentation, collaborate with project manager and designer
Name: Darren & Arav, Role: Designer, Responsibilities: UI/UX design
Name: Yucheng Yu & Ceaser, Role: Frontend Developer, Responsibilities: HTML/CSS/JS templates
Name: Alex & Darren, Role: Backend Developer, Responsibilities: Flask routes, database models, authentication logic
Name: Derek, Role: Database Engineer, Responsibilities: MySQL schema, ERD, query optimization
Name: Jarret, Role: QA/Test Engineer, Responsibilities: Test plans, unit/integration testing, bug reporting
<!-- Can change the above upon request -->


## Technologies
- Backend: Python 3, Flask
- Database: MySQL and aiven(host database)
- Frontend: HTML5, CSS3, JavaScript (Jinja2 templates)
- Version Control: Git and GitHub
- Environment: macOS/Linux/Windows

## System Requirements
- Python 3.10 or higher
- MySQL 8.0 or higher
- pip (Python package manager)
- Git

## Setup and Installation
1. Clone Repository
   `git clone https://github.com/Jsingh651/project-golf-electronic-voting.git`
   `cd project-golf-electronic-voting`

2. Install python on your machine 


3. Create Virtual Environment and Activate
   Run `python3 -m venv venv `
   Activate Environment `source venv/bin/activate`
   Install dependencies: `pip install -r requirements.txt` (might be different command for windows)

4. Run Application  
  `python server.py`  
  The app will be accessible at http://127.0.0.1:{dynamic_port}/ (server chooses a free port).  
  You can also set a fixed port (e.g. for Docker) by editing `server.py` to use a constant.

<!-- For developers -->
 Once done with the setup and a page is showing up on the browser reach out to project manager to setup git branches.
 We will have to share a database server so everyone can access it instead of it being on each developers computer.
 We can use aiven to host a shared MySQL database. Database engineer will have to work with developers to get the backend connected to the database.

## Project Timeline
| Phase | Target Completion |
|------|-------------------|
| Requirements Analysis | Week 2 |
| System Design | Week 4 |
| Implementation | Week 8 |
| Testing and Integration | Week 9 |
| Final Deployment | Week 10 |


## Documentation
## Migrations & Diagnostics
Scripts have been organized under `scripts/`:

```
scripts/
  migrations/
    create_option_table.py          # Idempotent creation of the `option` table
    migrate_fk_vote_to_option.py    # Idempotent fix for vote.vote_option_id foreign key
    docs/sql/migrations/2025-11-11_fix_vote_fk.sql  # Raw SQL (use only if FK still points to `choices`)
  diagnostics/
    inspect_schema.py               # Lists key tables and foreign keys
    list_event_option_counts.py     # Recent events with candidate counts
```

Usage examples:

Create option table (safe to run multiple times):
```
python scripts/migrations/create_option_table.py
```

Fix foreign key if legacy schema pointed to `choices`:
```
python scripts/migrations/migrate_fk_vote_to_option.py
```

Schema inspection:
```
python scripts/diagnostics/inspect_schema.py
```

Event / option counts:
```
python scripts/diagnostics/list_event_option_counts.py
```

Manual foreign-key smoke test (development only):
```
python tests/manual/test_fk_insert.py
```

## Voting Flow (Backend Summary)
Routes:
- `POST /vote/cast`  Submit or update the user's vote for an open event.
- `POST /vote/delete` Retract an existing vote while event is still open.

Server-side validations include:
1. Auth & role check (must be logged in and not an admin for voting).
2. Event existence & status (`Open`).
3. Option belongs to the targeted event.
4. One vote per user per event (update instead of duplicate insert).

Future enhancements (optional):
- Live results visibility toggle (currently results show after event closes; could allow "show after vote" strategy).  
- Caching tallies for high‑traffic events.  
- Replacing `print()` diagnostics with structured logging.

Detailed documentation (requirements, design diagrams, test plans) will be maintained in the /docs directory and updated at the completion of each Waterfall phase.


## Folder and file structure.

Current structure has 5 folders. 
config: Is to connect to the database server.
models: Read/Write/Delete in the database by connecting to config and controllers folder for the api routes.
controllers: Connects to the models and frontend (a middle man between database and frontend)
static: includes javascript, css, fonts, images
templates: holds html files for the frontend.
__init__.py: Basically marks the flask_app folder as a package and can initialize it. so you can easily import files and functions from one file to another.
requirements.txt: lists dependencies; goes in the project root.
server.py: starts your Flask app; goes in the project root too.

<!-- Once you do the setup additional files will appear Pipfile and Pipfile.lock -->
<!-- for best practices use .env file for any private keys and .gitignore so the .env file isnt pushed up onto github -->


## Database Engineer Tasks

### 1. Aiven MySQL Database Already Created
- The database `votesystemdb` has been set up on Aiven.
- Connection credentials:


- **Note:** The `ca.pem` file is in the project folder (`flask_app/config/ca.pem`) so all developers can use it.

CREDS:
Host: mysql-34862870-votesystemdb.d.aivencloud.com
Port: 18174
Database: defaultdb
User: avnadmin
Password: ***REMOVED***
SSL Mode: REQUIRED
CA Certificate: ca.pem (included in the project folder)

### 2. Test Connection Using MySQL Workbench
Each developer should:
1. Open **MySQL Workbench** → `Database → Manage Connections → New Connection`
2. Enter the above credentials.
3. Under **SSL**, select “Require SSL” and point to the `ca.pem` certificate in `flask_app/`.
4. Click **Test Connection** to ensure it works.

---

### 3. Create ERDs (Entity-Relationship Diagrams)
- Developers should create ERDs locally in MySQL Workbench for reference:
  1. Create tables (e.g., `users`, `votes`, `elections`, etc.).
  2. Define primary keys, foreign keys, and relationships.
  3. Optionally, reverse engineer from the Aiven database if you want to reflect existing tables.
- **Forward Engineer** the ERD to Aiven if any schema changes are made:
  - Select `defaultdb` as the target database.
  - Ensure SSL is enabled.
- Save the ERD file locally for documentation and version control.

---

### 4. Verify Database Functionality
- Run sample queries in MySQL Workbench or Aiven Query Console to confirm tables are working:
```sql
Create a dummy user: See if it shows up and then delete it. We only get 1gb of database storage on the free tier.


## Task assignment
We will use trello to keep track of the progress and tasks.
Trello link: 
https://trello.com/invite/b/68d37c7a355d2c21c36e3bcc/ATTI35f812121433e0aeffd617d6ffa8e8f0FEAE1537/votingsystem

Meeting time to be decided to track progress once every week.

-- Note to team members: If you guys need any help or confused on anything just reach out to me.
