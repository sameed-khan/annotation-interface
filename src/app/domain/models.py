from dataclasses import dataclass

@dataclass
class UserData:
    request_username: str
    request_password: str

@dataclass
class AnnotationUpdate:
    task_uuid: str
    annotation_id: int
    label: str