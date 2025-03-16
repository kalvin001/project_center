from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import timedelta
import os
import uuid
import aiofiles

from app.core.security import verify_password, create_access_token, get_password_hash
from app.core.config import settings
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserResponse, UserUpdate
from app.api.deps import get_current_active_user

router = APIRouter()


@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """用户登录获取令牌"""
    # 查询用户
    result = await db.execute(
        select(User).where(User.username == form_data.username)
    )
    user = result.scalars().first()
    
    # 验证用户和密码
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="账户已禁用",
        )
    
    # 生成访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """用户注册"""
    # 检查用户名是否已存在
    result = await db.execute(select(User).where(User.username == user_in.username))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已被使用",
        )
    
    # 检查电子邮件是否已存在
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="电子邮件已被使用",
        )
    
    # 创建新用户
    db_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        is_active=True,
        is_admin=False,  # 默认非管理员
    )
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    return db_user


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_active_user),
):
    """获取当前用户信息"""
    return current_user


@router.put("/update", response_model=UserResponse)
async def update_user(
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新用户信息"""
    # 更新用户对象
    if user_update.username is not None:
        current_user.username = user_update.username
    if user_update.email is not None:
        current_user.email = user_update.email
    if user_update.password is not None:
        current_user.hashed_password = get_password_hash(user_update.password)
    if user_update.avatar_url is not None:
        current_user.avatar_url = user_update.avatar_url
    
    # 只有管理员可以更改这些字段
    if current_user.is_admin:
        if user_update.is_active is not None:
            current_user.is_active = user_update.is_active
        if user_update.is_admin is not None:
            current_user.is_admin = user_update.is_admin
    
    # 保存更改
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    
    return current_user


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """修改密码"""
    if not verify_password(password_data.get("current_password"), current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前密码不正确",
        )
    
    if password_data.get("new_password") != password_data.get("confirm_password"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码与确认密码不匹配",
        )
    
    current_user.hashed_password = get_password_hash(password_data.get("new_password"))
    db.add(current_user)
    await db.commit()
    
    return {"message": "密码已成功更新"}


@router.post("/upload-avatar", response_model=UserResponse)
async def upload_avatar(
    avatar: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """上传用户头像"""
    # 检查文件类型
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if avatar.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不支持的文件类型，只允许上传JPEG、PNG、GIF或WEBP图片",
        )
    
    # 创建保存目录
    upload_dir = os.path.join("static", "avatars")
    os.makedirs(upload_dir, exist_ok=True)
    
    # 生成唯一文件名
    file_extension = os.path.splitext(avatar.filename)[1]
    unique_filename = f"{uuid.uuid4().hex}{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # 保存文件
    async with aiofiles.open(file_path, "wb") as out_file:
        content = await avatar.read()
        await out_file.write(content)
    
    # 更新用户的头像URL
    avatar_url = f"/static/avatars/{unique_filename}"
    current_user.avatar_url = avatar_url
    
    # 保存更改
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    
    return current_user 