# Third-party notices

## Webots Robot Window bridge

`plugins/robot_windows/lockbox_window/RobotWindow.js` and `request_methods.js` include Cyberbotics' Webots Robot Window bridge. Their source headers retain the original copyright and licensing information. The Apache License 2.0 is included as `plugins/robot_windows/lockbox_window/LICENSE-Webots.txt`.

Webots is developed by Cyberbotics. The simulator is installed separately and is not distributed in this repository.

## Video tooling

The editable video project uses Remotion, React and related npm packages. Exact versions are recorded in `demo-studio/package-lock.json`. These packages are installed separately with `npm ci`; their respective licenses apply. Remotion licensing terms may depend on the user's organization and usage.

The Python controller and evaluation scripts require the Python standard library plus Webots' bundled controller API.

The optional dashboard test uses jsdom under the MIT license. Report generation uses ReportLab under its BSD license. These packages are needed only to rebuild or check the accompanying materials.
