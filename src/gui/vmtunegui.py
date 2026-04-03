#!/usr/bin/env python3

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk


class VMTuneWindow(Gtk.ApplicationWindow):
    def __init__(self, application):
        super().__init__(application=application)

        self.set_title("VM-TUNE")
        self.set_default_size(1000, 600)

        self.configure_page_index = 0
        self.create_page_index = 0
        self.passthrough_page_index = 0

        self.available_virtual_machines = ["VM1", "VM2", "VM3"]
        self.available_os_variants = [
            "ubuntu24.04",
            "fedora40",
            "win11",
            "generic",
        ]

        self.selected_virtual_machine = None
        self.selected_preset = None
        self.selected_asus_laptop_answer = None

        self.selected_gpu_vendor = None
        self.selected_vfio_answer = None

        self.vm_cpu_pinning_checkbuttons = {}
        self.emulator_cpu_pinning_checkbuttons = {}

        self.create_vm_name_entry = None
        self.create_iso_path_entry = None
        self.create_os_variant_dropdown = None
        self.create_memory_entry = None
        self.create_cpu_entry = None
        self.create_storage_entry = None

        self.configure_section_stack = None
        self.create_section_stack = None
        self.passthrough_section_stack = None
        self.main_section_stack = None

        self.configure_page_names = [
            "choose_vm",
            "vm_cpu_pinning",
            "emulator_cpu_pinning",
            "preset",
            "asus",
        ]

        self.create_page_names = [
            "create_vm_name",
            "create_iso",
            "create_resources",
        ]

        self.passthrough_page_names = [
            "select_gpu",
            "enable_vfio",
        ]

        self.set_child(self.build_main_layout())

    def build_main_layout(self):
        main_horizontal_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)

        left_sidebar = self.build_left_sidebar()
        right_content = self.build_right_content()

        main_horizontal_box.append(left_sidebar)
        main_horizontal_box.append(right_content)

        return main_horizontal_box

    def build_left_sidebar(self):
        sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        sidebar_box.set_size_request(210, -1)

        configure_button = self.build_sidebar_button("Configure", self.on_sidebar_configure_clicked)
        create_button = self.build_sidebar_button("Create", self.on_sidebar_create_clicked)
        passthrough_button = self.build_sidebar_button("Passthrough", self.on_sidebar_passthrough_clicked)

        sidebar_box.append(configure_button)
        sidebar_box.append(create_button)
        sidebar_box.append(passthrough_button)

        return sidebar_box

    def build_sidebar_button(self, label_text, clicked_handler):
        button = Gtk.Button(label=label_text)
        button.set_size_request(-1, 110)
        button.set_hexpand(True)
        button.connect("clicked", clicked_handler)
        return button

    def build_right_content(self):
        self.main_section_stack = Gtk.Stack()
        self.main_section_stack.set_hexpand(True)
        self.main_section_stack.set_vexpand(True)

        configure_section = self.build_configure_section()
        create_section = self.build_create_section()
        passthrough_section = self.build_passthrough_section()

        self.main_section_stack.add_named(configure_section, "configure")
        self.main_section_stack.add_named(create_section, "create")
        self.main_section_stack.add_named(passthrough_section, "passthrough")

        self.main_section_stack.set_visible_child_name("configure")

        return self.main_section_stack

    # -------------------------------------------------
    # Configure section
    # -------------------------------------------------

    def build_configure_section(self):
        self.configure_section_stack = Gtk.Stack()
        self.configure_section_stack.set_hexpand(True)
        self.configure_section_stack.set_vexpand(True)

        choose_vm_page = self.build_choose_vm_page()
        vm_cpu_pinning_page = self.build_vm_cpu_pinning_page()
        emulator_cpu_pinning_page = self.build_emulator_cpu_pinning_page()
        preset_page = self.build_preset_page()
        asus_page = self.build_asus_laptop_page()

        self.configure_section_stack.add_named(choose_vm_page, "choose_vm")
        self.configure_section_stack.add_named(vm_cpu_pinning_page, "vm_cpu_pinning")
        self.configure_section_stack.add_named(emulator_cpu_pinning_page, "emulator_cpu_pinning")
        self.configure_section_stack.add_named(preset_page, "preset")
        self.configure_section_stack.add_named(asus_page, "asus")

        self.update_configure_visible_page()

        return self.configure_section_stack

    def build_choose_vm_page(self):
        page_box = self.build_page_box()

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        content_box.set_valign(Gtk.Align.CENTER)
        content_box.set_halign(Gtk.Align.CENTER)
        content_box.set_vexpand(True)

        title_label = Gtk.Label(label="Choose VM")
        content_box.append(title_label)

        radio_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        radio_box.set_halign(Gtk.Align.CENTER)

        first_radio_button = None

        for virtual_machine_name in self.available_virtual_machines:
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
            row_box.set_halign(Gtk.Align.CENTER)

            radio_button = Gtk.CheckButton()
            if first_radio_button is None:
                first_radio_button = radio_button
            else:
                radio_button.set_group(first_radio_button)

            radio_button.connect("toggled", self.on_virtual_machine_selected, virtual_machine_name)

            name_label = Gtk.Label(label=virtual_machine_name)

            row_box.append(radio_button)
            row_box.append(name_label)
            radio_box.append(row_box)

        content_box.append(radio_box)
        page_box.append(content_box)
        page_box.append(self.build_navigation_row("configure", show_previous=False, show_next=True))

        return page_box

    def build_vm_cpu_pinning_page(self):
        page_box = self.build_page_box()

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        content_box.set_valign(Gtk.Align.CENTER)
        content_box.set_halign(Gtk.Align.CENTER)
        content_box.set_vexpand(True)

        title_label = Gtk.Label(label="VM CPU\nPINNING")
        title_label.set_justify(Gtk.Justification.CENTER)
        content_box.append(title_label)

        pinning_grid = self.build_cpu_pinning_grid(self.vm_cpu_pinning_checkbuttons)
        content_box.append(pinning_grid)

        page_box.append(content_box)
        page_box.append(self.build_navigation_row("configure", show_previous=True, show_next=True))

        return page_box

    def build_emulator_cpu_pinning_page(self):
        page_box = self.build_page_box()

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        content_box.set_valign(Gtk.Align.CENTER)
        content_box.set_halign(Gtk.Align.CENTER)
        content_box.set_vexpand(True)

        title_label = Gtk.Label(label="EMULATOR\nCPU\nPINNING")
        title_label.set_justify(Gtk.Justification.CENTER)
        content_box.append(title_label)

        pinning_grid = self.build_cpu_pinning_grid(self.emulator_cpu_pinning_checkbuttons)
        content_box.append(pinning_grid)

        page_box.append(content_box)
        page_box.append(self.build_navigation_row("configure", show_previous=True, show_next=True))

        return page_box

    def build_preset_page(self):
        page_box = self.build_page_box()

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        content_box.set_valign(Gtk.Align.CENTER)
        content_box.set_halign(Gtk.Align.CENTER)
        content_box.set_vexpand(True)

        title_label = Gtk.Label(label="Select\nPreset")
        title_label.set_justify(Gtk.Justification.CENTER)
        content_box.append(title_label)

        radio_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=28)
        radio_box.set_halign(Gtk.Align.CENTER)

        default_radio_button = Gtk.CheckButton()
        default_radio_button.connect("toggled", self.on_preset_selected, "Default")

        gaming_radio_button = Gtk.CheckButton()
        gaming_radio_button.set_group(default_radio_button)
        gaming_radio_button.connect("toggled", self.on_preset_selected, "Gaming")

        radio_box.append(self.build_radio_row(default_radio_button, "Default"))
        radio_box.append(self.build_radio_row(gaming_radio_button, "Gaming"))

        content_box.append(radio_box)
        page_box.append(content_box)
        page_box.append(self.build_navigation_row("configure", show_previous=True, show_next=True))

        return page_box

    def build_asus_laptop_page(self):
        page_box = self.build_page_box()

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        content_box.set_valign(Gtk.Align.CENTER)
        content_box.set_halign(Gtk.Align.CENTER)
        content_box.set_vexpand(True)

        title_label = Gtk.Label(label="Are you\nusing an\nAsus\ngaming\nlaptop?")
        title_label.set_justify(Gtk.Justification.CENTER)
        content_box.append(title_label)

        radio_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=28)
        radio_box.set_halign(Gtk.Align.CENTER)

        yes_radio_button = Gtk.CheckButton()
        yes_radio_button.connect("toggled", self.on_asus_laptop_answer_selected, "Yes")

        no_radio_button = Gtk.CheckButton()
        no_radio_button.set_group(yes_radio_button)
        no_radio_button.connect("toggled", self.on_asus_laptop_answer_selected, "No")

        radio_box.append(self.build_radio_row(yes_radio_button, "Yes"))
        radio_box.append(self.build_radio_row(no_radio_button, "No"))

        content_box.append(radio_box)
        page_box.append(content_box)
        page_box.append(self.build_navigation_row("configure", show_previous=True, show_next=True))

        return page_box

    # -------------------------------------------------
    # Create section
    # -------------------------------------------------

    def build_create_section(self):
        self.create_section_stack = Gtk.Stack()
        self.create_section_stack.set_hexpand(True)
        self.create_section_stack.set_vexpand(True)

        create_vm_name_page = self.build_create_vm_name_page()
        create_iso_page = self.build_create_iso_page()
        create_resources_page = self.build_create_resources_page()

        self.create_section_stack.add_named(create_vm_name_page, "create_vm_name")
        self.create_section_stack.add_named(create_iso_page, "create_iso")
        self.create_section_stack.add_named(create_resources_page, "create_resources")

        self.update_create_visible_page()

        return self.create_section_stack

    def build_create_vm_name_page(self):
        page_box = self.build_page_box()

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=28)
        content_box.set_valign(Gtk.Align.CENTER)
        content_box.set_halign(Gtk.Align.CENTER)
        content_box.set_vexpand(True)

        title_label = Gtk.Label(label="Create VM")
        content_box.append(title_label)

        row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row_box.set_halign(Gtk.Align.CENTER)

        name_label = Gtk.Label(label="Enter VM Name:")
        self.create_vm_name_entry = Gtk.Entry()
        self.create_vm_name_entry.set_width_chars(16)

        row_box.append(name_label)
        row_box.append(self.create_vm_name_entry)

        content_box.append(row_box)
        page_box.append(content_box)
        page_box.append(self.build_navigation_row("create", show_previous=False, show_next=True))

        return page_box

    def build_create_iso_page(self):
        page_box = self.build_page_box()

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=36)
        content_box.set_valign(Gtk.Align.CENTER)
        content_box.set_halign(Gtk.Align.CENTER)
        content_box.set_vexpand(True)

        title_label = Gtk.Label(label="Choose ISO")
        content_box.append(title_label)

        iso_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        iso_row.set_halign(Gtk.Align.CENTER)

        iso_label = Gtk.Label(label="ISO Path:")
        self.create_iso_path_entry = Gtk.Entry()
        self.create_iso_path_entry.set_width_chars(18)

        browse_button = Gtk.Button(label="Browse")
        browse_button.connect("clicked", self.on_browse_iso_clicked)

        iso_row.append(iso_label)
        iso_row.append(self.create_iso_path_entry)
        iso_row.append(browse_button)

        os_variant_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        os_variant_row.set_halign(Gtk.Align.CENTER)

        os_variant_label = Gtk.Label(label="Choose OS-Variant")

        os_variant_string_list = Gtk.StringList.new(self.available_os_variants)
        self.create_os_variant_dropdown = Gtk.DropDown.new(os_variant_string_list, None)
        self.create_os_variant_dropdown.set_size_request(180, -1)

        os_variant_row.append(os_variant_label)
        os_variant_row.append(self.create_os_variant_dropdown)

        content_box.append(iso_row)
        content_box.append(os_variant_row)

        page_box.append(content_box)
        page_box.append(self.build_navigation_row("create", show_previous=True, show_next=True))

        return page_box

    def build_create_resources_page(self):
        page_box = self.build_page_box()

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        content_box.set_valign(Gtk.Align.CENTER)
        content_box.set_halign(Gtk.Align.CENTER)
        content_box.set_vexpand(True)

        title_label = Gtk.Label(label="Resource\nAllocation")
        title_label.set_justify(Gtk.Justification.CENTER)
        content_box.append(title_label)

        grid = Gtk.Grid()
        grid.set_row_spacing(18)
        grid.set_column_spacing(12)
        grid.set_halign(Gtk.Align.CENTER)

        memory_label = Gtk.Label(label="Memory:")
        self.create_memory_entry = Gtk.Entry()
        self.create_memory_entry.set_width_chars(12)
        memory_unit_label = Gtk.Label(label="MiB")

        cpu_label = Gtk.Label(label="CPUs:")
        self.create_cpu_entry = Gtk.Entry()
        self.create_cpu_entry.set_width_chars(12)

        storage_label = Gtk.Label(label="Storage:")
        self.create_storage_entry = Gtk.Entry()
        self.create_storage_entry.set_width_chars(12)
        storage_unit_label = Gtk.Label(label="GiB")

        grid.attach(memory_label, 0, 0, 1, 1)
        grid.attach(self.create_memory_entry, 1, 0, 1, 1)
        grid.attach(memory_unit_label, 2, 0, 1, 1)

        grid.attach(cpu_label, 0, 1, 1, 1)
        grid.attach(self.create_cpu_entry, 1, 1, 1, 1)

        grid.attach(storage_label, 0, 2, 1, 1)
        grid.attach(self.create_storage_entry, 1, 2, 1, 1)
        grid.attach(storage_unit_label, 2, 2, 1, 1)

        content_box.append(grid)

        page_box.append(content_box)
        page_box.append(self.build_navigation_row("create", show_previous=True, show_next=True))

        return page_box

    # -------------------------------------------------
    # Passthrough section
    # -------------------------------------------------

    def build_passthrough_section(self):
        self.passthrough_section_stack = Gtk.Stack()
        self.passthrough_section_stack.set_hexpand(True)
        self.passthrough_section_stack.set_vexpand(True)

        select_gpu_page = self.build_select_gpu_page()
        enable_vfio_page = self.build_enable_vfio_page()

        self.passthrough_section_stack.add_named(select_gpu_page, "select_gpu")
        self.passthrough_section_stack.add_named(enable_vfio_page, "enable_vfio")

        self.update_passthrough_visible_page()

        return self.passthrough_section_stack

    def build_select_gpu_page(self):
        page_box = self.build_page_box()

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        content_box.set_valign(Gtk.Align.CENTER)
        content_box.set_halign(Gtk.Align.CENTER)
        content_box.set_vexpand(True)

        title_label = Gtk.Label(label="Select GPU")
        content_box.append(title_label)

        radio_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=28)
        radio_box.set_halign(Gtk.Align.CENTER)

        nvidia_radio_button = Gtk.CheckButton()
        nvidia_radio_button.connect("toggled", self.on_gpu_vendor_selected, "Nvidia")

        amd_radio_button = Gtk.CheckButton()
        amd_radio_button.set_group(nvidia_radio_button)
        amd_radio_button.connect("toggled", self.on_gpu_vendor_selected, "AMD")

        radio_box.append(self.build_radio_row(nvidia_radio_button, "Nvidia"))
        radio_box.append(self.build_radio_row(amd_radio_button, "AMD"))

        content_box.append(radio_box)

        page_box.append(content_box)
        page_box.append(self.build_navigation_row("passthrough", show_previous=False, show_next=True))

        return page_box

    def build_enable_vfio_page(self):
        page_box = self.build_page_box()

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        content_box.set_valign(Gtk.Align.CENTER)
        content_box.set_halign(Gtk.Align.CENTER)
        content_box.set_vexpand(True)

        title_label = Gtk.Label(label="Enable VFIO?")
        content_box.append(title_label)

        radio_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=28)
        radio_box.set_halign(Gtk.Align.CENTER)

        yes_radio_button = Gtk.CheckButton()
        yes_radio_button.connect("toggled", self.on_vfio_answer_selected, "Yes")

        no_radio_button = Gtk.CheckButton()
        no_radio_button.set_group(yes_radio_button)
        no_radio_button.connect("toggled", self.on_vfio_answer_selected, "No")

        radio_box.append(self.build_radio_row(yes_radio_button, "Yes"))
        radio_box.append(self.build_radio_row(no_radio_button, "No"))

        content_box.append(radio_box)

        page_box.append(content_box)
        page_box.append(self.build_navigation_row("passthrough", show_previous=True, show_next=True))

        return page_box

    # -------------------------------------------------
    # Shared UI helpers
    # -------------------------------------------------

    def build_page_box(self):
        page_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        page_box.set_hexpand(True)
        page_box.set_vexpand(True)
        page_box.set_margin_top(20)
        page_box.set_margin_bottom(20)
        page_box.set_margin_start(30)
        page_box.set_margin_end(30)
        return page_box

    def build_radio_row(self, radio_button, label_text):
        row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        row_box.set_halign(Gtk.Align.CENTER)

        label = Gtk.Label(label=label_text)

        row_box.append(radio_button)
        row_box.append(label)

        return row_box

    def build_cpu_pinning_grid(self, checkbutton_dictionary):
        grid = Gtk.Grid()
        grid.set_column_spacing(26)
        grid.set_row_spacing(18)
        grid.set_halign(Gtk.Align.CENTER)
        grid.set_valign(Gtk.Align.CENTER)

        thread_0_label = Gtk.Label(label="Thread 0")
        thread_1_label = Gtk.Label(label="Thread 1")
        thread_2_label = Gtk.Label(label="Thread 2")
        thread_3_label = Gtk.Label(label="Thread 3")

        core_0_label = Gtk.Label(label="Core 0")
        core_1_label = Gtk.Label(label="Core 1")

        thread_0_checkbutton = Gtk.CheckButton()
        thread_1_checkbutton = Gtk.CheckButton()
        thread_2_checkbutton = Gtk.CheckButton()
        thread_3_checkbutton = Gtk.CheckButton()

        checkbutton_dictionary["thread_0"] = thread_0_checkbutton
        checkbutton_dictionary["thread_1"] = thread_1_checkbutton
        checkbutton_dictionary["thread_2"] = thread_2_checkbutton
        checkbutton_dictionary["thread_3"] = thread_3_checkbutton

        grid.attach(thread_0_label, 1, 0, 1, 1)
        grid.attach(thread_1_label, 2, 0, 1, 1)

        grid.attach(core_0_label, 0, 1, 1, 1)
        grid.attach(thread_0_checkbutton, 1, 1, 1, 1)
        grid.attach(thread_1_checkbutton, 2, 1, 1, 1)

        grid.attach(thread_2_label, 1, 2, 1, 1)
        grid.attach(thread_3_label, 2, 2, 1, 1)

        grid.attach(core_1_label, 0, 3, 1, 1)
        grid.attach(thread_2_checkbutton, 1, 3, 1, 1)
        grid.attach(thread_3_checkbutton, 2, 3, 1, 1)

        return grid

    def build_navigation_row(self, section_name, show_previous, show_next):
        navigation_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        navigation_box.set_hexpand(True)
        navigation_box.set_margin_top(20)

        previous_button = Gtk.Button(label="Previous")
        previous_button.connect("clicked", self.on_previous_clicked, section_name)

        next_button = Gtk.Button(label="Next")
        next_button.connect("clicked", self.on_next_clicked, section_name)

        if show_previous:
            navigation_box.append(previous_button)
        else:
            left_spacer = Gtk.Box()
            left_spacer.set_size_request(80, 1)
            navigation_box.append(left_spacer)

        center_spacer = Gtk.Box()
        center_spacer.set_hexpand(True)
        navigation_box.append(center_spacer)

        if show_next:
            navigation_box.append(next_button)

        return navigation_box

    # -------------------------------------------------
    # Sidebar actions
    # -------------------------------------------------

    def on_sidebar_configure_clicked(self, button):
        self.main_section_stack.set_visible_child_name("configure")

    def on_sidebar_create_clicked(self, button):
        self.main_section_stack.set_visible_child_name("create")

    def on_sidebar_passthrough_clicked(self, button):
        self.main_section_stack.set_visible_child_name("passthrough")

    # -------------------------------------------------
    # Configure actions
    # -------------------------------------------------

    def on_virtual_machine_selected(self, check_button, virtual_machine_name):
        if check_button.get_active():
            self.selected_virtual_machine = virtual_machine_name
            print("Selected VM:", self.selected_virtual_machine)

    def on_preset_selected(self, check_button, preset_name):
        if check_button.get_active():
            self.selected_preset = preset_name
            print("Selected preset:", self.selected_preset)

    def on_asus_laptop_answer_selected(self, check_button, answer_text):
        if check_button.get_active():
            self.selected_asus_laptop_answer = answer_text
            print("Asus gaming laptop:", self.selected_asus_laptop_answer)

    def update_configure_visible_page(self):
        page_name = self.configure_page_names[self.configure_page_index]
        self.configure_section_stack.set_visible_child_name(page_name)

    def print_configure_results(self):
        vm_cpu_pinning_values = self.get_checkbutton_values(self.vm_cpu_pinning_checkbuttons)
        emulator_cpu_pinning_values = self.get_checkbutton_values(self.emulator_cpu_pinning_checkbuttons)

        print()
        print("Configure wizard results")
        print("------------------------")
        print("Selected VM:", self.selected_virtual_machine)
        print("VM CPU pinning:", vm_cpu_pinning_values)
        print("Emulator CPU pinning:", emulator_cpu_pinning_values)
        print("Preset:", self.selected_preset)
        print("Asus gaming laptop:", self.selected_asus_laptop_answer)
        print()

    # -------------------------------------------------
    # Create actions
    # -------------------------------------------------

    def update_create_visible_page(self):
        page_name = self.create_page_names[self.create_page_index]
        self.create_section_stack.set_visible_child_name(page_name)

    def on_browse_iso_clicked(self, button):
        file_chooser = Gtk.FileChooserNative(
            title="Choose ISO",
            transient_for=self,
            action=Gtk.FileChooserAction.OPEN,
            accept_label="Open",
            cancel_label="Cancel",
        )

        file_filter = Gtk.FileFilter()
        file_filter.set_name("ISO files")
        file_filter.add_pattern("*.iso")
        file_chooser.add_filter(file_filter)

        file_chooser.connect("response", self.on_iso_file_dialog_response)
        file_chooser.show()

    def on_iso_file_dialog_response(self, file_chooser, response):
        if response == Gtk.ResponseType.ACCEPT:
            selected_file = file_chooser.get_file()
            if selected_file is not None:
                selected_path = selected_file.get_path()
                if selected_path is not None:
                    self.create_iso_path_entry.set_text(selected_path)

    def print_create_results(self):
        selected_index = self.create_os_variant_dropdown.get_selected()
        selected_os_variant = None

        if selected_index != Gtk.INVALID_LIST_POSITION:
            selected_os_variant = self.available_os_variants[selected_index]

        print()
        print("Create VM wizard results")
        print("------------------------")
        print("VM name:", self.create_vm_name_entry.get_text())
        print("ISO path:", self.create_iso_path_entry.get_text())
        print("OS variant:", selected_os_variant)
        print("Memory MiB:", self.create_memory_entry.get_text())
        print("CPUs:", self.create_cpu_entry.get_text())
        print("Storage GiB:", self.create_storage_entry.get_text())
        print()

    # -------------------------------------------------
    # Passthrough actions
    # -------------------------------------------------

    def on_gpu_vendor_selected(self, check_button, gpu_vendor_name):
        if check_button.get_active():
            self.selected_gpu_vendor = gpu_vendor_name
            print("Selected GPU vendor:", self.selected_gpu_vendor)

    def on_vfio_answer_selected(self, check_button, answer_text):
        if check_button.get_active():
            self.selected_vfio_answer = answer_text
            print("Enable VFIO:", self.selected_vfio_answer)

    def update_passthrough_visible_page(self):
        page_name = self.passthrough_page_names[self.passthrough_page_index]
        self.passthrough_section_stack.set_visible_child_name(page_name)

    def print_passthrough_results(self):
        print()
        print("Passthrough wizard results")
        print("--------------------------")
        print("GPU vendor:", self.selected_gpu_vendor)
        print("Enable VFIO:", self.selected_vfio_answer)
        print()

    # -------------------------------------------------
    # Shared navigation
    # -------------------------------------------------

    def on_previous_clicked(self, button, section_name):
        if section_name == "configure":
            if self.configure_page_index > 0:
                self.configure_page_index -= 1
                self.update_configure_visible_page()

        elif section_name == "create":
            if self.create_page_index > 0:
                self.create_page_index -= 1
                self.update_create_visible_page()

        elif section_name == "passthrough":
            if self.passthrough_page_index > 0:
                self.passthrough_page_index -= 1
                self.update_passthrough_visible_page()

    def on_next_clicked(self, button, section_name):
        if section_name == "configure":
            if self.configure_page_index < len(self.configure_page_names) - 1:
                self.configure_page_index += 1
                self.update_configure_visible_page()
            else:
                self.print_configure_results()

        elif section_name == "create":
            if self.create_page_index < len(self.create_page_names) - 1:
                self.create_page_index += 1
                self.update_create_visible_page()
            else:
                self.print_create_results()

        elif section_name == "passthrough":
            if self.passthrough_page_index < len(self.passthrough_page_names) - 1:
                self.passthrough_page_index += 1
                self.update_passthrough_visible_page()
            else:
                self.print_passthrough_results()

    def get_checkbutton_values(self, checkbutton_dictionary):
        values = {}

        for thread_name, checkbutton in checkbutton_dictionary.items():
            values[thread_name] = checkbutton.get_active()

        return values


class VMTuneApplication(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.example.vmtune")

    def do_activate(self):
        window = VMTuneWindow(self)
        window.present()


def main():
    application = VMTuneApplication()
    application.run(None)


if __name__ == "__main__":
    main()