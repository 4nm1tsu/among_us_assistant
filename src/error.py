class NotAttendeeError(Exception):
    def __init__(self, name):
        self.name = name
    def __str__(self):
        return f"{self.name} is not attendee."
    pass


class DuplicateRoleError(Exception):
    def __str__(self):
        return "duplicate role."
    pass


class NoSuchRelationError(Exception):
    def __str__(self):
        return "no such relation."
    pass

class SpecifyYourselfError(Exception):
    def __str__(self):
        return "don't specify yourself as a target."

class NoPlayerError(Exception):
    def __str__(self):
        return "there's no players in the graph."
