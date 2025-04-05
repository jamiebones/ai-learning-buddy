from pydantic import BaseModel, EmailStr, UUID4

class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: UUID4 
    
    class Config:
        from_attributes = True 