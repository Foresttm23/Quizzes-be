from uuid import UUID

from fastapi import APIRouter, status, Query

from app.core.dependencies import LocalJWTDep, CompanyServiceDep
from app.schemas.company_schemas.company_request_schema import CompanyCreateRequest, CompanyUpdateInfoRequest
from app.schemas.company_schemas.company_response_schema import CompanyListResponse, CompanyDetailsResponse

router = APIRouter(prefix="/companies", tags=["Companies"])


@router.post("/", response_model=CompanyDetailsResponse, status_code=status.HTTP_201_CREATED)
async def create_company(company_service: CompanyServiceDep, jwt_payload: LocalJWTDep,
                         company_info: CompanyCreateRequest):
    """
    Creates a company for authenticated user.
    This user is owner of the created company.
    """
    company_info = await company_service.create_company(owner_id=jwt_payload["id"], company_info=company_info)
    return company_info


@router.get("/", response_model=CompanyListResponse, status_code=status.HTTP_200_OK)
async def list_companies(company_service: CompanyServiceDep, page: int = Query(ge=1), page_size: int = Query(ge=1)):
    """
    Return a list of all companies by page and page_size.
    Filters can be added later.
    Crud operations in company_repository supports it.
    """
    companies_data = await company_service.fetch_companies_data_paginated(page=page, page_size=page_size)
    return companies_data


@router.get("/{company_id}", response_model=CompanyDetailsResponse, status_code=status.HTTP_200_OK)
async def get_company(company_service: CompanyServiceDep, company_id: UUID):
    """Returns a company by its id"""
    company = await company_service.fetch_company_by_id(company_id=company_id)
    return company


@router.patch("/{company_id}", response_model=CompanyDetailsResponse, status_code=status.HTTP_200_OK)
async def update_company(company_service: CompanyServiceDep, jwt_payload: LocalJWTDep, company_id: UUID,
                         new_company_info: CompanyUpdateInfoRequest):
    """
    Updates a company by its id,
    if company.owner_id is equal to the currently authenticated user id.
    """
    updated_company = await company_service.update_company(company_id=company_id, owner_id=jwt_payload["id"],
                                                           company_info=new_company_info)
    return updated_company


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(company_service: CompanyServiceDep, jwt_payload: LocalJWTDep, company_id: UUID):
    """
    Deletes a company by its id,
    if company.owner_id is equal to the currently authenticated user id.
    """
    await company_service.delete_company(company_id=company_id, owner_id=jwt_payload["id"])
