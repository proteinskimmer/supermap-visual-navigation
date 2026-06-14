# Team Workflow

## Current Stable Baseline

The current stable Git checkpoint is:

```text
tag: v0.6
branch: main
branch: develop
```

`v0.6` includes:

- visual current-frame display fixes;
- terrain-draped online imagery preview;
- one-click deployment preparation;
- stable route safety fixes up to that checkpoint.

## Recommended Team Split

| Group | Branch Prefix | Main Work |
| --- | --- | --- |
| Vision | `feature/vision-*` | OpenCV/SIFT/AKAZE/BRISK, evidence generation, visual localization credibility |
| Frontend | `feature/frontend-*` | cockpit UI, frame panel, visualization, screenshots |
| SuperMap/GIS | `feature/supermap-*` | Luojia workspace, iServer services, terrain/orthophoto/building data |
| Docs/Delivery | `feature/docs-*` | PPT, report, demo script, acceptance checklist |

## Daily Flow

1. Pull latest `develop`.
2. Create a feature branch.
3. Make focused changes.
4. Run relevant checks.
5. Open PR into `develop`.
6. Merge after review.
7. When demo-ready, tag a new version.

Example:

```powershell
git checkout develop
git pull
git checkout -b feature/frontend-vision-panel
```

## Demo Versioning

Use tags for demo checkpoints:

```text
v0.6
v0.7
v1.0-demo
```

Each tag should correspond to a state that can be explained and, ideally, started through `START_DEMO.bat`.

## Local Setup

For a new computer:

```text
INSTALL_DEMO.bat
START_DEMO.bat
STOP_DEMO.bat
```

See:

```text
docs/deploy_one_click.md
```

## Review Checklist

Before merging into `develop`, check:

- No accidental large generated files.
- Frontend still builds.
- Backend tests pass when backend behavior changed.
- Project status log is updated for meaningful milestones.
- Demo claims remain truthful: distinguish mock/proxy, OpenCV evidence, and real SuperMap service status.
