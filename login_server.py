from fastapi import FastAPI, Depends, Body, Request
from sqlalchemy.orm import Session
from model import UserTable
from db import session
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import os
import uvicorn

login = FastAPI()

login.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False, 
    allow_methods=["*"],
    allow_headers=["*"],
)

login.add_middleware(SessionMiddleware, secret_key="your-secret-key")

def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()

# 로그인 처리
@login.post("/login/")
async def search_user(request: Request, user_id: str = Body(...), password: str = Body(...), db: Session = Depends(get_db)):
    # 사용자가 입력한 user_id로 해당 유저 정보 조회
    user = db.query(UserTable).filter(UserTable.user_id == user_id).first()

    # 유저가 없거나 비밀번호가 False반환
    if not user or user.password != password:
        return False
    
    # 로그인 성공시 세션에 사용자 정보 저장
    request.session["user_id"] = user.user_id
    request.session["username"] = user.username

    return {"user_id": user.user_id}

# 로그아웃 처리
@login.post("/logout/")
async def logout(request: Request):
    # 세션에서 사용자 정보 삭제
    request.session.clear()
    return {"message": "Logged out successfully"}

# 로그인 상태 확인
@login.get("/check_login/")
async def check_login(request: Request):
    # 세션에서 사용자 정보 확인
    if "user_id" not in request.session:
        return False
    
    return {"user_id": f"{request.session['user_id']}"}

if __name__ == "__login__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
