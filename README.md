<div  align="center">
    <h2>Command launcher for Maya</h2>
    <a href="https://results.pre-commit.ci/latest/github/lixaft/maya-toolbar/main"><img alt="pre-commit.ci status" src="https://results.pre-commit.ci/badge/github/lixaft/maya-toolbar/main.svg"></a>
    <a href="https://pypi.org/project/maya-toolbar/"><img src="https://img.shields.io/pypi/v/maya-toolbar.svg"></a>
    <a href="https://github.com/psf/black/blob/main/LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/licence-MIT-blue"></a>
    <img src=https://img.shields.io/badge/python-2.7%20|%203.7+-blue>
    <img src=https://img.shields.io/badge/maya-2020+-green>
    <a href="https://github.com/astral-sh/ruff"><img alt="Code style: ruff" src="https://img.shields.io/badge/code%20style-ruff-261230.svg"></a>
</div>

<br>
<br>

> Ever wanted more space on your shelf?

_maya-toolbar_ is a user interface designed to quickly access and execute user-defined commands.

<br>

<div  align="center">
    <img width="1362" alt="image" src="https://user-images.githubusercontent.com/61330762/166395183-3b3f9291-2f37-4eb2-99a5-14543562985e.png" width=80% style="border-radius:10px;">
</div>

<br>

<h3>Features</h3>

- Resizable UI
- Dockable UI
- Persistent UI
- Customizable

<br>

<h3>Table of Contents</h3>

