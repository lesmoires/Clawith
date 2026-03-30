"""Authentication API routes."""

import uuid
from datetime import datetime, timezone

from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_authenticated_user, get_current_user, hash_password, verify_password
from app.database import get_db
from app.models.user import User
from app.schemas.schemas import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    IdentityBindRequest,
    IdentityUnbindRequest,
    OAuthAuthorizeResponse,
    OAuthCallbackRequest,
    TokenResponse,
    UserLogin,
    UserOut,
    UserRegister,
    UserUpdate,
    VerifyEmailRequest,
    ResendVerificationRequest,
    NeedsVerificationResponse,
    RegisterInitRequest,
    RegisterInitResponse,
    RegisterCompleteRequest,
    RegisterCompleteResponse,
    SSORegisterRequest,
    TenantChoice,
    MultiTenantResponse,
)
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/registration-config")
async def get_registration_config(db: AsyncSession = Depends(get_db)):
    """Public endpoint — returns registration requirements (no auth needed)."""
    from app.models.system_settings import SystemSetting
    result = await db.execute(select(SystemSetting).where(SystemSetting.key == "invitation_code_enabled"))
    setting = result.scalar_one_or_none()
    enabled = setting.value.get("enabled", False) if setting else False
    return {"invitation_code_required": enabled}


@router.get("/check-duplicate")
async def check_duplicate(
    email: str | None = Query(None, description="Email to check"),
    username: str | None = Query(None, description="Username to check"),
    db: AsyncSession = Depends(get_db),
):
    """Check if email or username already exists."""
    result = {"email_exists": False, "username_exists": False, "conflicts": []}

    if email:
        # Check email - use exact match (case-insensitive)
        existing = await db.execute(
            select(User).where(User.email.ilike(email))
        )
        if existing.scalar_one_or_none():
            result["email_exists"] = True
            result["conflicts"].append({"type": "email", "message": "Email already registered"})

    if username:
        existing = await db.execute(select(User).where(User.username == username))
        if existing.scalar_one_or_none():
            result["username_exists"] = True
            result["conflicts"].append({"type": "username", "message": "Username already taken"})

    result["has_conflict"] = result["email_exists"] or result["username_exists"]
    return result


