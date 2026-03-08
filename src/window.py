"""GC-Setup main window."""

import threading

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib

from src.pages.apps_page import AppsPage
from src.pages.extensions_page import ExtensionsPage
from src.pages.misc_page import MiscPage
from src.installer.dialog import ProgressWindow
from src.installer.detection import (
    detect_installed_apps,
    detect_installed_extensions,
    detect_installed_misc,
)


class GCSetupWindow(Adw.ApplicationWindow):
    """Main application window with sidebar navigation."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.set_title('GC-Setup')
        self.set_default_size(900, 700)

        # Track all pages for collecting selections
        self._pages = {}

        # Build the UI
        self._build_ui()

        # Run installed-detection in background
        self._run_detection()

    def _build_ui(self):
        # Root: OverlaySplitView — each pane gets its own header bar
        # so the sidebar integrates with the window chrome.
        self._split_view = Adw.OverlaySplitView()
        self._split_view.set_collapsed(False)
        self._split_view.set_min_sidebar_width(200)
        self._split_view.set_max_sidebar_width(260)
        self.set_content(self._split_view)

        # === SIDEBAR (left pane with its own header) ===
        sidebar_toolbar = Adw.ToolbarView()

        sidebar_header = Adw.HeaderBar()
        sidebar_header.set_show_end_title_buttons(False)
        title_label = Gtk.Label(label='GC-Setup')
        title_label.set_css_classes(['title'])
        sidebar_header.set_title_widget(title_label)
        sidebar_toolbar.add_top_bar(sidebar_header)

        sidebar_scroll = Gtk.ScrolledWindow()
        sidebar_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sidebar_scroll.set_vexpand(True)

        self._sidebar_list = Gtk.ListBox()
        self._sidebar_list.set_css_classes(['navigation-sidebar'])
        self._sidebar_list.set_selection_mode(Gtk.SelectionMode.SINGLE)

        # Sidebar rows
        sidebar_items = [
            ('applications-symbolic', 'Apps'),
            ('application-x-addon-symbolic', 'Extensions'),
            ('preferences-other-symbolic', 'Misc'),
        ]
        for icon_name, label in sidebar_items:
            row = Gtk.ListBoxRow()
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            box.set_margin_top(8)
            box.set_margin_bottom(8)
            box.set_margin_start(12)
            box.set_margin_end(12)
            icon = Gtk.Image.new_from_icon_name(icon_name)
            lbl = Gtk.Label(label=label)
            lbl.set_xalign(0)
            lbl.set_hexpand(True)
            box.append(icon)
            box.append(lbl)
            row.set_child(box)
            self._sidebar_list.append(row)

        sidebar_scroll.set_child(self._sidebar_list)
        sidebar_toolbar.set_content(sidebar_scroll)

        sidebar_page = Adw.NavigationPage(title='Navigation')
        sidebar_page.set_child(sidebar_toolbar)
        self._split_view.set_sidebar(sidebar_page)

        # === CONTENT AREA (right pane with its own header) ===
        content_toolbar = Adw.ToolbarView()

        content_header = Adw.HeaderBar()
        content_header.set_show_start_title_buttons(False)

        # About button in content header
        about_btn = Gtk.Button(icon_name='help-about-symbolic')
        about_btn.set_tooltip_text('About GC-Setup')
        about_btn.connect(
            'clicked',
            lambda *_: self.get_application().activate_action('about', None),
        )
        content_header.pack_end(about_btn)

        content_toolbar.add_top_bar(content_header)

        # Content stack
        self._content_stack = Gtk.Stack()
        self._content_stack.set_transition_type(
            Gtk.StackTransitionType.CROSSFADE
        )
        self._content_stack.set_transition_duration(200)

        # Create pages
        apps_page = AppsPage()
        extensions_page = ExtensionsPage()
        misc_page = MiscPage()

        self._pages['apps'] = apps_page
        self._pages['extensions'] = extensions_page
        self._pages['misc'] = misc_page

        self._content_stack.add_named(apps_page, 'apps')
        self._content_stack.add_named(extensions_page, 'extensions')
        self._content_stack.add_named(misc_page, 'misc')

        # Content wrapper with bottom bar
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.set_vexpand(True)

        self._content_stack.set_vexpand(True)
        content_box.append(self._content_stack)

        # === BOTTOM BAR ===
        bottom_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        bottom_bar.set_css_classes(['toolbar'])
        bottom_bar.set_margin_top(6)
        bottom_bar.set_margin_bottom(6)
        bottom_bar.set_margin_start(12)
        bottom_bar.set_margin_end(12)
        bottom_bar.set_halign(Gtk.Align.END)

        install_button = Gtk.Button(label='Apply')
        install_button.set_css_classes(['suggested-action', 'pill'])
        install_button.connect('clicked', self._on_install_clicked)
        bottom_bar.append(install_button)

        content_box.append(bottom_bar)

        content_toolbar.set_content(content_box)

        content_page = Adw.NavigationPage(title='Content')
        content_page.set_child(content_toolbar)
        self._split_view.set_content(content_page)

        # Connect sidebar selection
        self._sidebar_list.connect('row-selected', self._on_sidebar_selected)
        self._sidebar_list.select_row(
            self._sidebar_list.get_row_at_index(0)
        )

    def _run_detection(self):
        """Run installed-software detection in background threads."""
        apps_page = self._pages.get('apps')
        ext_page = self._pages.get('extensions')
        misc_page = self._pages.get('misc')

        if apps_page:
            threading.Thread(
                target=detect_installed_apps,
                args=(apps_page,),
                daemon=True,
            ).start()

        if ext_page:
            threading.Thread(
                target=detect_installed_extensions,
                args=(ext_page,),
                daemon=True,
            ).start()

        if misc_page:
            threading.Thread(
                target=detect_installed_misc,
                args=(misc_page,),
                daemon=True,
            ).start()

    def _on_sidebar_selected(self, _listbox, row):
        if row is None:
            return
        index = row.get_index()
        page_names = ['apps', 'extensions', 'misc']
        if 0 <= index < len(page_names):
            self._content_stack.set_visible_child_name(page_names[index])

    def _on_install_clicked(self, _button):
        """Collect all selected items and start installation."""
        selected_items = []

        # Collect from apps page
        apps_page = self._pages.get('apps')
        if apps_page:
            selected_items.extend(apps_page.get_selected_items())

        # Collect from extensions page
        ext_page = self._pages.get('extensions')
        if ext_page:
            selected_items.extend(ext_page.get_selected_items())

        # Collect from misc page
        misc_page = self._pages.get('misc')
        if misc_page:
            selected_items.extend(misc_page.get_selected_items())

        if not selected_items:
            dialog = Adw.AlertDialog(
                heading='Nothing Selected',
                body='Please select at least one item to install.',
            )
            dialog.add_response('ok', 'OK')
            dialog.present(self)
            return

        # Open progress window
        progress = ProgressWindow(selected_items, self)
        progress.present()
