from fastapi import FastAPI, Depends, Body, Request, Response, HTTPException
from sqlalchemy.orm import Session
from model import UserTable
from db import session
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis
import uuid
import os
import uvicorn

login = FastAPI()

login.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

redis = Redis(host="localhost", port=6379, decode_responses=True)

def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()

# 로그인 처리
@login.post("/login/")
async def search_user(response: Response, user_id: str = Body(...), password: str = Body(...), db: Session = Depends(get_db)):
    # 사용자가 입력한 user_id로 해당 유저 정보 조회
    user = db.query(UserTable).filter(UserTable.user_id == user_id).first()

    # 유저가 없거나 비밀번호가 일치하지 않는 경우
    if not user or user.password != password:
        return False

    # 로그인 성공 시 Redis에 세션 저장
    session_id = str(uuid.uuid4())  # 고유 세션 ID 생성
    session_data = {"user_id": user.user_id, "username": user.username}
    await redis.set(session_id, str(session_data))

    # 클라이언트 쿠키에 세션 ID 저장
    response.set_cookie(key="session_id", value=session_id, httponly=True)

    return {"success": True, "message": "Login successful"}

# 로그아웃 처리
@login.post("/logout/")
async def logout(request: Request, response: Response):
    # 쿠키에서 세션 ID 가져오기
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="No session found")

    # Redis에서 세션 삭제
    result = await redis.delete(session_id)
    if result == 0:
        raise HTTPException(status_code=400, detail="Invalid session_id")

    # 쿠키 삭제
    response.delete_cookie(key="session_id")

    return {"success": True, "message": "Logged out successfully"}

# 로그인 상태 확인
@login.get("/check_login/")
async def check_login(request: Request):
    # 쿠키에서 세션 ID 가져오기
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="No session found")

    # Redis에서 세션 데이터 가져오기
    session_data = await redis.get(session_id)
    if not session_data:
        raise {"success": False}

    return {"success": True, "session_id": session_id, "session_data": session_data}

if __name__ == "__login__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)