async def _send_verification_email_task(
    user: User,
    background_tasks: BackgroundTasks,
    settings: Any,
) -> None:
    """Helper to create verification token and add email task to background tasks."""
    if not settings.SYSTEM_SMTP_HOST or not settings.SYSTEM_EMAIL_FROM_ADDRESS:
        return

    from app.services.email_verification_service import (
        create_email_verification_token,
        build_email_verification_url,
        send_verification_email,
    )

    try:
        raw_code, expires_at = await create_email_verification_token(user.id, user.email)
        expiry_minutes = int((expires_at - datetime.now(timezone.utc)).total_seconds() // 60)

        background_tasks.add_task(
            send_verification_email,
            user.email,
            user.display_name or user.username,
            raw_code,
            expiry_minutes,
            tenant_id=user.tenant_id,
        )
    except Exception as exc:
        logger.warning(f"Failed to send verification email for {user.email}: {exc}")


@router.post("/register", response_model=Any, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserRegister,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Legacy registration endpoint - kept for backward compatibility.

    For new implementations, use:
    - /register/init - Step 1: Initialize registration
    - /register/sso - SSO registration
    - /verify-email - Step 3: Verify email
    """
    from app.config import get_settings
    settings = get_settings()

    # Handle SSO registration if provider info provided
    if data.provider and data.provider_code:
        return await _handle_sso_register(data, db)

    # Regular username/password registration - delegate to new flow
    return await _handle_normal_register(data, background_tasks, db, settings)


@router.post("/register/init", response_model=RegisterInitResponse, status_code=status.HTTP_201_CREATED)
async def register_init(
    data: RegisterInitRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Step 1: Initialize registration with account credentials.

    Creates a new user with email_verified=False and no tenant.
    Returns a temporary token for company selection.
    """
    from app.config import get_settings
    settings = get_settings()
    from app.services.registration_service import registration_service

    logger.info(f"[REGISTER_INIT] Starting registration for email={data.email}")

    # Check if this is the first user (platform admin setup)
    from sqlalchemy import func
    user_count_result = await db.execute(select(func.count()).select_from(User))
    is_first_user = user_count_result.scalar() == 0
    logger.info(f"[REGISTER_INIT] is_first_user={is_first_user}")

    # Check if email already exists (any tenant or no tenant)
    existing_query = select(User).where(User.email.ilike(data.email))
    existing_result = await db.execute(existing_query)
    existing_user = existing_result.scalar_one_or_none()

    if existing_user:
        logger.info(f"[REGISTER_INIT] Email exists: email_verified={existing_user.email_verified}")
        if not existing_user.email_verified:
            # Verify password if user exists
            if not verify_password(data.password, existing_user.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Email already registered. Incorrect password."
                )

            # Resend verification for unverified user
            await _send_verification_email_task(existing_user, background_tasks, settings)
            # Return token for company selection
            token = create_access_token(str(existing_user.id), existing_user.role)
            return RegisterInitResponse(
                user_id=existing_user.id,
                email=existing_user.email,
                access_token=token,
                user=UserOut.model_validate(existing_user),
                message="Email already registered but not verified. Verification code resent.",
                needs_company_setup=existing_user.tenant_id is None,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered and verified"
            )

    # Determine role
    role = "platform_admin" if is_first_user else "member"

    # For first user: auto-create default tenant
    tenant_uuid = None
    if is_first_user:
        from app.models.tenant import Tenant
        default = await db.execute(select(Tenant).where(Tenant.slug == "default"))
        tenant = default.scalar_one_or_none()
        if not tenant:
            tenant = Tenant(name="Default", slug="default", im_provider="web_only")
            db.add(tenant)
            await db.flush()
        tenant_uuid = tenant.id
        logger.info(f"[REGISTER_INIT] First user - assigned to default tenant={tenant_uuid}")

    logger.info(f"[REGISTER_INIT] Creating user: role={role}, tenant_id={tenant_uuid}")

    # Create user (unverified, no tenant for non-first users)
    user = User(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
        display_name=data.display_name or data.username,
        role=role,
        tenant_id=tenant_uuid,  # Only first user gets tenant immediately
        is_active=False,  # Inactive until email verified
        email_verified=False,
    )
    db.add(user)
    await db.flush()
    logger.info(f"[REGISTER_INIT] User created: user_id={user.id}")

    # Create Participant identity
    from app.models.participant import Participant
    db.add(Participant(
        type="user", ref_id=user.id,
        display_name=user.display_name, avatar_url=user.avatar_url,
    ))
    await db.flush()

    # Seed default agents for first user
    if is_first_user:
        await db.commit()
        try:
            from app.services.agent_seeder import seed_default_agents
            await seed_default_agents()
        except Exception as e:
            logger.warning(f"Failed to seed default agents: {e}")

    # Generate temporary token for company selection
    token = create_access_token(str(user.id), user.role)

    # Send verification email
    await _send_verification_email_task(user, background_tasks, settings)
    logger.info(f"[REGISTER_INIT] Verification email sent to {user.email}")

    return RegisterInitResponse(
        user_id=user.id,
        email=user.email,
        access_token=token,
        user=UserOut.model_validate(user),
        message="Registration initiated. Please check your email for verification code.",
        needs_company_setup=user.tenant_id is None,
    )


@router.post("/register/sso", response_model=TokenResponse)
async def register_sso(
    data: SSORegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """SSO registration - completely separate from normal registration flow.

    This endpoint handles OAuth-based registration/login via external providers.
    """
    from app.services.auth_registry import auth_provider_registry
    from app.services.registration_service import registration_service

    logger.info(f"[REGISTER_SSO] Starting SSO registration: provider={data.provider}")

    # Get provider
    auth_provider = await auth_provider_registry.get_provider(db, data.provider)
    if not auth_provider:
        raise HTTPException(status_code=400, detail=f"Provider '{data.provider}' not supported")

    # Perform SSO registration
    user, is_new, error = await registration_service.register_with_sso(
        db, data.provider, data.code, auth_provider
    )

    if error:
        raise HTTPException(status_code=400, detail=error)

    # If no tenant, check for email domain match
    if not user.tenant_id and user.email:
        tenant, _ = await registration_service.get_tenant_for_registration(
            db, email=user.email, invitation_code=data.invitation_code
        )
        if tenant:
            user.tenant_id = tenant.id
            await db.flush()

    # Generate token
    token = create_access_token(str(user.id), user.role)

    logger.info(f"[REGISTER_SSO] SSO successful: user_id={user.id}, is_new={is_new}")

    return TokenResponse(
        access_token=token,
        user=UserOut.model_validate(user),
        needs_company_setup=user.tenant_id is None,
    )


async def _handle_normal_register(data: UserRegister, background_tasks: BackgroundTasks, db: AsyncSession, settings):
    """Legacy normal registration handler."""
    logger.info(f"[REGISTER_LEGACY] email={data.email}")

    from app.services.registration_service import registration_service
    from sqlalchemy import func

    # Check if first user
    user_count_result = await db.execute(select(func.count()).select_from(User))
    is_first_user = user_count_result.scalar() == 0

    # Resolve tenant
    tenant_uuid = None
    if is_first_user:
        from app.models.tenant import Tenant
        default = await db.execute(select(Tenant).where(Tenant.slug == "default"))
        tenant = default.scalar_one_or_none()
        if not tenant:
            tenant = Tenant(name="Default", slug="default", im_provider="web_only")
            db.add(tenant)
            await db.flush()
        tenant_uuid = tenant.id
        role = "platform_admin"
    else:
        tenant, _ = await registration_service.get_tenant_for_registration(
            db, email=data.email, invitation_code=data.invitation_code
        )
        if tenant:
            tenant_uuid = tenant.id
        role = "member"

    # Check for existing user in same tenant
    existing_query = select(User).where(
        User.email.ilike(data.email),
        User.tenant_id == tenant_uuid
    )
    existing_result = await db.execute(existing_query)
    existing_user = existing_result.scalar_one_or_none()

    if existing_user:
        if not existing_user.email_verified:
            # Verify password
            if not verify_password(data.password, existing_user.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Email already registered. Incorrect password."
                )
            
            await _send_verification_email_task(existing_user, background_tasks, settings)
            # Return token for company selection (requirement: allow self_create/join even if unverified)
            token = create_access_token(str(existing_user.id), existing_user.role)
            return RegisterInitResponse(
                user_id=existing_user.id,
                email=existing_user.email,
                access_token=token,
                user=UserOut.model_validate(existing_user),
                message="Email already registered but not verified. Verification code resent.",
                needs_company_setup=existing_user.tenant_id is None,
            )
        else:
            raise HTTPException(status_code=409, detail="Email already registered")

    # Create user
    is_active = is_first_user
    user = User(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
        display_name=data.display_name or data.username,
        role=role,
        tenant_id=tenant_uuid,
        is_active=is_active,
        email_verified=False,
    )
    db.add(user)
    await db.flush()

    # Create Participant
    from app.models.participant import Participant
    db.add(Participant(
        type="user", ref_id=user.id,
        display_name=user.display_name, avatar_url=user.avatar_url,
    ))
    await db.flush()

    # Seed default agents for first user
    if is_first_user:
        await db.commit()
        try:
            from app.services.agent_seeder import seed_default_agents
            await seed_default_agents()
        except Exception as e:
            logger.warning(f"Failed to seed default agents: {e}")

    # Send verification email
    await _send_verification_email_task(user, background_tasks, settings)

    return RegisterInitResponse(
        user_id=user.id,
        email=user.email,
        access_token=create_access_token(str(user.id), user.role),
        user=UserOut.model_validate(user),
        message="Registration successful. Please verify your email.",
        needs_company_setup=user.tenant_id is None,
    )


async def _handle_sso_register(data: UserRegister, db: AsyncSession):
    """Legacy SSO registration handler - delegates to new SSO endpoint logic."""
    # Redirect to new SSO flow
    sso_data = SSORegisterRequest(
        provider=data.provider,
        code=data.provider_code,
        invitation_code=data.invitation_code
    )
    return await register_sso(sso_data, db)



@router.post("/login", response_model=Any)
async def login(data: UserLogin, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Login with email and password. Supports multi-tenant selection."""
    from app.models.tenant import Tenant

    # 1. Query all users by email
    query = select(User).where(User.email.ilike(data.login_identifier))
    result = await db.execute(query)
    all_users = list(result.scalars().all())

    if not all_users:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # 2. Filter users with matching passwords
    valid_users = [u for u in all_users if verify_password(data.password, u.password_hash)]
    if not valid_users:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")


    # 4. Check for usable accounts (at least one must be active or unverified)
    if not any(u.is_active or not u.email_verified for u in valid_users):
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your account has been disabled.")

    # 5. Handle Tenant Selection and Company Setup (Requirement 1)
    if not data.tenant_id:
        # If multiple accounts exist (including one with tenant_id=None), return selection list
        if len(valid_users) > 1:
            tenant_ids = [u.tenant_id for u in valid_users if u.tenant_id]
            tenants_map = {}
            if tenant_ids:
                tenants_result = await db.execute(
                    select(Tenant).where(Tenant.id.in_(tenant_ids))
                )
                tenants_map = {str(t.id): t for t in tenants_result.scalars().all()}

            tenant_choices = []
            for u in valid_users:
                tenant = tenants_map.get(str(u.tenant_id)) if u.tenant_id else None
                tenant_choices.append(TenantChoice(
                    tenant_id=u.tenant_id,
                    tenant_name=tenant.name if tenant else "Create or Join Organization",
                    tenant_slug=tenant.slug if tenant else "",
                ))

            return MultiTenantResponse(
                requires_tenant_selection=True,
                login_identifier=data.login_identifier,
                tenants=tenant_choices,
            )

        # Only one valid user found
        user = valid_users[0]
    else:
        # Specific tenant requested
        # Platform admin is allowed to log into any tenant
        is_platform_admin = any(u.role == "platform_admin" for u in valid_users)
        
        if is_platform_admin:
            # Platform admin can "impersonate" or login into specific tenants
            user = next((u for u in valid_users if u.role == "platform_admin"), valid_users[0])
            # If they chose a tenant, and they have an account in it, use that. 
            # Otherwise use their platform_admin account but acknowledge the tenant selection?
            # Actually, standard logic:
            tenant_specific_user = next((u for u in valid_users if u.tenant_id == data.tenant_id), None)
            user = tenant_specific_user or user
        else:
            user = next((u for u in valid_users if u.tenant_id == data.tenant_id), None)
            if not user:
                 raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="This account does not belong to the selected organization.",
                )

    # 6. Final checks for the selected user
    if not user.email_verified:
        from app.config import get_settings
        await _send_verification_email_task(user, background_tasks, get_settings())
        token = create_access_token(str(user.id), user.role)
        return TokenResponse(
            access_token=token,
            user=UserOut.model_validate(user),
            needs_company_setup=user.tenant_id is None,
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This specific account is disabled.")

    if user.tenant_id:
        t_result = await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))
        tenant = t_result.scalar_one_or_none()
        if tenant and not tenant.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your organization has been disabled. Please contact the platform administrator.",
            )

    # 7. Generate Token
    token = create_access_token(str(user.id), user.role)
    return TokenResponse(
        access_token=token,
        user=UserOut.model_validate(user),
        needs_company_setup=user.tenant_id is None,
    )


@router.post("/forgot-password")
async def forgot_password(
    data: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Request a password reset link without revealing account existence."""
    from app.config import get_settings
    settings = get_settings()

    if not settings.SYSTEM_SMTP_HOST or not settings.SYSTEM_EMAIL_FROM_ADDRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset is currently unavailable (no mail server configured)."
        )

    generic_response = {
        "ok": True,
        "message": "If an account with that email exists, a password reset email has been sent.",
    }

    result = await db.execute(select(User).where(User.email == data.email))
    users = result.scalars().all()
    
    if not users:
        return generic_response

    # Loop through all matching users and send reset email if active
    for user in users:
        if not user.is_active:
            continue

        try:
            from app.services.password_reset_service import build_password_reset_url, create_password_reset_token
            from app.services.system_email_service import (
                send_password_reset_email,
            )

            raw_token, expires_at = await create_password_reset_token(user.id)

            reset_url = await build_password_reset_url(db, raw_token)
            expiry_minutes = int((expires_at - datetime.now(timezone.utc)).total_seconds() // 60)
            
            background_tasks.add_task(
                send_password_reset_email,
                user.email,
                user.display_name or user.username,
                reset_url,
                expiry_minutes,
                tenant_id=user.tenant_id,
            )
        except Exception as exc:
            logger.warning(f"Failed to process password reset email for {data.email} (User ID: {user.id}): {exc}")

    return generic_response


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Reset a password using a valid single-use token."""
    from app.services.password_reset_service import consume_password_reset_token

    token = await consume_password_reset_token(data.token)
    if not token:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user_id = token["user_id"]
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    new_hash = hash_password(data.new_password)
    user.password_hash = new_hash
    
    # Sync password for all matching accounts of this email (active and inactive)
    from sqlalchemy import update
    await db.execute(
        update(User)
        .where(User.email.ilike(user.email))
        .values(password_hash=new_hash)
    )
    
    await db.flush()
    await db.commit()
    return {"ok": True}


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_authenticated_user)):
    """Get current user profile."""
    return UserOut.model_validate(current_user)


@router.patch("/me", response_model=UserOut)
async def update_me(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user profile."""
    update_data = data.model_dump(exclude_unset=True)

    # Validate username uniqueness if changing
    if "username" in update_data and update_data["username"] != current_user.username:
        existing = await db.execute(select(User).where(User.username == update_data["username"]))
        if existing.scalars().first():
            raise HTTPException(status_code=409, detail="Username already taken")

    # Validate email uniqueness within tenant if changing
    if "email" in update_data and update_data["email"] != current_user.email:
        existing = await db.execute(
            select(User).where(
                User.email.ilike(update_data["email"]),
                User.tenant_id == current_user.tenant_id,
                User.id != current_user.id,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Email already registered")

    # Validate mobile uniqueness within tenant if changing
    if "primary_mobile" in update_data and update_data["primary_mobile"] != current_user.primary_mobile:
        existing = await db.execute(
            select(User).where(
                User.primary_mobile == update_data["primary_mobile"],
                User.tenant_id == current_user.tenant_id,
                User.id != current_user.id,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Mobile already registered")

    for field, value in update_data.items():
        setattr(current_user, field, value)
    await db.flush()

    # Sync email/phone to OrgMember if changed
    if "email" in update_data or "primary_mobile" in update_data:
        from app.services.registration_service import registration_service
        await registration_service.sync_org_member_contact_from_user(
            db,
            current_user,
            sync_email="email" in update_data,
            sync_phone="primary_mobile" in update_data,
        )

    return UserOut.model_validate(current_user)


@router.put("/me/password")
async def change_password(
    data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change current user's password. Requires old_password verification."""
    old_password = data.get("old_password", "")
    new_password = data.get("new_password", "")

    if not old_password or not new_password:
        raise HTTPException(status_code=400, detail="Both old_password and new_password are required")

    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")

    if not verify_password(old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    new_hash = hash_password(new_password)
    current_user.password_hash = new_hash
    
    # Sync password for all active accounts of this email
    from sqlalchemy import update
    await db.execute(
        update(User)
        .where(User.email.ilike(current_user.email), User.is_active == True)
        .values(password_hash=new_hash)
    )
    
    await db.flush()
    await db.commit()
    return {"ok": True}


# ─── SSO/OAuth Endpoints ─────────────────────────────────────────────


@router.get("/providers")
async def list_providers(
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID | None = Query(None, description="Optional tenant ID"),
):
    """List all available identity providers."""
    from app.services.auth_registry import auth_provider_registry

    providers = await auth_provider_registry.list_providers(db, str(tenant_id) if tenant_id else None)
    return [{"id": str(p.id), "provider_type": p.provider_type, "name": p.name, "is_active": p.is_active} for p in providers]


@router.get("/{provider}/authorize", response_model=OAuthAuthorizeResponse)
async def authorize(
    provider: str,
    redirect_uri: str = Query(..., description="OAuth callback URI"),
    state: str = Query("", description="CSRF state parameter"),
    db: AsyncSession = Depends(get_db),
):
    """Start OAuth authorization flow for a provider."""
    from app.services.auth_registry import auth_provider_registry
    from app.services.sso_service import sso_service

    # Get provider
    auth_provider = await auth_provider_registry.get_provider(db, provider)
    if not auth_provider:
        raise HTTPException(status_code=404, detail=f"Provider '{provider}' not supported")

    # Generate authorization URL
    try:
        auth_url = await auth_provider.get_authorization_url(redirect_uri, state)
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to generate authorization URL for {provider}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate authorization URL")

    return OAuthAuthorizeResponse(authorization_url=auth_url)


@router.post("/{provider}/callback", response_model=TokenResponse)
async def oauth_callback(
    provider: str,
    data: OAuthCallbackRequest,
    db: AsyncSession = Depends(get_db),
):
    """Handle OAuth callback and login/register user."""
    from app.services.auth_registry import auth_provider_registry

    # Get provider
    auth_provider = await auth_provider_registry.get_provider(db, provider)
    if not auth_provider:
        raise HTTPException(status_code=404, detail=f"Provider '{provider}' not supported")

    try:
        # Exchange code for token
        token_data = await auth_provider.exchange_code_for_token(data.code)
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to get access token from provider")

        # Get user info
        user_info = await auth_provider.get_user_info(access_token)

        # Find or create user
        user, is_new = await auth_provider.find_or_create_user(db, user_info)

        if not user:
            raise HTTPException(status_code=500, detail="Failed to create user")

        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account is disabled")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth callback failed for {provider}: {e}")
        raise HTTPException(status_code=500, detail="OAuth authentication failed")

    # Generate JWT token
    jwt_token = create_access_token(str(user.id), user.role)

    return TokenResponse(
        access_token=jwt_token,
        user=UserOut.model_validate(user),
        needs_company_setup=user.tenant_id is None,
    )


@router.post("/{provider}/bind", response_model=UserOut)
async def bind_identity(
    provider: str,
    data: IdentityBindRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Bind an external identity to the current user."""
    from app.services.auth_registry import auth_provider_registry
    from app.services.sso_service import sso_service

    # Get provider
    auth_provider = await auth_provider_registry.get_provider(db, provider)
    if not auth_provider:
        raise HTTPException(status_code=404, detail=f"Provider '{provider}' not supported")

    try:
        # Exchange code for token
        token_data = await auth_provider.exchange_code_for_token(data.code)
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to get access token from provider")

        # Get user info
        user_info = await auth_provider.get_user_info(access_token)

        # Check if identity is already linked to another user
        existing_user = await sso_service.check_duplicate_identity(db, provider, user_info.provider_user_id)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=409,
                detail="This identity is already linked to another account",
            )

        # Link identity to current user
        await sso_service.link_identity(
            db,
            str(current_user.id),
            provider,
            user_info.provider_user_id,
            user_info.raw_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Identity bind failed for {provider}: {e}")
        raise HTTPException(status_code=500, detail="Failed to bind identity")

    return UserOut.model_validate(current_user)


@router.post("/{provider}/unbind", response_model=UserOut)
async def unbind_identity(
    provider: str,
    data: IdentityUnbindRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Unlink an external identity from the current user."""
    from app.services.sso_service import sso_service

    # Unlink identity
    success = await sso_service.unlink_identity(db, str(current_user.id), provider)
    if not success:
        raise HTTPException(status_code=404, detail=f"No linked identity found for provider '{provider}'")

    return UserOut.model_validate(current_user)


# ─── Email Verification Endpoints ──────────────────────────────────────


@router.post("/verify-email")
async def verify_email(data: VerifyEmailRequest, db: AsyncSession = Depends(get_db)):
    """Verify email address using a token from the verification email.

    On success, returns user info and access token to allow immediate login.
    """
    from app.services.email_verification_service import consume_email_verification_token

    token_data = await consume_email_verification_token(data.token)
    if not token_data:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")

    user_id = token_data["user_id"]
    email = token_data["email"]

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")

    # Check if email matches (case-insensitive)
    if user.email.lower() != email.lower():
        raise HTTPException(status_code=400, detail="Email mismatch")

    user.email_verified = True
    user.is_active = True
    
    # Sync password for all active accounts of this email
    from sqlalchemy import update
    await db.execute(
        update(User)
        .where(User.email.ilike(email), User.is_active == True)
        .values(password_hash=user.password_hash)
    )
    
    await db.flush()
    await db.commit()

    # Generate token for immediate login
    token = create_access_token(str(user.id), user.role)

    return {
        "ok": True,
        "message": "Email verified successfully",
        "access_token": token,
        "user": UserOut.model_validate(user),
        "needs_company_setup": user.tenant_id is None,
    }


@router.post("/resend-verification")
async def resend_verification(
    data: ResendVerificationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Resend email verification link."""
    from app.config import get_settings
    settings = get_settings()

    # Always return success to prevent email enumeration
    generic_response = {
        "ok": True,
        "message": "If an account with that email exists, a verification email has been sent.",
    }

    if not settings.SYSTEM_SMTP_HOST or not settings.SYSTEM_EMAIL_FROM_ADDRESS:
        return generic_response

    result = await db.execute(select(User).where(User.email.ilike(data.email)))
    user = result.scalar_one_or_none()

    # Don't reveal if user exists or already verified
    if not user or user.email_verified:
        return generic_response

    await _send_verification_email_task(user, background_tasks, settings)

    return generic_response
