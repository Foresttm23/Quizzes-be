from typing import Annotated

from fastapi import Depends

from src.core.dependencies import DBSessionDep
from .service import (
    CompanyService,
    InvitationService,
    JoinRequestService,
    MemberService,
)


async def get_company_member_service(db: DBSessionDep) -> MemberService:
    return MemberService(db=db)


CompanyMemberServiceDep = Annotated[MemberService, Depends(get_company_member_service)]


async def get_company_service(
    db: DBSessionDep, member_service: CompanyMemberServiceDep
) -> CompanyService:
    return CompanyService(db=db, member_service=member_service)


CompanyServiceDep = Annotated[CompanyService, Depends(get_company_service)]


async def get_company_join_request_service(
    db: DBSessionDep, member_service: CompanyMemberServiceDep
) -> JoinRequestService:
    return JoinRequestService(db=db, member_service=member_service)


CompanyJoinRequestServiceDep = Annotated[
    JoinRequestService, Depends(get_company_join_request_service)
]


async def get_company_invitation_service(
    db: DBSessionDep, member_service: CompanyMemberServiceDep
) -> InvitationService:
    return InvitationService(db=db, member_service=member_service)


CompanyInvitationServiceDep = Annotated[
    InvitationService, Depends(get_company_invitation_service)
]
