# Script to add Branch model to models.py

with open('models.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the position after StudentGroup class
insert_marker = "class PeriodConfig(BaseModel):"
insert_pos = content.find(insert_marker)

if insert_pos == -1:
    print("ERROR: Could not find PeriodConfig class")
    exit(1)

# Branch model code
branch_code = '''class Branch(BaseModel):
    """Represents an academic branch/specialization (e.g., Computer Science in B.Tech)"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not hasattr(self, 'program'): self.program = None
        if not hasattr(self, 'name'): self.name = None
        if not hasattr(self, 'code'): self.code = None
        if not hasattr(self, 'hod_name'): self.hod_name = None
        if not hasattr(self, 'duration_years'): self.duration_years = 4
        if not hasattr(self, 'total_semesters'): self.total_semesters = 8

    def to_dict(self):
        d = super().to_dict()
        d['program'] = getattr(self, 'program', None)
        d['name'] = getattr(self, 'name', None)
        d['code'] = getattr(self, 'code', None)
        d['hod_name'] = getattr(self, 'hod_name', None)
        d['duration_years'] = getattr(self, 'duration_years', 4)
        d['total_semesters'] = getattr(self, 'total_semesters', 8)
        return d

    def __repr__(self):
        return f'<Branch {getattr(self, "name", None)} ({getattr(self, "program", "")})>'


'''

# Insert Branch code before PeriodConfig
new_content = content[:insert_pos] + branch_code + content[insert_pos:]

# Write back
with open('models.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("SUCCESS: Branch model added to models.py")
