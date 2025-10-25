from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class File(BaseModel):
    """File to be created or modified"""
    model_config = ConfigDict(extra='forbid')
    
    path: str = Field(description="The path to the file to be created or modified")
    purpose: str = Field(description="The purpose of the file, e.g. 'main application logic', 'data processing module', etc.")
    

class Plan(BaseModel):
    """Plan for the application to be built"""
    model_config = ConfigDict(extra='forbid')
    
    name: str = Field(description="The name of app to be built")
    description: str = Field(description="A oneline description of the app to be built, e.g. 'A web application for managing personal finances'")
    techstack: str = Field(description="The tech stack to be used for the app, e.g. 'python', 'javascript', 'react', 'flask', etc.")
    features: list[str] = Field(description="A list of features that the app should have, e.g. 'user authentication', 'data visualization', etc.")
    files: list[File] = Field(description="A list of files to be created, each with a 'path' and 'purpose'")


class ImplementationTask(BaseModel):
    """Individual implementation task"""
    model_config = ConfigDict(extra='forbid')
    
    filepath: str = Field(description="The path to the file to be modified")
    task_description: str = Field(description="A detailed description of the task to be performed on the file, e.g. 'add user authentication', 'implement data processing logic', etc.")


class TaskPlan(BaseModel):
    """Plan containing all implementation tasks"""
    model_config = ConfigDict(extra='forbid')
    
    plan: Optional[Plan] = Field(None, description="The original plan")
    implementation_steps: list[ImplementationTask] = Field(description="A list of steps to be taken to implement the task")
    

class CoderState(BaseModel):
    """State for the coder agent"""
    model_config = ConfigDict(extra='forbid')
    
    task_plan: TaskPlan = Field(description="The plan for the task to be implemented")
    current_step_idx: int = Field(default=0, description="The index of the current step in the implementation steps")
    current_file_content: Optional[str] = Field(default=None, description="The content of the file currently being edited or created")
    project_root: Optional[str] = Field(default=None, description="The root directory for the project")