from uuid import UUID

from fastapi import APIRouter, status
from fastapi_cache.decorator import cache

from src.auth.dependencies import GetOptionalUserJWTDep, GetUserJWTDep
from src.company.dependencies import CompanyMemberServiceDep
from src.core.caching.keys import endpoint_key_builder
from src.core.dependencies import PaginationParamDep
from src.core.schemas import PaginationResponse

from .dependencies import (
    AttemptLimitDep,
    AttemptServiceDep,
    CompanyQuizServiceDep,
    QuizLimitDep,
)
from .schemas import (
    CompanyQuizAdminSchema,
    CompanyQuizBaseSchema,
    CompanyQuizQuestionAdminSchema,
    CompanyQuizQuestionSchema,
    CompanyQuizSchema,
    QuestionCreateRequestSchema,
    QuestionUpdateRequestSchema,
    QuizAttemptAnswerSchema,
    QuizAttemptBaseSchema,
    QuizCreateRequestSchema,
    QuizReviewAttemptResponseSchema,
    QuizStartAttemptResponseSchema,
    QuizUpdateRequestSchema,
    SaveAnswerRequestSchema,
)

attempt_router = APIRouter(
    prefix="/attempts", tags=["Quiz Attempts"], dependencies=[AttemptLimitDep]
)
quiz_router = APIRouter(
    prefix="/companies/{company_id}/quizzes",
    tags=["Company Quizzes"],
    dependencies=[QuizLimitDep],
)


