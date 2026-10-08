from abc import ABC, abstractmethod

ALLOWED_STATUSES = ['open', 'in_progress', 'resolved', 'closed']
ALLOWED_PRIORITIES = ['low', 'medium', 'high', 'critical']


class BaseEntity(ABC):
    @abstractmethod
    def validate(self):
        pass

    def to_dict(self):
        return {
            key: value
            for key, value in self.__dict__.items()
        }


class Reporter(BaseEntity):
    def __init__(self, id, name, email, team):
        self.id = id
        self.name = name
        self.email = email
        self.team = team

    def validate(self):
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Name cannot be empty")
        if not isinstance(self.email, str) or '@' not in self.email:
            raise ValueError("Email must contain '@'")


class Issue(BaseEntity):
    def __init__(self, id, title, description, status, priority, reporter_id):
        self.id = id
        self.title = title
        self.description = description
        self.status = status
        self.priority = priority
        self.reporter_id = reporter_id

    def validate(self):
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("Title cannot be empty")
        if self.status not in ALLOWED_STATUSES:
            raise ValueError(
                f"Invalid status '{self.status}'. Allowed: {', '.join(ALLOWED_STATUSES)}"
            )
        if self.priority not in ALLOWED_PRIORITIES:
            raise ValueError(
                f"Invalid priority '{self.priority}'. Allowed: {', '.join(ALLOWED_PRIORITIES)}"
            )

    def describe(self):
        return f"{self.title} [{self.priority}]"


class CriticalIssue(Issue):
    def describe(self):
        return f"[URGENT] {self.title} — needs immediate attention"


class LowPriorityIssue(Issue):
    def describe(self):
        return f"{self.title} — low priority, handle when free"
