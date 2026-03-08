"""GC-Setup main window."""

import json
import os
import threading

import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, GLib

from src.pages.category_page import CategoryPage
from src.pages.system_tweaks_page import SystemTweaksPage
from src.installer.dialog import ProgressSheet
from src.installer.detection import detect_installed_items


def _get_data_path(filename):
    """Resolve path to bundled data file."""
    pkg = os.environ.get('GC_SETUP_PKGDATADIR', '')
    if pkg:
        path = os.path.join(pkg, 'data', filename)
        if os.path.exists(path):
            return path
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, 'data', filename)


def _load_catalog():
    """Load the unified catalog."""
    path = _get_data_path('catalog.json')
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f'Warning: Could not load catalog.json: {e}')
        return {'categories': []}


class GCSetupWindow(Adw.ApplicationWindow):
    """Main application window with sidebar navigation."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.set_title('GC-Setup')
        self.set_default_size(900, 700)

        self._pages = {}  # category_id -> CategoryPage
        self._category_ids = []  # ordered list of category IDs
        self._progress_sheet = None

        # Load catalog
        self._catalog = _load_catalog()

        # Build the UI
        self._build_ui()

        # Run installed-detection in background
        self._run_detection()

    def _build_ui(self):
        # Root: OverlaySplitView
        self._split_view = Adw.OverlaySplitView()
        self._split_view.set_collapsed(False)
        self._split_view.set_min_sidebar_width(200)
        self._split_view.set_max_sidebar_width(260)
        self.set_content(self._split_view)

        # === SIDEBAR ===
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

        # Content stack
        self._content_stack = Gtk.Stack()
        self._content_stack.set_transition_type(
            Gtk.StackTransitionType.CROSSFADE
        )
        self._content_stack.set_transition_duration(200)

        # Build sidebar rows and pages from catalog
        for cat in self._catalog.get('categories', []):
            cat_id = cat['id']
            cat_name = cat['name']
            cat_icon = cat.get('icon', 'application-x-executable-symbolic')
            self._category_ids.append(cat_id)

            # Sidebar row
            row = Gtk.ListBoxRow()
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            box.set_margin_top(8)
            box.set_margin_bottom(8)
            box.set_margin_start(12)
            box.set_margin_end(12)
            icon = Gtk.Image.new_from_icon_name(cat_icon)
            lbl = Gtk.Label(label=cat_name)
            lbl.set_xalign(0)
            lbl.set_hexpand(True)
            box.append(icon)
            box.append(lbl)
            row.set_child(box)
            self._sidebar_list.append(row)

            # Page widget — system-tweaks gets the special page with font rendering
            if cat_id == 'system-tweaks':
                page = SystemTweaksPage(cat)
            else:
                page = CategoryPage(cat)

            self._pages[cat_id] = page
            self._content_stack.add_named(page, cat_id)

        sidebar_scroll.set_child(self._sidebar_list)
        sidebar_toolbar.set_content(sidebar_scroll)

        sidebar_page = Adw.NavigationPage(title='Navigation')
        sidebar_page.set_child(sidebar_toolbar)
        self._split_view.set_sidebar(sidebar_page)

        # === CONTENT AREA ===
        content_toolbar = Adw.ToolbarView()

        content_header = Adw.HeaderBar()
        content_header.set_show_start_title_buttons(False)

        about_btn = Gtk.Button(icon_name='help-about-symbolic')
        about_btn.set_tooltip_text('About GC-Setup')
        about_btn.connect(
            'clicked',
            lambda *_: self.get_application().activate_action('about', None),
        )
        content_header.pack_end(about_btn)
        content_toolbar.add_top_bar(content_header)

        self._content_stack.set_vexpand(True)

        # === BOTTOM SHEET ===
        self._bottom_sheet = Adw.BottomSheet()
        self._bottom_sheet.set_content(self._content_stack)
        self._bottom_sheet.set_full_width(True)
        self._bottom_sheet.set_modal(True)
        self._bottom_sheet.set_show_drag_handle(True)
        self._bottom_sheet.set_can_open(False)

        # Bottom bar: Apply button
        bottom_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        bottom_bar.set_css_classes(['toolbar'])
        bottom_bar.set_margin_top(6)
        bottom_bar.set_margin_bottom(6)
        bottom_bar.set_margin_start(12)
        bottom_bar.set_margin_end(12)
        bottom_bar.set_halign(Gtk.Align.END)

        self._apply_button = Gtk.Button(label='Apply')
        self._apply_button.set_css_classes(['suggested-action', 'pill'])
        self._apply_button.connect('clicked', self._on_apply_clicked)
        bottom_bar.append(self._apply_button)

        self._bottom_sheet.set_bottom_bar(bottom_bar)
        self._bottom_sheet.set_reveal_bottom_bar(True)

        content_toolbar.set_content(self._bottom_sheet)

        content_page = Adw.NavigationPage(title='Content')
        content_page.set_child(content_toolbar)
        self._split_view.set_content(content_page)

        # Connect sidebar selection
        self._sidebar_list.connect('row-selected', self._on_sidebar_selected)
        self._sidebar_list.select_row(
            self._sidebar_list.get_row_at_index(0)
        )

    def _run_detection(self):
        """Run installed-software detection in background."""
        all_pages = list(self._pages.values())
        threading.Thread(
            target=detect_installed_items,
            args=(all_pages,),
            daemon=True,
        ).start()

    def _on_sidebar_selected(self, _listbox, row):
        if row is None:
            return
        index = row.get_index()
        if 0 <= index < len(self._category_ids):
            self._content_stack.set_visible_child_name(
                self._category_ids[index]
            )

    def _on_apply_clicked(self, _button):
        """Collect all selected items and open the bottom sheet."""
        selected_items = []
        for page in self._pages.values():
            selected_items.extend(page.get_selected_items())

        if not selected_items:
            dialog = Adw.AlertDialog(
                heading='Nothing Selected',
                body='Please select at least one item to install.',
            )
            dialog.add_response('ok', 'OK')
            dialog.present(self)
            return

        self._progress_sheet = ProgressSheet(
            selected_items,
            on_complete_cb=self._on_install_complete,
        )

        self._bottom_sheet.set_sheet(self._progress_sheet.widget)
        self._bottom_sheet.set_can_open(True)
        self._bottom_sheet.set_can_close(False)
        self._bottom_sheet.set_open(True)

        self._apply_button.set_sensitive(False)
        self._progress_sheet.start()

    def _on_install_complete(self):
        """Called when all installs are finished."""
        self._bottom_sheet.set_can_close(True)
        self._apply_button.set_sensitive(True)
        self._run_detection()