- [System Requirements](#system-requirements)
- [Installation](#installation)
  - [Manual](#manual)
  - [pip](#pip)
- [Usage](#usage)
- [Add New Tabs](#add-new-tabs)
- [YAML References](#yaml-references)
  - [Tab](#tab)
  - [Category](#category)
  - [Command](#command)
  - [Menu](#menu)
  - [Menu item](#menu-item)
    - [`command`](#command-1)
    - [`separator`](#separator)
    - [`menu`](#menu-1)
- [Execute function](#execute-function)
- [Environment Variables](#environment-variables)
  - [`TOOLBAR_PATH_DISCOVER`](#toolbar_path_discover)
  - [`TOOLBAR_ACTIVE_TAB`](#toolbar_active_tab)
  - [`TOOLBAR_AUTOLOAD`](#toolbar_autoload)
- [Special Thanks](#special-thanks)

<br>

### System Requirements

- [Autodesk Maya](https://help.autodesk.com/view/MAYAUL/2020/ENU/) _(2020+)_

  In theory, it _may_ run in older maya versions, but those are never being tested. If you try to use it on one of these versions and everything seems to works properly, please do not hesitate to let me know! :)

  Note that the tool does not currently support maya 2025+ due to the upgrade of the pyside library to the version 6. I plan to add a support using the [Qt.py](https://github.com/mottosso/Qt.py/blob/master/Qt.py) in a future release.

- [YAML](https://pyyaml.org)

  This will allow to write proper and readable configuration files that the UI will read to generate the user interface. The library is not included with the Maya installation, so we need to install it separately. Please see the [installation](#installation) section below for details.

<br>

### Installation

The installation can be done using two different methods.

<br>

#### Manual

1. Located the maya _script_ directory (or any other directory that will be available in the [`PYTHONPATH`](https://docs.python.org/3/using/cmdline.html#envvar-PYTHONPATH)).

   - Linux
     - `~/maya/scripts`
     - `~/maya/{VERSION}/scripts`
   - Windows
     - `~/Documents/maya/scripts`
     - `~/Documents/maya/{VERSION}/scripts`
   - Mac OS
     - `Library/Preferences/Autodesk/maya/scripts`
     - `Library/Preferences/Autodesk/maya/{VERSION}/scripts`

2. Install [`pyyaml`](https://github.com/yaml/pyyaml) package.

   If your workstation is in a studio, there is a good chance that the library is already installed. If you are not sure, you can try running the following code:

   ```python
   import yaml
   ```

   If an `ImportError` is raised, the library needs to be installed, otherwise, you're good to go :)

   The easiest way to install it is to use [`pip`](https://pip.pypa.io/en/stable/). The `--target` option allows us to change the directory in which the package will be installed. In our case, we want to use the _scripts_ directory found above (or another directory that is a part of the [`PYTHONPATH`](https://docs.python.org/3/using/cmdline.html#envvar-PYTHONPATH)).

   ```bash
   pip install pyyaml --target ~/maya/scripts
   ```

3. Download the file [`maya_toolbar.py`](https://raw.githubusercontent.com/lixaft/maya-toolbar/main/maya_toolbar.py) and save it inside the _scripts_ directory.

4. See [usage](#usage) below.

<br>

#### pip

_maya-toolbar_ is also uploaded on [`PyPI`](https://pypi.org) and can directly be installed using [`pip`](https://pip.pypa.io/en/stable/). This means that all the dependencies will be automatically be installed without doing anything else!

```bash
pip install maya-toolbar
```

Like in the [manual](#manual) section, its possible to use the `--target` option to install the package in other directory, for example, the maya _scripts_ folder.

<br>

### Usage

To open the toolbar, get a new python tab inside the script editor, and execute the following lines:

```py
import maya_toolbar
maya_toolbar.show()
```

The user interface will added to the current [workspace](https://knowledge.autodesk.com/support/maya/learn-explore/caas/CloudHelp/cloudhelp/2023/ENU/Maya-Basics/files/GUID-0384C282-3CA1-4587-9775-F7164D3F6980-htm.html). This means that it will automatically reopen where it was left for the next Maya session!

Enjoy! :)

<br>

<div  align="center">
    <img width="1362" alt="image" src="https://user-images.githubusercontent.com/61330762/166395183-3b3f9291-2f37-4eb2-99a5-14543562985e.png" width=80% style="border-radius:10px;">
</div>

<br>

### Add New Tabs

Each tab is represented by a single [YAML](https://pyyaml.org) file which contains all the configuration to generate the UI.

By default the tabs will be searched in the following directories (where `~` represent the `$HOME` directory):

- Linux
  - `~/toolbar`
  - `~/maya/toolbar`
  - `~/maya/{VERSION}/prefs/toolbar`
- Windows
  - `~/toolbar`
  - `~/Documents/maya/toolbar`
  - `~/Documents/maya/{VERSION}/prefs/toolbar`
- Mac OS
  - `~/toolbar`
  - `Library/Preferences/Autodesk/maya/toolbar`
  - `Library/Preferences/Autodesk/maya/{VERSION}/prefs/toolbar`

In addition to these directories, every maya module that contains a directory called `toolbar` will also be included.

Arbitrary directories can also be added using the [`TOOLBAR_PATH_DISCOVER`](#toolbar_path_discover) environment variable or directly from the python interpreter using the [`PATH_DISCOVER`](#toolbar_path_discover) attribute:

```bash
export TOOLBAR_PATH_DISCOVER = $TOOLBAR_PATH_DISCOVER:path/to/directory
```

```python
import maya_toolbar
maya_toolbar.PATH_DISCOVER.append("path/to/directory")
maya_toolbar.show()
```

<br>

### YAML References

All the configure of the toolbar are done through [YAML](https://pyyaml.org) files. There will be no explanation of syntax here but its possible to learn it from the [official documentation](https://yaml.org/spec/1.2.2/).

See bellow all the different options available for each component of the toolbar.

<br>

#### Tab

- `name` _(str)_ - The name of the tab. If not specified, the name of the file will be used (without the extensions).
- `load` _(bool)_ - Specify if the configuration should be loaded as a tab or not. Defaults to [`AUTOLOAD`](#toolbar_autoload).
- `categories` _(list)_ - The configuration of the categories.

```yaml
name: demo
load: true
categories: []
```

<br>

#### Category

- `name` _(str)_ - The name of the category.
- `open` _(bool)_ - Should the category be extended or collapsed by default? Defaults to `false`.
- `commands` _(list)_ - The configuration of the commands.

```yaml
name: Category A
open: false
commands: []
```

<br>

#### Command

- `name` _(str)_ - The name of the command (Displayed as a tooltip).
- `icon` _(str)_ - The icon with which the command will be displayed.
- `label` _(str)_ - A short text that will be displayed below the command.
- `callback` _(str)_ - The function that should be executed (see the syntax [here](#execute-function)).
- `menu` _(dict)_ - The configuration of the menu.

```yaml
name: Command A
icon: :mayaCommand.png
label: a
callback: maya.cmds:NewScene
menu: {}
```

<br>

#### Menu

- `click` _(str)_ - The click that will show the menu (`left` or `right`). Defaults to `right`.
- `items` _(list)_ - The item to add as children.

```yaml
name: Menu A
click: right
items: []
```

<br>

#### Menu item

- `type` _(str)_ - The type of the item to add. For each of them, different options are available:

Additional options are available according to the specified type:

##### `command`

- `name` _(str)_ - The name of the command.
- `icon` _(str)_ - The icon with which the command will be displayed.
- `callback` _(str)_ - The function that should be executed (see the syntax [here](#execute-function)).

```yaml
type: command
name: Menu command A
icon: :mayaCommand.png
callback: maya.cmds:NewScene
```

##### `separator`

No options are available.

```yaml
type: separator
```

##### `menu`

- `name` _(str)_ - The name of the menu.
- `icon` _(str)_ - The icon with which the menu will be displayed.
- `items` _(list)_ - The item to add as children.

```yaml
type: menu
name: Menu A
icon: :mayaCommand.png
items: []
```

<br>

### Execute function

To call a function, a special syntax similar to setuptools is used. The package name is separated from the function name using a `:`, where the package can be anything accessible from python (inside the [`PYTHONPATH`](https://docs.python.org/3/using/cmdline.html#envvar-PYTHONPATH))).

So for example, if we have a module called `commands.py` available inside our [`PYTHONPATH`](https://docs.python.org/3/using/cmdline.html#envvar-PYTHONPATH) and that contains the following code:

```python
def hello_world():
    print("Hello Word!")
```

Inside the [YAML configuration file](#add-new-tabs), we can point to our `hello_world` function using:

```yaml
callback: commands:hello_world
```

<br>

### Environment Variables

Functionalities of the toolbar can be modified using environment variables.

<br>

#### `TOOLBAR_PATH_DISCOVER`

Similar to what python does with the [`PYTHONPATH`](https://docs.python.org/3/using/cmdline.html#envvar-PYTHONPATH)) variable, this allows the specified custom path to include in the search for the tab configuration file.

```bash
echo $TOOLBAR_PATH_DISCOVER
```

The equivalent attribute in the python module is `PATH_DISCOVER`:

```python
import maya_toolbar
maya_toolbar.PATH_DISCOVER
```
<br>

#### `TOOLBAR_ACTIVE_TAB`

The name of the tab that should have the focus when the user interface is opened or reloaded.

```bash
echo $TOOLBAR_ACTIVE_TAB
```

The equivalent attribute in the python module is `ACTIVE_TAB`:

```python
import maya_toolbar
maya_toolbar.ACTIVE_TAB
```
<br>

#### `TOOLBAR_AUTOLOAD`

Set the default loading behaviour for discovered configuration files.

`1` means that all configuration files will be automatically loaded, unless `load: false` is explicitly specified.

`0` is the exact opposite. Each configuration file will not be considered for loading unless the `load: true` option is specified.

```bash
echo $TOOLBAR_AUTOLOAD
```

The equivalent attribute in the python module is `AUTOLOAD`:

```python
import maya_toolbar
maya_toolbar.AUTOLOAD
```

## Special Thanks

- [@BenoitGielly](https://github.com/BenoitGielly) for the original idea and implementation!
