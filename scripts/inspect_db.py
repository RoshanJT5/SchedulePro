from app.database import engine
from sqlalchemy import inspect
insp = inspect(engine)
for tbl in ['courses','instructors','rooms','timeslots']:
    if insp.has_table(tbl):
        cols = [c['name'] for c in insp.get_columns(tbl)]
        print(f"Table {tbl}: columns -> {cols}")
    else:
        print(f"Table {tbl} does not exist")
