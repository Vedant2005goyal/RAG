from pydantic import BaseModel, ConfigDict, Field, AliasPath

class GithubData(BaseModel):
    model_config=ConfigDict(extra="ignore")
    number:int 
    title:str 
    user:str=Field(validation_alias=AliasPath("user", "login"))
    html_url:str
    created_at:str
    closed_at:str
    body:str

class GithubIssues(GithubData):
    source_type:str="issue"

class GithubPR(GithubData):
    source_type:str="pull_request"
    merged_at:str
    merge_commit_sha:str
    
