# SuperMap Low-Altitude Navigation Demo

This repository is the working prototype for the SuperMap GIS based low-altitude visual navigation and 3D simulation planning system.

Current phase:

- Mock backend APIs with FastAPI.
- Demo mission data without requiring SuperMap to be installed.
- Frontend prototype that can later replace the mock map with SuperMap iClient3D for WebGL.

## Project Layout

```text
backend/       FastAPI backend and planning/risk services
frontend/      Vue + Vite frontend prototype
demo_data/     Fixed demo mission data
docs/          Planning and project management documents
config/        SuperMap service URL configuration templates
```

## Project Status

The cross-conversation status source is:

```text
docs/project_management/12_project_status_log.md
```

Before starting a new task, read the status log first, then check:

```text
docs/project_management/08_task_board.md
```

SuperMap integration guide:

```text
docs/supermap_integration/README.md
```

Delivery material drafts:

```text
docs/delivery/README.md
```

## Quick Start

Backend:

```powershell
& 'E:\anaconda\Scripts\conda.exe' env create -f environment.yml
.\scripts\start_backend.ps1
```

The recommended backend environment is the dedicated Conda environment `supermap_nav`. Do not install backend packages into the global Python environment or Anaconda base.

Frontend:

```powershell
cd frontend
npm install
npm run dev
```

Open the frontend URL printed by Vite. By default, the frontend calls `http://localhost:8000/api`.

Frontend dependencies are installed only inside `frontend\node_modules`.

## Current Mock Features

- Task and layer APIs.
- A* based demo route planning.
- Route risk scoring and elevation profile output.
- Temporary risk zone and dynamic replanning API.
- Precomputed visual matching result API.
- Vue mock dashboard for mission, routes, risks, simulation events, and visual matching.
