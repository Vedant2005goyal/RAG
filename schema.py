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
    
class LocalDocument(BaseModel):
    source_uri: str
    title: str
    content: str
    chunk_index: int

class AgentResponse(BaseModel):
    incident: str
    answer: str
    sources: list[dict]

class UserQuery(BaseModel):
    model_config=ConfigDict(extra="ignore")
    query:str

class RetrievedChunk(BaseModel):
    score: float
    content: str
    source: str | None = None
    title: str | None = None
    source_type: str | None = None
    number: int | None = None

