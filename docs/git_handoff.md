# GitHub Handoff

Repository:

```text
https://github.com/proteinskimmer/supermap-visual-navigation
```

## Branch Map

```text
main                         stable baseline
develop                      team integration branch
codex/v0.5-development       Codex working branch with historical checkpoints
```

Stable tags:

```text
v0.4
v0.5
v0.6
```

## First Clone

```powershell
git clone https://github.com/proteinskimmer/supermap-visual-navigation.git
cd supermap-visual-navigation
git checkout develop
```

Then follow:

```text
docs/deploy_one_click.md
```

## Important Local Files

Some files are local or generated and should not be assumed to exist after cloning:

- SuperMap published service registry;
- local iServer accounts/license state;
- generated evidence image batches;
- large raw GIS inputs;
- `frontend/public/vendor/supermap3d` if the SDK was not copied.

Run `INSTALL_DEMO.bat` on a new machine to prepare dependencies and SDK resources.

## Before Taking Over

Read:

```text
CONTRIBUTING.md
docs/team_workflow.md
docs/project_management/12_project_status_log.md
```

Then confirm the current demo state with:

```powershell
npm run build
E:\anaconda\envs\supermap_nav\python.exe -m pytest backend/tests
```
