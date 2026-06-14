# Team Contribution Guide

This repository is the shared workspace for the SuperMap visual autonomous navigation demo.

## Branches

- `main`: stable demo baseline. Keep it runnable.
- `develop`: integration branch for accepted team work.
- `feature/vision-*`: visual localization and matching work.
- `feature/frontend-*`: UI and interaction work.
- `feature/supermap-*`: GIS data, SuperMap service, and scene work.
- `feature/docs-*`: documentation, report, PPT, and presentation work.

Do not commit directly to `main`. Open a pull request into `develop`.

## Before You Commit

Run the checks relevant to your change:

```powershell
cd E:\supermap_project\frontend
npm run build
```

```powershell
cd E:\supermap_project
E:\anaconda\envs\supermap_nav\python.exe -m pytest backend/tests
```

For SuperMap evidence:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check_supermap_goal_evidence.ps1 -Strict
```

## Artifact Policy

Commit:

- source code;
- small config files;
- documentation;
- small curated demo JSON.

Do not casually commit:

- generated UAV frame caches;
- generated OpenCV evidence batches;
- videos;
- raw large GIS datasets;
- local SuperMap binary workspaces;
- `node_modules`;
- local environment folders.

Large evidence or delivery assets should be shared through GitHub Releases, cloud storage, or a separately agreed artifact package.

## Commit Message Style

Use clear short messages:

```text
Improve visual frame synchronization
Add SuperMap deployment checker
Document v0.6 demo handoff
```

## Pull Request Expectations

Every PR should include:

- what changed;
- how it was tested;
- whether generated artifacts were intentionally included;
- screenshots when UI or SuperMap scene appearance changed.
