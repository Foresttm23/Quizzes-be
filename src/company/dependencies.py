from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi_limiter.depends import RateLimiter

from core.dependencies import DBSessionDep
from .repository import (
    CompanyRepository,
    InvitationRepository,
    JoinRequestRepository,
    MemberRepository,
)
from .service import (
    CompanyService,
    InvitationService,
    JoinRequestService,
    MemberService,
)

CompanyLimitDep = Depends(RateLimiter(times=20, seconds=60))
InvLimitDep = Depends(RateLimiter(times=20, seconds=60))
ReqLimitDep = Depends(RateLimiter(times=20, seconds=60))


async def get_company_member_service(
    member_repo: MemberRepositoryDep,
) -> MemberService:
    return MemberService(member_repo=member_repo)


CompanyMemberServiceDep = Annotated[MemberService, Depends(get_company_member_service)]


async def get_company_service(
    company_repo: CompanyRepositoryDep, member_service: CompanyMemberServiceDep
) -> CompanyService:
    return CompanyService(company_repo=company_repo, member_service=member_service)


CompanyServiceDep = Annotated[CompanyService, Depends(get_company_service)]


async def get_company_join_request_service(
    join_request_repo: JoinRequestRepositoryDep, member_service: CompanyMemberServiceDep
) -> JoinRequestService:
    return JoinRequestService(
        join_request_repo=join_request_repo, member_service=member_service
    )


CompanyJoinRequestServiceDep = Annotated[
    JoinRequestService, Depends(get_company_join_request_service)
]


async def get_company_invitation_service(
    invitation_repo: InvitationRepositoryDep, member_service: CompanyMemberServiceDep
) -> InvitationService:
    return InvitationService(
        invitation_repo=invitation_repo, member_service=member_service
    )


CompanyInvitationServiceDep = Annotated[
    InvitationService, Depends(get_company_invitation_service)
]


def get_join_request_repository(db: DBSessionDep) -> JoinRequestRepository:
    return JoinRequestRepository(db=db)


JoinRequestRepositoryDep = Annotated[
    JoinRequestRepository, Depends(get_join_request_repository)
]


def get_invitation_repository(db: DBSessionDep) -> InvitationRepository:
    return InvitationRepository(db=db)


InvitationRepositoryDep = Annotated[
    InvitationRepository, Depends(get_invitation_repository)
]


def get_company_repository(db: DBSessionDep) -> CompanyRepository:
    return CompanyRepository(db=db)


CompanyRepositoryDep = Annotated[CompanyRepository, Depends(get_company_repository)]


def get_member_repository(db: DBSessionDep) -> MemberRepository:
    return MemberRepository(db=db)


MemberRepositoryDep = Annotated[MemberRepository, Depends(get_member_repository)]
