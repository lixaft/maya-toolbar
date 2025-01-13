"""Command launcher for Autodesk Maya."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import os
import re
import webbrowser

import shiboken2
import yaml
from maya import OpenMayaUI
from maya import cmds
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

TYPE_CHECKING = False
if TYPE_CHECKING:
    from typing import ClassVar  # noqa: F401

# Project information.
__version__ = "0.2.0"
__author__ = "Fabien Taxil"
__author_email__ = "me@lixaft.dev"
__url__ = "https://github.com/lixaft/maya-toolbar"

# Public content.
__all__ = [
    "ACTIVE_TAB",
    "AUTOLOAD",
    "PATH_DISCOVER",
    "show",
]

# Logger configuration.
LOG = logging.getLogger(__name__)


# Public constants.
ACTIVE_TAB = os.getenv("TOOLBAR_ACTIVE_TAB", "")
AUTOLOAD = os.getenv("TOOLBAR_AUTOLOAD", "1") == "1"
PATH_DISCOVER = []


# Private constants.
_DIRECTORY_NAME = "toolbar"
_WIDGET_NAME = "maya_toolbar_main_widget"
_WORKSPACE_NAME = "maya_toolbar_workspace_control"
_CSS = """\
Toolbar > QToolButton,
Tab,
Command {
    border: none;
}
Category > QPushButton {
    color: rgb(189, 189, 189);
    background-color: rgb(93, 93, 93);
    padding-left: 30px;
    border: none;
    border-radius: 2px;
    font: bold;
    text-align: left;
}
Command > QLabel#label {
    background-color: rgba(0, 0, 0, 0.5);
    color: rgba(255, 255, 255, 0.8);
    font-size: 10px;
    min-height: 10px;
    border-radius: 3px;
}
"""


def retrieve_callback(path):
    """Retrieve the callable that is located at the given path.

    The ``path`` argument use a special syntax to specify the function that
    must be invoked when the command will be pressed. Like setuptools, the
    package name and the function name are separated using a ``:``.

    Arguments:
        path (str): The path that point to the function to retrieve.

    Returns:
        callable: The callable of the function at the given path.
    """
    module, _, function = path.partition(":")
    module_object = __import__(module, fromlist=[""])
    return getattr(module_object, function)


def discover_tab_files(pattern=r".+\.ya?ml"):
    """Find all the configuration files that can be found.

    By default, the YAML files found in the ``PATH_DISCOVER`` directories and
    that match the given ``pattern`` (By default, any file with that have the
    ``.yaml`` or ``.yml`` extension) will be returned.

    Arguments:
        pattern (str): The regular expression that the file names must  match.

    Yields:
        str: The next configuration file.
    """
    for path in PATH_DISCOVER:
        if not os.path.exists(path):
            continue
        for file_ in os.listdir(path):
            if not re.match(pattern, file_):
                continue
            yield os.path.join(path, file_)


def show():
    """Open the toolbar interface.

    A workspace control will be created and the toolbar will be attached to
    this control. This means that the window will be saved with the user's
    workspace.

    When a new Maya is opened, a small script is in charge of bringing the
    toolbar back to where the user left it during the last session :)

    Returns:
        Toolbar: The instance of the widget used to build the interface.
    """
    # Create the workspace control if needed.
    if not cmds.workspaceControl(_WORKSPACE_NAME, query=True, exists=True):
        cmds.workspaceControl(
            _WORKSPACE_NAME,
            retain=False,
            floating=True,
            widthProperty="preferred",
            loadImmediately=True,
            uiScript="import {0};{0}.show()".format(__name__),
        )

    # Update the label of the workspace to add the current version.
    label = "Toolbar " + __version__
    cmds.workspaceControl(_WORKSPACE_NAME, edit=True, label=label)

    # Get the workspace as PySide2 instance from its c++ pointer.
    pointer = OpenMayaUI.MQtUtil.findControl(_WORKSPACE_NAME)
    control = shiboken2.wrapInstance(
        getattr(__builtins__, "long", int)(pointer),
        QtWidgets.QWidget,
    )

    # Get the layout of the workspace control.
    layout = control.layout()

    # Remove every children from the layout.
    for i in reversed(range(layout.count())):
        item = layout.takeAt(i)
        item.widget().setParent(None)

    # Remove any existing top-level widgets.
    for each in QtWidgets.QApplication.topLevelWidgets():
        if each.objectName() == _WIDGET_NAME:
            each.deleteLater()

    # Attach the main window to the layout.
    widget = Toolbar()
    widget.refresh()
    layout.addWidget(widget)

    return widget


class Toolbar(QtWidgets.QWidget):
    """Main widget used to build the toolbar interface.

    Arguments:
        parent (QtWidgets.QWidget): The widget under which the toolbar will
            be created.
    """

    def __init__(self, parent=None):
        super(Toolbar, self).__init__(parent)
        icon_size = QtCore.QSize(24, 24)

        # Initialize the widget properties.
        self.setObjectName(_WIDGET_NAME)
        self.setStyleSheet(_CSS)
        self.setMinimumWidth(137)

        # Create info button.
        info = QtWidgets.QToolButton()
        info.setIcon(QtGui.QIcon(":info.png"))
        info.setIconSize(icon_size)
        info.setAutoRaise(True)
        info.setToolTip("Open the documentation")
        info.clicked.connect(lambda: webbrowser.open(__url__))

        # Create refresh button.
        refresh = QtWidgets.QToolButton()
        refresh.setIcon(QtGui.QIcon(":refresh.png"))
        refresh.setIconSize(icon_size)
        refresh.setAutoRaise(True)
        refresh.setToolTip("Refresh the content of the toolbar")
        refresh.clicked.connect(self.refresh)

        # Initialize the widget that will contain all the different tabs.
        tab = QtWidgets.QTabWidget()

        # Create header layout.
        header = QtWidgets.QHBoxLayout()
        header.addWidget(info)
        header.addStretch()
        header.addWidget(refresh)

        # Create the main layout.
        main = QtWidgets.QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)
        main.addLayout(header)
        main.addWidget(tab)

        # Register widgets inside the instance.
        self.__tab = tab

    def refresh(self):
        """Refresh the tabs based on what will be found on the disk.

        The ``ACTIVE_TAB`` will be used to determine which tabs should have
        the focus at the end of the operation.
        """
        self.__tab.clear()

        # Store the tab that should have the focus.
        active = None

        for path in discover_tab_files():
            with open(path) as stream:
                config = yaml.safe_load(stream)

            # Skip the file if it shouln't be loaded.
            if not config.get("load", AUTOLOAD):
                continue

            # Get the name of the tab.
            name = config.get("name")
            if not name:
                name = os.path.splitext(os.path.split(path)[-1])[0]

            # Build a tab based on its configuration.
            LOG.info("Loading '%s'...", path)
            widget = self.load_dict(config)
            if name == ACTIVE_TAB:
                active = widget

        # Set the focus on the specified tab.
        if active is not None:
            self.__tab.setCurrentWidget(active)

    def add_tab(self, name):
        """Add a new tab to the toolbar.

        Arguments:
            name (str): The name that will be used to create the tab.

        Returns:
            Tab: The instance of the created tab.
        """
        widget = Tab()
        self.__tab.addTab(widget, name)
        return widget

    def load_dict(self, configuration):
        """Create a new tab based on the given configuration dictionary.

        Arguments:
            configuration (dict): The data that will drive the new widget.

        Returns:
            Tab: The instance of the created tab.
        """
        tab = self.add_tab(configuration.get("name", ""))

        # Add categories.
        for category_config in configuration.get("categories", []):
            category = tab.add_category(
                category_config["name"],
                category_config.get("open", False),
            )

            # Add commands.
            for command_config in category_config.get("commands", []):
                command = category.add_command(
                    command_config["name"],
                    command_config.get("icon"),
                    command_config.get("label"),
                    command_config.get("callback"),
                )

                # Check if we need to go further.
                menu_config = command_config.get("menu", {})
                if not menu_config:
                    continue

                # Add menu.
                def add_items(widget, menu_item_config):
                    # pylint: disable=cell-var-from-loop
                    for item_config in menu_item_config:
                        item_type = item_config.get("type", "command")
                        if item_type == "command":
                            widget.add_command(
                                item_config["name"],
                                item_config.get("icon", ""),
                                item_config.get("callback", None),
                            )
                        elif item_type == "menu":
                            sub = widget.add_menu(item_config["name"])
                            add_items(sub, item_config.get("items", []))
                        elif item_type == "separator":
                            widget.add_separator()
                        else:
                            msg = "Invalid item type '{}'."
                            raise ValueError(msg.format(item_type))

                menu = command.add_menu(menu_config.get("click", "right"))
                add_items(menu, menu_config.get("items", []))

        return tab


class Tab(QtWidgets.QScrollArea):
    """Build a tab for the toolbar.

    Arguments:
        parent (QtWidgets.QWidget): The widget under which the tab will
            be created.
    """

    def __init__(self, parent=None):
        super(Tab, self).__init__(parent)

        # Required to allow the widget to be scrollable.
        self.setWidgetResizable(True)

        # Create the widget that will contain all the categories.
        widget = QtWidgets.QWidget()
        self.setWidget(widget)

        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addStretch()

        self.__layout = layout

    def add_category(self, name, expanded=False):
        """Add a new category.

        Arguments:
            name (str): The name that will be used to create the category.
            expanded (bool): The collapse state of the widget on the creation.

        Returns:
            Category: The instance of the created category widget.
        """
        widget = Category(name)
        index = self.__layout.count() - 1
        self.__layout.insertWidget(index, widget)
        widget.set_expanded(expanded)
        return widget


class Category(QtWidgets.QWidget):
    """Category widget.

    Arguments:
        title (str): The name that will be displayed on the category.
        parent (QtWidgets.QWidget): The widget under which the category will
            be created.
    """

    _OPEN_POINTS = [
        QtCore.QPointF(0, 0.2),
        QtCore.QPointF(0.5, 0.8),
        QtCore.QPointF(1, 0.2),
    ]
    _CLOSE_POINTS = [
        QtCore.QPointF(0.2, 0),
        QtCore.QPointF(0.8, 0.5),
        QtCore.QPointF(0.2, 1),
    ]

    def __init__(self, title, parent=None):
        super(Category, self).__init__(parent)

        # Ensure the right behavior and resize.
        policy = QtWidgets.QSizePolicy()
        policy.setVerticalPolicy(QtWidgets.QSizePolicy.Maximum)
        policy.setHorizontalPolicy(QtWidgets.QSizePolicy.Ignored)
        self.setSizePolicy(policy)

        # Create the header button.
        button = QtWidgets.QPushButton(title)
        button.setCheckable(True)
        button.setChecked(True)
        button.setFixedHeight(24)
        button.toggled.connect(self.__toggled)
        label = QtWidgets.QLabel(button)

        # Create the widget on which the commands will be added.
        widget = QtWidgets.QWidget()
        flow = _FlowLayout(widget)
        flow.setContentsMargins(1, 5, 1, 5)
        flow.setSpacing(1)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(button)
        layout.addWidget(widget)

        self.__label = label
        self.__button = button
        self.__widget = widget
        self.__flow = flow

        # Initialize the icon.
        self.__update_icon(True)

    def set_expanded(self, value):
        """Change the widget state between collapsed and expanded.

        Arguments:
            value (bool): True means expanded and False means collapsed.
        """
        self.__button.setChecked(value)

    def __toggled(self):
        """Toggle between expanded and collapsed."""
        is_checked = self.__button.isChecked()
        self.__widget.setVisible(is_checked)
        self.__update_icon(is_checked)

    def __update_icon(self, state):
        """Draw the arrow icon the specify the collapse/expand state."""
        pixmap = QtGui.QPixmap(self.__button.height(), self.__button.height())
        pixmap.fill(QtCore.Qt.transparent)

        brush = QtGui.QBrush(pixmap)
        brush.setStyle(QtCore.Qt.SolidPattern)
        brush.setColor(QtGui.QColor(238, 238, 238))

        pen = QtGui.QPen()
        pen.setColor(QtCore.Qt.transparent)

        painter = QtGui.QPainter(pixmap)
        painter.setPen(pen)
        painter.setBrush(brush)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, True)

        points = []
        for point in self._OPEN_POINTS if state else self._CLOSE_POINTS:
            offset = self.__button.height() * 0.25
            offset = QtCore.QPointF(offset, offset)
            points.append(point * self.__button.height() * 0.5 + offset)
        painter.drawPolygon(points)

        painter.end()
        self.__label.setPixmap(pixmap)

    def add_command(self, name, icon=None, label=None, callback=None):
        """Add a new command.

        Arguments:
            name (str): The name of the command.
            icon (str): The icon that will be used with the command.
            label (str): A short additional text that will be add.
            callback (str): The string that will be used with the
                ``retrieve_callback`` function.

        Returns:
            Command: The instance of the created command.
        """
        widget = Command()
        widget.setToolTip(name)
        if label is not None:
            widget.set_label(label)
        if icon is not None:
            widget.setIcon(QtGui.QIcon(icon))
        if callback is not None:
            widget.clicked.connect(retrieve_callback(callback))
        self.__flow.addWidget(widget)
        return widget


class Command(QtWidgets.QToolButton):
    """Command widget.

    Arguments:
        parent (QtWidgets.QWidget): The widget under which the command will
            be created.
    """

    CLICKS = {
        "right": QtCore.Qt.RightButton,
        "left": QtCore.Qt.LeftButton,
    }

    def __init__(self, parent=None):
        super(Command, self).__init__(parent)

        self.setAutoRaise(True)
        self.setIcon(QtGui.QIcon(":commandButton.png"))
        size = QtCore.QSize(38, 38)
        self.setMinimumSize(size)
        self.setMaximumSize(size)
        self.setIconSize(size * 0.9)

        self.__menu = None
        self.__click = None

    def mousePressEvent(self, event):
        """Implement the context menu."""
        if self.__menu is not None and event.button() == self.__click:
            pos = QtGui.QCursor.pos()
            self.__menu.exec_(pos)
            return
        super(Command, self).mousePressEvent(event)

    def set_label(self, text):
        """Set the label of the command."""
        if not text:
            return
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        label = QtWidgets.QLabel(text)
        label.setObjectName("label")
        label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addStretch()
        layout.addWidget(label)

    def add_menu(self, click=None):
        """Set the menu of the widget.

        Arguments:
            click (str): The click on which the menu should be triggered.
                Possible value are ``right`` and ``left``.

        Returns:
            Menu: The instance of the created menu.
        """
        self.__menu = Menu()
        self.__click = self.CLICKS.get(click, QtCore.Qt.RightButton)
        return self.__menu


class Menu(QtWidgets.QMenu):
    """Build the menu used inside a toolbar command."""

    def add_separator(self):
        """Add a new separator to the menu."""
        self.addSeparator()

    def add_command(self, name, icon=None, callback=None):
        """Add a new command to the menu.

        Arguments:
            name (str): The name of the command item.
            icon (str): The path to the icon that will be used.
            callback (str): The string that will be used with the
                ``retrieve_callback`` function.
        """
        action = self.addAction(name)
        if callback is not None:
            action.triggered.connect(retrieve_callback(callback))
        if icon is not None:
            action.setIcon(QtGui.QIcon(icon))

    def add_menu(self, name, icon=None):
        """Add a new sub-menu to the menu.

        Arguments:
            name (str): The name to give to the sub-menu.
            icon (str): The path to the icon that will be used.

        Returns:
            Menu: The instance of the created menu.
        """
        menu = Menu(name)
        self.addMenu(menu)
        if icon is not None:
            menu.setIcon(QtGui.QIcon(icon))
        return menu


class _FlowLayout(QtWidgets.QLayout):
    """Custom resizable widget.

    Arguments:
        parent (QtWidgets.QWidget): The widget in which the layout should be
            created.
    """

    def __init__(self, parent=None):
        super(_FlowLayout, self).__init__(parent)
        self.__items = []

    def itemAt(self, index):
        """Return the item at the given index.

        Arguments:
            index (int): The index that will be used to retrieve the item.

        Returns:
            QtWidgets.QLayoutItem: The item at the given index.
        """
        try:
            return self.__items[index]
        except IndexError:
            return None

    def takeAt(self, index):
        """Remove and return the item at the given index.

        Arguments:
            index (int): The index that will be used to take the item.

        Returns:
            QtWidgets.QLayoutItem: The item at the given index.
        """
        try:
            return self.__items.pop(index)
        except IndexError:
            return None

    def count(self):
        """Return the number of item in the layout."""
        return len(self.__items)

    def addItem(self, item):
        """Add an item to the layout.

        Arguments:
            item (QtWidgets.QLayoutItem): The instance of the item to add.
        """
        self.__items.append(item)

    def minimumSize(self):
        """Find the minimum size of the layout."""
        size = QtCore.QSize(0, 0)
        for item in self.__items:
            size = size.expandedTo(item.minimumSize())
        size += QtCore.QSize(
            self.contentsMargins().left() + self.contentsMargins().right(),
            self.contentsMargins().top() + self.contentsMargins().bottom(),
        )
        return size

    def sizeHint(self):
        """The preferred size of the layout."""
        return self.minimumSize()

    def hasHeightForWidth(self):
        """Tell Qt that the height of the layout is depending of its width."""
        return True

    def heightForWidth(self, width):
        """Calculare the height needed base on the layout width."""
        return self.__do_layout(QtCore.QRect(0, 0, width, 0), move=False)

    def setGeometry(self, rect):
        """Place all the item in the space allocated to the layout."""
        self.__do_layout(rect, move=True)

    def __do_layout(self, rect, move=False):
        current_x = self.contentsMargins().left()
        current_y = self.contentsMargins().top()
        next_x = current_x
        next_y = current_y
        for item in self.__items:
            next_x = current_x + item.sizeHint().width() + self.spacing()
            if next_x + self.contentsMargins().right() >= rect.width():
                current_x = self.contentsMargins().left()
                current_y = next_y + self.spacing()
                next_x = current_x + item.sizeHint().width() + self.spacing()
            if move:
                point = QtCore.QPoint(current_x, current_y)
                item.setGeometry(QtCore.QRect(point, item.sizeHint()))
            current_x = next_x
            next_y = max(next_y, current_y + item.sizeHint().height())
        return next_y + self.contentsMargins().bottom()


def _init():
    """Initialize the module by fill-in the global variables."""
    # Python 2 list does not have any clear() method like in python3. And if
    # we use the assiggnment operator to do the same thing, pylint complain as
    # its not allowed to assign a constant in a function scope.
    globals()["PATH_DISCOVER"] = []

    # Add path from the environment variable.
    PATH_DISCOVER.extend(
        path
        for path in (os.getenv("TOOLBAR_PATH_DISCOVER") or "").split(
            os.pathsep
        )
        if path
    )

    # Add path from maya modules.
    for module in cmds.moduleInfo(listModules=True):
        path = os.path.normpath(cmds.moduleInfo(moduleName=module, path=True))
        if path not in PATH_DISCOVER:
            PATH_DISCOVER.append(path)
    for path in (os.getenv("MAYA_MODULE_PATH") or "").split(os.pathsep):
        if path and path not in PATH_DISCOVER:
            PATH_DISCOVER.append(os.path.normpath(path))

    # Add path from maya prefs directories.
    directories = [
        cmds.internalVar(userPrefDir=True),
        cmds.internalVar(userAppDir=True),
        os.path.dirname(__file__),
        os.path.expanduser("~"),
    ]
    for directory in directories:
        path = os.path.normpath(os.path.join(directory, _DIRECTORY_NAME))
        PATH_DISCOVER.append(path)


_init()
