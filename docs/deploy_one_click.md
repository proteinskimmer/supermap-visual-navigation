# One-click deployment guide

This guide is for moving the demo to another Windows computer.

## Recommended workflow

1. Copy the whole project folder to the target computer.

   Recommended path:

   ```text
   E:\supermap_project
   ```

   Other paths are supported because `INSTALL_DEMO.bat`, `START_DEMO.bat`, and `STOP_DEMO.bat` now resolve the project root from their own location.

2. Install prerequisite software on the target computer.

   Required:

   ```text
   Anaconda or Miniconda
   Node.js 20 LTS or 22 LTS
   SuperMap iServer 2025
   SuperMap iClient3D for WebGL/WebGPU 2025U1
   ```

   Optional, only needed when rebuilding or editing SuperMap workspaces:

   ```text
   SuperMap iDesktopX 2025
   ```

3. Double-click:

   ```text
   INSTALL_DEMO.bat
   ```

   The installer will:

   - create or update the `supermap_nav` conda environment from `environment.yml`;
   - run `npm ci` in `frontend`;
   - run `npm run build`;
   - copy iClient3D resources into `frontend/public/vendor/supermap3d` if needed;
   - check whether `supermap_file_root` and SuperMap service config exist.

4. Confirm iServer service publication.

   Open:

   ```text
   http://localhost:8090/iserver
   ```

   If this is a fresh computer, publish or verify the Luojia project workspace services. The file root should point to:

   ```text
   <project_root>\supermap_file_root
   ```

5. Double-click:

   ```text
   START_DEMO.bat
   ```

   Default app URL:

   ```text
   http://localhost:5173
   ```

6. Stop the demo with:

   ```text
   STOP_DEMO.bat
   ```

## If the target computer has no network

Use:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_demo_one_click.ps1 -NoNetwork
```

In `-NoNetwork` mode, the target computer must already have:

- conda environment `supermap_nav`;
- `frontend\node_modules`;
- iClient3D SDK already copied to `frontend\public\vendor\supermap3d`.

## Custom paths

If SuperMap software is installed in a non-default location:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_demo_one_click.ps1 `
  -IClient3DRoot "D:\supermap_software\supermap-iclient3d-for-webgl_webgpu-2025u1" `
  -IServerRoot "D:\supermap_software\supermap-iserver-2025u1a-windows-x64-all"
```

## Deployment responsibility boundary

The installer can prepare code dependencies and static SDK resources. It cannot fully replace the first-time iServer admin confirmation and service publication on a new computer, because those depend on the local iServer account, license, file root, and published service registry.

For formal acceptance, run the existing evidence gate after services are published:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check_supermap_goal_evidence.ps1 -Strict
```