@quiz_router.post(
    "/",
    response_model=CompanyQuizAdminSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_company_quiz(
    quiz_service: CompanyQuizServiceDep,
    user: GetUserJWTDep,
    company_id: UUID,
    quiz_info: QuizCreateRequestSchema,
):
    quiz = await quiz_service.create_quiz(
        company_id=company_id, acting_user_id=user.id, quiz_info=quiz_info
    )
    return quiz


@quiz_router.post(
    "/{quiz_id}/publish",
    response_model=CompanyQuizAdminSchema,
    status_code=status.HTTP_200_OK,
)
async def publish_quiz(
    quiz_service: CompanyQuizServiceDep,
    user: GetUserJWTDep,
    company_id: UUID,
    quiz_id: UUID,
):
    quiz = await quiz_service.publish_quiz(
        company_id=company_id, acting_user_id=user.id, quiz_id=quiz_id
    )
    return quiz


@quiz_router.delete("/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company_quiz(
    quiz_service: CompanyQuizServiceDep,
    user: GetUserJWTDep,
    company_id: UUID,
    quiz_id: UUID,
):
    await quiz_service.delete_quiz(
        company_id=company_id, quiz_id=quiz_id, acting_user_id=user.id
    )


@quiz_router.get(
    "/{quiz_id}",
    response_model=CompanyQuizAdminSchema | CompanyQuizSchema,
    status_code=status.HTTP_200_OK,
)
@cache(expire=600, key_builder=endpoint_key_builder)
async def get_quiz(
    member_service: CompanyMemberServiceDep,
    quiz_service: CompanyQuizServiceDep,
    user: GetOptionalUserJWTDep,
    company_id: UUID,
    quiz_id: UUID,
):
    user_id = user.id if user else None
    is_admin = await member_service.has_admin_permission(
        company_id=company_id, user_id=user_id
    )
    quiz = await quiz_service.get_quiz(
        company_id=company_id, is_admin=is_admin, quiz_id=quiz_id
    )
    # Service layer already handles schema transformation
    return quiz


@quiz_router.get(
    "/",
    response_model=PaginationResponse[CompanyQuizBaseSchema],
    status_code=status.HTTP_200_OK,
)
@cache(expire=60, key_builder=endpoint_key_builder)
async def get_quizzes(
    quiz_service: CompanyQuizServiceDep,
    user: GetOptionalUserJWTDep,
    company_id: UUID,
    pagination: PaginationParamDep,
):
    user_id = user.id if user else None
    quizzes = await quiz_service.get_quizzes_paginated(
        company_id=company_id,
        page=pagination.page,
        page_size=pagination.page_size,
        user_id=user_id,
    )
    return quizzes


@quiz_router.patch(
    "/{quiz_id}",
    response_model=CompanyQuizAdminSchema,
    status_code=status.HTTP_200_OK,
)
async def update_quiz(
    quiz_service: CompanyQuizServiceDep,
    user: GetUserJWTDep,
    company_id: UUID,
    quiz_id: UUID,
    quiz_info: QuizUpdateRequestSchema,
):
    quiz = await quiz_service.update_quiz(
        company_id=company_id,
        acting_user_id=user.id,
        quiz_id=quiz_id,
        quiz_info=quiz_info,
    )
    return quiz


@quiz_router.post(
    "/{quiz_id}/question",
    response_model=CompanyQuizQuestionAdminSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_question(
    quiz_service: CompanyQuizServiceDep,
    user: GetUserJWTDep,
    company_id: UUID,
    quiz_id: UUID,
    question_info: QuestionCreateRequestSchema,
):
    question = await quiz_service.create_question(
        company_id=company_id,
        acting_user_id=user.id,
        quiz_id=quiz_id,
        question_info=question_info,
    )
    return question


@quiz_router.delete(
    "/{quiz_id}/questions/{question_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_question(
    quiz_service: CompanyQuizServiceDep,
    user: GetUserJWTDep,
    company_id: UUID,
    quiz_id: UUID,
    question_id: UUID,
):
    await quiz_service.delete_question(
        company_id=company_id,
        acting_user_id=user.id,
        quiz_id=quiz_id,
        question_id=question_id,
    )


@quiz_router.get(
    "/{quiz_id}/questions",
    response_model=list[CompanyQuizQuestionAdminSchema]
    | list[CompanyQuizQuestionSchema],
    status_code=status.HTTP_200_OK,
)
@cache(expire=600, key_builder=endpoint_key_builder)
async def get_questions(
    quiz_service: CompanyQuizServiceDep,
    member_service: CompanyMemberServiceDep,
    user: GetUserJWTDep,
    company_id: UUID,
    quiz_id: UUID,
):
    is_admin = await member_service.has_admin_permission(
        company_id=company_id, user_id=user.id
    )
    questions = await quiz_service.get_questions_and_options(
        company_id=company_id, quiz_id=quiz_id, is_admin=is_admin
    )
    return questions


@quiz_router.patch(
    "/{quiz_id}/questions/{question_id}",
    response_model=CompanyQuizQuestionAdminSchema,
    status_code=status.HTTP_200_OK,
)
async def update_question_full(
    quiz_service: CompanyQuizServiceDep,
    user: GetUserJWTDep,
    company_id: UUID,
    quiz_id: UUID,
    question_id: UUID,
    question_info: QuestionUpdateRequestSchema,
):
    question = await quiz_service.update_question(
        company_id=company_id,
        acting_user_id=user.id,
        quiz_id=quiz_id,
        question_id=question_id,
        question_info=question_info,
    )
    return question


@quiz_router.post(
    "/{quiz_id}/versions",
    response_model=CompanyQuizAdminSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_new_quiz_version_within_company(
    quiz_service: CompanyQuizServiceDep,
    user: GetUserJWTDep,
    company_id: UUID,
    quiz_id: UUID,
):
    quiz = await quiz_service.create_new_version_within_company(
        company_id=company_id, acting_user_id=user.id, curr_quiz_id=quiz_id
    )
    return quiz


@quiz_router.post(
    "/{quiz_id}/attempts",
    response_model=QuizStartAttemptResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def start_quiz_attempt(
    attempt_service: AttemptServiceDep,
    user: GetUserJWTDep,
    company_id: UUID,
    quiz_id: UUID,
):
    questions, attempt = await attempt_service.start_attempt(
        company_id=company_id, quiz_id=quiz_id, user_id=user.id
    )
    return {"questions": questions, "attempt": attempt}


@attempt_router.post(
    "/{attempt_id}/questions/{question_id}/answer",
    response_model=QuizAttemptAnswerSchema,
    status_code=status.HTTP_200_OK,
)
async def save_quiz_answer(
    attempt_service: AttemptServiceDep,
    user: GetUserJWTDep,
    attempt_id: UUID,
    question_id: UUID,
    answer_info: SaveAnswerRequestSchema,
):
    answer = await attempt_service.save_answer(
        user_id=user.id,
        question_id=question_id,
        attempt_id=attempt_id,
        selected_option_info=answer_info,
    )
    return answer


@attempt_router.post(
    "/{attempt_id}/submit",
    response_model=QuizAttemptBaseSchema,
    status_code=status.HTTP_200_OK,
)
async def submit_quiz_attempt(
    attempt_service: AttemptServiceDep,
    user: GetUserJWTDep,
    attempt_id: UUID,
):
    return await attempt_service.submit_attempt(user_id=user.id, attempt_id=attempt_id)


@attempt_router.get(  # TODO? add router for the admin to review member answers
    "/{attempt_id}/active",
    response_model=QuizStartAttemptResponseSchema,
    status_code=status.HTTP_200_OK,
)
# Must be 'fresh', since returns user answers and active attempt that update in real time
async def get_active_attempt(
    attempt_service: AttemptServiceDep,
    user: GetUserJWTDep,
    attempt_id: UUID,
):
    # Users only access their own active attempts here; admin review mode is not enabled.
    return await attempt_service.continue_attempt(
        user_id=user.id, attempt_id=attempt_id
    )


@attempt_router.get(
    "/{attempt_id}/results",
    response_model=QuizReviewAttemptResponseSchema,
    status_code=status.HTTP_200_OK,
)
@cache(expire=600, key_builder=endpoint_key_builder)
async def get_quiz_attempt_results(
    attempt_service: AttemptServiceDep,
    user: GetUserJWTDep,
    attempt_id: UUID,
):
    # is_admin = False for now, since user cant see his attempts unless an attempt ended.
    return await attempt_service.get_attempt_results(
        user_id=user.id, attempt_id=attempt_id, is_admin=False
    )


@attempt_router.get(
    "/",
    response_model=PaginationResponse[QuizAttemptBaseSchema],
    status_code=status.HTTP_200_OK,
)
@cache(expire=60, key_builder=endpoint_key_builder)  # Critical endpoint
async def get_attempts(
    attempt_service: AttemptServiceDep,
    user: GetUserJWTDep,
    pagination: PaginationParamDep,
):
    return await attempt_service.get_user_attempts(
        user_id=user.id, page=pagination.page, page_size=pagination.page_size
    )
