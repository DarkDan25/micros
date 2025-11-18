from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from ..services.movie_service import MovieService
from ..models.movie import (
    MoviesListResponse, ScheduleListResponse, OrderRequest,
    OrderResponse, ScheduleUpdateRequest, UpdateMovieRequest
)

movie_router = APIRouter(prefix='/movies', tags=['Movies'])

@movie_router.get('/', response_model=MoviesListResponse)
def get_all_movies(
    movie_service: MovieService = Depends(MovieService)
):
    try:
        movies = movie_service.get_all_movies()
        return MoviesListResponse(movies=movies)
    except Exception as e:
        raise HTTPException(500, f"Internal server error: {str(e)}")

@movie_router.get('/schedule', response_model=ScheduleListResponse)
def get_schedule(
    movie_id: UUID = Query(None, description="ID фильма для фильтрации"),
    movie_service: MovieService = Depends(MovieService)
):
    try:
        schedule = movie_service.get_movie_schedule(movie_id)
        return ScheduleListResponse(schedule=schedule)
    except Exception as e:
        raise HTTPException(500, f"Internal server error: {str(e)}")

@movie_router.post('/order', response_model=OrderResponse)
def create_order(
    request: OrderRequest,
    movie_service: MovieService = Depends(MovieService)
):
    try:
        return movie_service.create_order(request)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except KeyError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Internal server error: {str(e)}")

@movie_router.put('/admin/schedule/{session_id}')
def update_schedule(
    session_id: UUID,
    request: ScheduleUpdateRequest,
    movie_service: MovieService = Depends(MovieService)
):
    try:
        return movie_service.update_schedule(session_id, request)
    except KeyError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Internal server error: {str(e)}")

@movie_router.get('/{movie_id}')
def get_movie(
    movie_id: UUID,
    movie_service: MovieService = Depends(MovieService)
):
    try:
        return movie_service.get_movie_by_id(movie_id)
    except KeyError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Internal server error: {str(e)}")

@movie_router.get('/sessions/{session_id}')
def get_session(
    session_id: UUID,
    movie_service: MovieService = Depends(MovieService)
):
    try:
        return movie_service.get_session_by_id(session_id)
    except KeyError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Internal server error: {str(e)}")

@movie_router.put('/admin/movies/{movie_id}')
def update_movie(
    movie_id: UUID,
    request: UpdateMovieRequest,
    movie_service: MovieService = Depends(MovieService)
):
    try:
        return movie_service.update_movie(movie_id, request)
    except KeyError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Internal server error: {str(e)}")