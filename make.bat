@echo off
set CMD=%1
if "%CMD%"=="" set CMD=up

if "%CMD%"=="up" (
    docker compose up -d
) else if "%CMD%"=="down" (
    docker compose down
) else if "%CMD%"=="restart" (
    docker compose down && docker compose up -d
) else if "%CMD%"=="test" (
    docker compose run --rm backend pytest -v
    if errorlevel 1 exit /b 1
    docker compose run --rm worker pytest -v
    if errorlevel 1 exit /b 1
    docker compose run --rm frontend npm test
    if errorlevel 1 exit /b 1
) else if "%CMD%"=="lint" (
    docker compose run --rm backend ruff check .
    if errorlevel 1 exit /b 1
    docker compose run --rm worker ruff check .
    if errorlevel 1 exit /b 1
    docker compose run --rm frontend npm run lint
    if errorlevel 1 exit /b 1
) else if "%CMD%"=="migrate" (
    docker compose run --rm backend alembic upgrade head
) else (
    echo Unknown target: %CMD%
    exit /b 1
)
