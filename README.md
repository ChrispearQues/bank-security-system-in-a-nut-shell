# security Program 
homemade security prototype, testing use only 

# A open Perplepxity session is here to share infos
https://www.perplexity.ai/projects/secured-area-JkVsgcn3R6yEDPL1PZf_rA

# dependence extensions
all are recored inthe TXT file named requirents,
do this in windows terminal:
- pip install -r requirements.txt

# Local Development & Testing
Everything below is run from the project root (the folder that contains app/).

1. One-time setup
python3 -m venv .venv          # macOS / Linux
py -m venv .venv               # Windows

source .venv/bin/activate      # macOS / Linux  ← run every time you open a new terminal
.venv\Scripts\activate         # Windows
pip install -r requirements.txt

2. Run the app
Run this in powershell: uvicorn app.main:app --reload

--reload auto-restarts the server when you save a file.
Health check: http://127.0.0.1:8000/health → {"status":"ok"}
Swagger UI: http://127.0.0.1:8000/docs — click and send test requests from the browser.

3. Check the database
import app.main runs Base.metadata.create_all(),
creating bank.db (SQLite file in the project root) and any missing tables.
python -c "from app.db.database import engine; from sqlalchemy import inspect; print(inspect(engine).get_table_names())"
Healthy output: ['accounts', 'roles', 'user_roles', 'users']
# To see rows visually: install the VS Code extension SQLite Viewer and click bank.db.

4. Reset the database
create_all only creates tables that don't exist — it never alters an existing one. After editing a model, start over:
rm bank.db       # macOS / Linux
del bank.db      # Windows
Restart the app and bank.db is rebuilt from the current models.

5. Before you commit
# .venv/ and bank.db are already in .gitignore — never commit them. 
Run the app once; check /health and the table, list above, then push.