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
from src.installer.dialog import ProgressDialog
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

        self._pages = {}          # category_id -> CategoryPage
        self._category_ids = []   # ordered list of category IDs

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
            
            # Add experimental badge for system-tweaks
            if cat_id == 'system-tweaks':
                badge = Gtk.Label(label='Experimental')
                badge.set_css_classes(['caption', 'dim-label'])
                badge.set_margin_start(6)
                box.append(badge)
            
            row.set_child(box)
            self._sidebar_list.append(row)

            # Page widget
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

        # Toast overlay wraps the page stack
        self._toast_overlay = Adw.ToastOverlay()
        self._toast_overlay.set_child(self._content_stack)
        content_toolbar.set_content(self._toast_overlay)

        # === BOTTOM BAR — Apply + Remove ===
        bottom_bar = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=8,
            halign=Gtk.Align.END,
        )
        bottom_bar.set_margin_top(6)
        bottom_bar.set_margin_bottom(6)
        bottom_bar.set_margin_start(12)
        bottom_bar.set_margin_end(12)

        self._remove_button = Gtk.Button(label='Remove')
        self._remove_button.set_css_classes(['destructive-action', 'pill'])
        self._remove_button.connect('clicked', self._on_remove_clicked)
        bottom_bar.append(self._remove_button)

        self._apply_button = Gtk.Button(label='Apply')
        self._apply_button.set_css_classes(['suggested-action', 'pill'])
        self._apply_button.connect('clicked', self._on_apply_clicked)
        bottom_bar.append(self._apply_button)

        content_toolbar.add_bottom_bar(bottom_bar)

        content_page = Adw.NavigationPage(title='Content')
        content_page.set_child(content_toolbar)
        self._split_view.set_content(content_page)

        # Connect sidebar selection
        self._sidebar_list.connect('row-selected', self._on_sidebar_selected)
        self._sidebar_list.select_row(
            self._sidebar_list.get_row_at_index(0)
        )

    # ── Detection ─────────────────────────────────────────────────

    def _run_detection(self):
        """Run installed-software detection in background."""
        all_pages = list(self._pages.values())
        threading.Thread(
            target=detect_installed_items,
            args=(all_pages,),
            daemon=True,
        ).start()

    # ── Callbacks ─────────────────────────────────────────────────

    def _on_sidebar_selected(self, _listbox, row):
        if row is None:
            return
        index = row.get_index()
        if 0 <= index < len(self._category_ids):
            self._content_stack.set_visible_child_name(
                self._category_ids[index]
            )

    def _on_apply_clicked(self, _button):
        """Collect selected non-installed items and open progress dialog."""
        selected = []
        for page in self._pages.values():
            selected.extend(page.get_selected_items())

        if not selected:
            toast = Adw.Toast.new('Nothing selected to install')
            toast.set_timeout(2)
            self._toast_overlay.add_toast(toast)
            return

        self._apply_button.set_sensitive(False)
        self._remove_button.set_sensitive(False)

        dlg = ProgressDialog(
            selected,
            mode='install',
            on_complete_cb=self._on_operation_complete,
        )
        dlg.present(self)
        dlg.start()

    def _on_remove_clicked(self, _button):
        """Collect selected installed items and open progress dialog for removal."""
        selected = []
        for page in self._pages.values():
            selected.extend(page.get_selected_installed_items())

        if not selected:
            toast = Adw.Toast.new('Nothing selected to remove')
            toast.set_timeout(2)
            self._toast_overlay.add_toast(toast)
            return

        self._apply_button.set_sensitive(False)
        self._remove_button.set_sensitive(False)

        dlg = ProgressDialog(
            selected,
            mode='remove',
            on_complete_cb=self._on_operation_complete,
        )
        dlg.present(self)
        dlg.start()

    def _on_operation_complete(self):
        """Called when install or remove finishes."""
        self._apply_button.set_sensitive(True)
        self._remove_button.set_sensitive(True)
        # Clear checkboxes and re-detect
        for page in self._pages.values():
            page.clear_selection()
        self._run_detection()
