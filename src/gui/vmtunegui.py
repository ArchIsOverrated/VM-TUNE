#!/usr/bin/env python3

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio, GLib
import sys
sys.path.append("..")
import api
import subprocess

lib_dir = "/usr/local/lib/VMTUNE/"
script_location = "/usr/local/bin/vmtune"

class VMTuneWindow(Gtk.ApplicationWindow):
    def __init__(self, application):
        super().__init__(application=application)

        self.set_title("VM-TUNE")
        self.set_default_size(888, 500)

        self.configure_page_index = 0
        self.create_page_index = 0
        self.passthrough_page_index = 0

        virtual_machine_query = api.configure_vm.query(script_location,"vms")
        self.available_virtual_machines = virtual_machine_query["vms"]

        os_variants_query = api.create_vm.query(script_location,"os-variants")
        self.available_os_variants = os_variants_query["os_variants"]

        cpu_topology_query = api.configure_vm.query(script_location,"cpu-topology")
        self.cpu_topology = cpu_topology_query

        gpu_query = api.gpu_passthrough.query(script_location,"gpus")
        self.available_gpus = gpu_query["gpus"]

        print(type(self.available_gpus))
        print(self.available_gpus)
        print(type(self.available_gpus[0]))
        print(self.available_gpus[0])

        

        self.selected_virtual_machine = None
        self.selected_preset = None
        self.selected_asus_laptop_answer = None

        self.selected_gpu_name = None
        self.selected_gpu_ids = None
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
            "configure_choose_vm",
            "configure_vm_cpu_pinning",
            "configure_emulator_cpu_pinning",
            "configure_preset",
            "configure_asus",
            "configure_confirm"
        ]

        self.create_page_names = [
            "create_vm_name",
            "create_iso",
            "create_resources",
            "create_confirm"
        ]

        self.passthrough_page_names = [
            "passthrough_select_gpu",
            "passthrough_enable_vfio",
            "passthrough_confirm"
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
        sidebar_box.set_size_request(-1, -1)

        configure_button = self.build_sidebar_button("Configure", self.on_sidebar_configure_clicked)
        create_button = self.build_sidebar_button("Create", self.on_sidebar_create_clicked)
        passthrough_button = self.build_sidebar_button("Passthrough", self.on_sidebar_passthrough_clicked)

        sidebar_box.append(configure_button)
        sidebar_box.append(create_button)
        sidebar_box.append(passthrough_button)

        return sidebar_box

    def build_sidebar_button(self, label_text, clicked_handler):
        button = Gtk.Button(label=label_text)
        button.set_size_request(-1, -1)
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
        confirm_page = self.build_configure_confirm_page()

        self.configure_section_stack.add_named(choose_vm_page, "configure_choose_vm")
        self.configure_section_stack.add_named(vm_cpu_pinning_page, "configure_vm_cpu_pinning")
        self.configure_section_stack.add_named(emulator_cpu_pinning_page, "configure_emulator_cpu_pinning")
        self.configure_section_stack.add_named(preset_page, "configure_preset")
        self.configure_section_stack.add_named(asus_page, "configure_asus")
        self.configure_section_stack.add_named(confirm_page,"configure_confirm")

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

        pinning_grid = self.build_cpu_pinning_grid(self.vm_cpu_pinning_checkbuttons,self.cpu_topology)
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
        pinning_grid = self.build_cpu_pinning_grid(self.emulator_cpu_pinning_checkbuttons,self.cpu_topology)
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
        default_radio_button.connect("toggled", self.on_preset_selected, "1")

        gaming_radio_button = Gtk.CheckButton()
        gaming_radio_button.set_group(default_radio_button)
        gaming_radio_button.connect("toggled", self.on_preset_selected, "2")

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
        yes_radio_button.connect("toggled", self.on_asus_laptop_answer_selected, 1)

        no_radio_button = Gtk.CheckButton()
        no_radio_button.set_group(yes_radio_button)
        no_radio_button.connect("toggled", self.on_asus_laptop_answer_selected, 2)

        radio_box.append(self.build_radio_row(yes_radio_button, "Yes"))
        radio_box.append(self.build_radio_row(no_radio_button, "No"))

        content_box.append(radio_box)
        page_box.append(content_box)
        page_box.append(self.build_navigation_row("configure", show_previous=True, show_next=True))

        return page_box

    def build_configure_confirm_page(self):

        print("----------------------------------------------------")
        print("building the confirm page")
        page_box = self.build_page_box()

        vm_cpu_pinning_values = self.get_checkbutton_values(self.vm_cpu_pinning_checkbuttons)
        emulator_cpu_pinning_values = self.get_checkbutton_values(self.emulator_cpu_pinning_checkbuttons)

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        content_box.set_valign(Gtk.Align.CENTER)
        content_box.set_halign(Gtk.Align.CENTER)
        content_box.set_vexpand(True)

        title_label = Gtk.Label(label="Confirm results")
        title_label.set_justify(Gtk.Justification.CENTER)
        content_box.append(title_label)

        print("Selected VM:",self.selected_virtual_machine)
        selected_vm_string="Selected VM: "+str(self.selected_virtual_machine)
        selected_vm_label = Gtk.Label(label=selected_vm_string)
        content_box.append(selected_vm_label)

        print("VM CPU pinning:",vm_cpu_pinning_values)
        cpu_pinning_string="VM CPU pinning: "+str(vm_cpu_pinning_values)
        cpu_pinning_label = Gtk.Label(label=cpu_pinning_string)
        content_box.append(cpu_pinning_label)

        print("Emulator CPU pinning:",emulator_cpu_pinning_values)
        emulator_pinning_string="Emulator CPU pinning: "+str(emulator_cpu_pinning_values)
        emulator_pinning_label = Gtk.Label(label=emulator_pinning_string)
        content_box.append(emulator_pinning_label)

        print("VM Preset:",self.selected_preset)
        selected_preset_string="VM Preset: "+str(self.selected_preset)
        preset_label = Gtk.Label(label=selected_preset_string)
        content_box.append(preset_label)

        print("Asus gaming laptop:",self.selected_asus_laptop_answer)
        asus_laptop_string="Asus gaming laptop: "+str(self.selected_asus_laptop_answer)
        selected_vm_label = Gtk.Label(label=asus_laptop_string)
        content_box.append(selected_vm_label)

        apply_button = Gtk.Button(label="Apply")
        apply_button.connect("clicked", self.apply_configure_changes)
        content_box.append(apply_button)

        page_box.append(content_box)
        page_box.append(self.build_navigation_row("configure",show_previous=True, show_next=False))

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
        create_confirm_page = self.build_create_confirm_page()

        self.create_section_stack.add_named(create_vm_name_page, "create_vm_name")
        self.create_section_stack.add_named(create_iso_page, "create_iso")
        self.create_section_stack.add_named(create_resources_page, "create_resources")
        self.create_section_stack.add_named(create_confirm_page,"create_confirm")

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

    def build_create_confirm_page(self):
        page_box = self.build_page_box()

        vm_cpu_pinning_values = self.get_checkbutton_values(self.vm_cpu_pinning_checkbuttons)
        emulator_cpu_pinning_values = self.get_checkbutton_values(self.emulator_cpu_pinning_checkbuttons)

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        content_box.set_valign(Gtk.Align.CENTER)
        content_box.set_halign(Gtk.Align.CENTER)
        content_box.set_vexpand(True)

        title_label = Gtk.Label(label="Confirm results")
        title_label.set_justify(Gtk.Justification.CENTER)
        content_box.append(title_label)

        vm_name_string="VM name: "+str(self.create_vm_name_entry.get_text())
        vm_name_label = Gtk.Label(label=vm_name_string)
        content_box.append(vm_name_label)

        iso_path_string="ISO Path: "+str(self.create_iso_path_entry.get_text())      
        iso_path_label = Gtk.Label(label=iso_path_string)
        content_box.append(iso_path_label)

        selected_index = self.create_os_variant_dropdown.get_selected()
        selected_os_variant = None

        if selected_index != Gtk.INVALID_LIST_POSITION:
            selected_os_variant = self.available_os_variants[selected_index]

        os_variant_string ="OS variant: "+selected_os_variant
        os_variant_label = Gtk.Label(label=os_variant_string)
        content_box.append(os_variant_label)

        os_memory_string = "Memory MiB: "+ self.create_memory_entry.get_text()
        os_memory_label = Gtk.Label(label=os_memory_string)
        content_box.append(os_memory_label)

        cpu_string = "CPUs: " + self.create_cpu_entry.get_text()
        cpu_label = Gtk.Label(label=cpu_string)
        content_box.append(cpu_label)

        storage_string = "Storage GiB: " + self.create_storage_entry.get_text()
        storage_label = Gtk.Label(label=storage_string)
        content_box.append(storage_label)

        apply_button = Gtk.Button(label="Apply")
        apply_button.connect("clicked", self.apply_create_vm_changes)
        content_box.append(apply_button)

        page_box.append(content_box)
        page_box.append(self.build_navigation_row("configure",show_previous=True, show_next=False))

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
        confirm_page = self.build_passthrough_confirm_page()

        self.passthrough_section_stack.add_named(select_gpu_page, "passthrough_select_gpu")
        self.passthrough_section_stack.add_named(enable_vfio_page, "passthrough_enable_vfio")
        self.passthrough_section_stack.add_named(confirm_page,"passthrough_confirm")

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

        print("gpus")
        radio_buttons = []
        for index in range(len(self.available_gpus)):
            radio_buttons.append(Gtk.CheckButton())
            radio_buttons[index].set_group(radio_buttons[0])
            radio_buttons[index].connect("toggled",self.on_gpu_vendor_selected,self.available_gpus[index]['name'],self.available_gpus[index]['ids'])
            radio_box.append(self.build_radio_row(radio_buttons[index], self.available_gpus[index]['name']))

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
        yes_radio_button.connect("toggled", self.on_vfio_answer_selected, 1)

        no_radio_button = Gtk.CheckButton()
        no_radio_button.set_group(yes_radio_button)
        no_radio_button.connect("toggled", self.on_vfio_answer_selected, 0)

        radio_box.append(self.build_radio_row(yes_radio_button, "Yes"))
        radio_box.append(self.build_radio_row(no_radio_button, "No"))

        content_box.append(radio_box)

        page_box.append(content_box)
        page_box.append(self.build_navigation_row("passthrough", show_previous=True, show_next=True))

        return page_box

    def build_passthrough_confirm_page(self):
        page_box = self.build_page_box()

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        content_box.set_valign(Gtk.Align.CENTER)
        content_box.set_halign(Gtk.Align.CENTER)
        content_box.set_vexpand(True)

        title_label = Gtk.Label(label="Confirm results")
        title_label.set_justify(Gtk.Justification.CENTER)
        content_box.append(title_label)

        gpu_label = Gtk.Label(label="Selected GPU: "+str(self.selected_gpu_name))
        content_box.append(gpu_label)

        vfio_mode_label = Gtk.Label(label="VFIO Mode: "+str(self.selected_vfio_answer))
        content_box.append(vfio_mode_label)

        apply_button = Gtk.Button(label="Apply")
        apply_button.connect("clicked", self.apply_passthrough_changes)
        content_box.append(apply_button)

        page_box.append(content_box)
        page_box.append(self.build_navigation_row("configure",show_previous=True, show_next=False))

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

    def build_cpu_pinning_grid(self, checkbutton_dictionary, cpu_topology):
        #note to self to make this build based off of cpu layout
        grid = Gtk.Grid()
        grid.set_column_spacing(26)
        grid.set_row_spacing(18)
        grid.set_halign(Gtk.Align.CENTER)
        grid.set_valign(Gtk.Align.CENTER)

        cpu_vendor = cpu_topology["vendor"]
        cpu_cores = cpu_topology["cores"]

        index=0
        thread_labels = []
        thread_checkbuttons = []
        for cpu in cpu_cores:
            cpu_split = []
            if cpu_vendor == "intel":
                cpu_split = cpu.split("-")
            elif cpu_vendor == "amd":
                cpu_split = cpu.split(",")
                
            for thread in cpu_split:
                label_string = "Thread " + str(index)
                thread_labels.append(Gtk.Label(label = label_string))
                thread_checkbuttons.append(Gtk.CheckButton())
                index=index+1

        core_labels = []
        for cpu in range(len(cpu_cores)):
            label_string = "Core " + str(cpu)
            core_labels.append(Gtk.Label(label = label_string))

        index=0
        for thread in range(len(thread_labels)):
            label_string = "thread_" + str(index)
            checkbutton_dictionary[label_string] = thread_checkbuttons[index]
            index=index+1
        
        cpu_index = 0
        thread_index = 0
        for cpu in cpu_cores:
            grid.attach(core_labels[cpu_index],0,(1+(cpu_index*2)),1,1)
            cpu_split = []
            if cpu_vendor == "intel":
                cpu_split = cpu.split("-")
            elif cpu_vendor == "amd":
                cpu_split = cpu.split(",")

            for thread in cpu_split:
                grid.attach(thread_labels[thread_index],(1+(thread_index % 2)),(0+(cpu_index*2)),1,1)
                grid.attach(thread_checkbuttons[thread_index],(1+(thread_index % 2)),(1+(cpu_index*2)),1,1)
                thread_index = thread_index + 1
            cpu_index = cpu_index + 1
                    
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

    def apply_configure_changes(self,apply_button):
        vm_cpu_pinning_values = self.get_checkbutton_values(self.vm_cpu_pinning_checkbuttons)
        emulator_cpu_pinning_values = self.get_checkbutton_values(self.emulator_cpu_pinning_checkbuttons)
        print()
        print("Configure wizard results")
        print("------------------------")
        print("Selected VM:", self.selected_virtual_machine,type(self.selected_virtual_machine))
        print("VM CPU pinning:", vm_cpu_pinning_values,type(vm_cpu_pinning_values))
        print("Emulator CPU pinning:", emulator_cpu_pinning_values,type(emulator_cpu_pinning_values))
        print("Preset:", self.selected_preset,type(self.selected_preset))
        print("Asus gaming laptop:", self.selected_asus_laptop_answer,type(self.selected_asus_laptop_answer))
        print()
        
        api.configure_vm.action(script_location,
        "configure",
        vm=self.selected_virtual_machine,
        cpu=vm_cpu_pinning_values,
        emulator=emulator_cpu_pinning_values,
        preset=self.selected_preset,
        laptop=self.selected_asus_laptop_answer,
        libdir=lib_dir)


    # -------------------------------------------------
    # Create actions
    # -------------------------------------------------

    def update_create_visible_page(self):
        page_name = self.create_page_names[self.create_page_index]
        self.create_section_stack.set_visible_child_name(page_name)
    
    def on_browse_iso_clicked(self, sender):
        iso_file_filter = Gtk.FileFilter()
        iso_file_filter.set_name("ISO files")
        iso_file_filter.add_pattern("*.iso")

        file_filter_list = Gio.ListStore.new(Gtk.FileFilter)
        file_filter_list.append(iso_file_filter)

        iso_file_dialog = Gtk.FileDialog(
            title="Choose ISO",
            filters=file_filter_list,
        )
        iso_file_dialog.open(self, None, self.on_iso_file_dialog_response)

    def on_iso_file_dialog_response(self, iso_file_dialog, async_result):
        try:
            selected_file = iso_file_dialog.open_finish(async_result)
        except GLib.Error:
            return

        if selected_file is None:
            return

        selected_path = selected_file.get_path()

        if selected_path is None:
            return

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

    def apply_create_vm_changes(self,apply_button):
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
        
        api.create_vm.action(script_location,
        "create",
        vm=self.create_vm_name_entry.get_text(),
        iso=self.create_iso_path_entry.get_text(),
        disk=self.create_storage_entry.get_text(),
        ram=self.create_memory_entry.get_text(),
        cpu=self.create_cpu_entry.get_text(),
        osvariant=selected_os_variant,
        libdir=lib_dir)

    # -------------------------------------------------
    # Passthrough actions
    # -------------------------------------------------

    def on_gpu_vendor_selected(self, check_button, gpu_vendor_name, gpu_ids):
        if check_button.get_active():
            self.selected_gpu_name = gpu_vendor_name
            self.selected_gpu_ids = gpu_ids
            print("Selected GPU vendor:", self.selected_gpu_name)

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
        print("GPU vendor:", self.selected_gpu_name)
        print("GPU ids:", self.selected_gpu_ids)
        print("Enable VFIO:", self.selected_vfio_answer)
        print()
    
    def apply_passthrough_changes(self,apply_button):
        print()
        print("Passthrough wizard results")
        print("--------------------------")
        print("GPU vendor:", self.selected_gpu_name)
        print("GPU ids:", self.selected_gpu_ids)
        print("Enable VFIO:", self.selected_vfio_answer)
        print()
        api.gpu_passthrough.action(script_location,
        "set",
        vfio=self.selected_vfio_answer,
        gpuids=self.selected_gpu_ids,
        libdir=lib_dir)

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
            print("configure")
            if self.configure_page_index < len(self.configure_page_names) - 1:
                self.configure_page_index += 1
                self.update_configure_visible_page()

        elif section_name == "create":
            print("create")
            if self.create_page_index < len(self.create_page_names) - 1:
                self.create_page_index += 1
                self.update_create_visible_page()

        elif section_name == "passthrough":
            print("passthrough")
            if self.passthrough_page_index < len(self.passthrough_page_names) - 1:
                self.passthrough_page_index += 1
                self.update_passthrough_visible_page()

    def get_checkbutton_values(self, checkbutton_dictionary):
        values = {}
        comma_separated_list = ""
        index = 0
        for thread_name, checkbutton in checkbutton_dictionary.items():
            if checkbutton.get_active() == True:
                comma_separated_list=comma_separated_list+str(index)+","

            value = checkbutton.get_active()
            values[thread_name] = checkbutton.get_active()
            index=index+1

        comma_separated_list=comma_separated_list[:-1]

        return comma_separated_list


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