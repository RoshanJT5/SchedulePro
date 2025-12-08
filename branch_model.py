
class Branch(BaseModel):
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
