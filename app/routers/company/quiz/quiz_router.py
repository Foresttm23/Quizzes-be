from uuid import UUID

from fastapi import APIRouter, status, Query
from pydantic import TypeAdapter

from app.core.config import settings
from app.core.dependencies import (GetUserJWTDep, CompanyQuizServiceDep, GetOptionalUserJWTDep, )
from app.schemas.base_schemas import PaginationResponse
from app.schemas.company.quiz.question_schema import (QuestionUserResponseSchema, QuestionUpdateRequestSchema,
                                                      QuestionAdminResponseSchema, QuestionCreateRequestSchema, )
from app.schemas.company.quiz.quiz_schema import (QuizCreateRequestSchema, QuizDetailsResponseSchema,
                                                  QuizUpdateRequestSchema, )

router = APIRouter(prefix="/company-quizzes", tags=["Company Quizzes"])


@router.post("/{company_id}/quiz", response_model=QuizDetailsResponseSchema, status_code=status.HTTP_201_CREATED, )
async def create_company_quiz(quiz_service: CompanyQuizServiceDep, user: GetUserJWTDep, company_id: UUID,
                              quiz_info: QuizCreateRequestSchema, ):
    quiz = await quiz_service.create_quiz(company_id=company_id, acting_user_id=user.id, quiz_info=quiz_info)
    return quiz


@router.patch("/{company_id}/{quiz_id}/publish", response_model=QuizDetailsResponseSchema,
              status_code=status.HTTP_200_OK, )
async def publish_quiz(quiz_service: CompanyQuizServiceDep, user: GetUserJWTDep, company_id: UUID, quiz_id: UUID, ):
    quiz = await quiz_service.publish_quiz(company_id=company_id, acting_user_id=user.id, quiz_id=quiz_id)
    return quiz


@router.delete("/{company_id}/{quiz_id}/quiz", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company_quiz(quiz_service: CompanyQuizServiceDep, user: GetUserJWTDep, company_id: UUID,
                              quiz_id: UUID, ):
    await quiz_service.delete_quiz(company_id=company_id, quiz_id=quiz_id, acting_user_id=user.id)


@router.get("/{company_id}/{quiz_id}/quiz", response_model=QuizDetailsResponseSchema, status_code=status.HTTP_200_OK, )
async def get_quiz(quiz_service: CompanyQuizServiceDep, user: GetOptionalUserJWTDep, company_id: UUID, quiz_id: UUID):
    user_id = user.id if user else None
    quiz = await quiz_service.get_quiz(company_id=company_id, user_id=user_id, quiz_id=quiz_id)
    return quiz


@router.get("/{company_id}/quizzes", response_model=PaginationResponse[QuizDetailsResponseSchema],
            status_code=status.HTTP_200_OK, )
async def get_quizzes(quiz_service: CompanyQuizServiceDep, user: GetOptionalUserJWTDep, company_id: UUID,
                      page: int = Query(default=1, ge=1),
                      page_size: int = Query(default=10, ge=1, le=settings.APP.MAX_PAGE_SIZE), ):
    user_id = user.id if user else None
    quizzes = await quiz_service.get_quizzes_paginated(company_id=company_id, page=page, page_size=page_size,
                                                       user_id=user_id)
    return quizzes


@router.patch("/{company_id}/{quiz_id}/quiz", response_model=QuizDetailsResponseSchema,
              status_code=status.HTTP_200_OK, )
async def update_quiz(quiz_service: CompanyQuizServiceDep, user: GetUserJWTDep, company_id: UUID, quiz_id: UUID,
                      quiz_info: QuizUpdateRequestSchema, ):
    quiz = await quiz_service.update_quiz(company_id=company_id, acting_user_id=user.id, quiz_id=quiz_id,
                                          quiz_info=quiz_info, )
    return quiz


@router.post("/{company_id}/{quiz_id}/question",
             response_model=QuestionUserResponseSchema | QuestionAdminResponseSchema,
             status_code=status.HTTP_201_CREATED, )
async def create_question(quiz_service: CompanyQuizServiceDep, user: GetUserJWTDep, company_id: UUID, quiz_id: UUID,
                          question_info: QuestionCreateRequestSchema, ):
    question = await quiz_service.create_question(company_id=company_id, acting_user_id=user.id, quiz_id=quiz_id,
                                                  question_info=question_info, )
    return question


@router.delete("/{company_id}/{quiz_id}/{question_id}/question", status_code=status.HTTP_204_NO_CONTENT, )
async def delete_question(quiz_service: CompanyQuizServiceDep, user: GetUserJWTDep, company_id: UUID, quiz_id: UUID,
                          question_id: UUID, ):
    await quiz_service.delete_question(company_id=company_id, acting_user_id=user.id, quiz_id=quiz_id,
                                       question_id=question_id, )


@router.get("/{company_id}/{quiz_id}/questions",
            response_model=list[QuestionAdminResponseSchema] | list[QuestionUserResponseSchema],
            status_code=status.HTTP_200_OK, )
async def get_questions(quiz_service: CompanyQuizServiceDep, user: GetUserJWTDep, company_id: UUID, quiz_id: UUID, ):
    questions = await quiz_service.get_questions_and_options(company_id=company_id, quiz_id=quiz_id)

    is_admin = await quiz_service.has_admin_permission(company_id=company_id, user_id=user.id)
    if is_admin:
        return TypeAdapter(list[QuestionAdminResponseSchema]).validate_python(questions)
    else:
        return TypeAdapter(list[QuestionUserResponseSchema]).validate_python(questions)


@router.patch("/{company_id}/{quiz_id}/{question_id}/question", response_model=QuestionAdminResponseSchema,
              status_code=status.HTTP_200_OK, )
async def update_question_full(quiz_service: CompanyQuizServiceDep, user: GetUserJWTDep, company_id: UUID,
                               quiz_id: UUID, question_id: UUID, question_info: QuestionUpdateRequestSchema, ):
    question = await quiz_service.update_question(company_id=company_id, acting_user_id=user.id, quiz_id=quiz_id,
                                                  question_id=question_id, question_info=question_info)
    return question


@router.post("/{company_id}/{quiz_id}/versions", response_model=QuizDetailsResponseSchema,
             status_code=status.HTTP_201_CREATED, )
async def create_new_quiz_version_within_company(quiz_service: CompanyQuizServiceDep, user: GetUserJWTDep,
                                                 company_id: UUID, quiz_id: UUID):
    quiz = await quiz_service.create_new_version_within_company(company_id=company_id, acting_user_id=user.id,
                                                                curr_quiz_id=quiz_id)
    return quiz
