import tkinter as tk

from src.ui.ui_components.dialog_boxes import DialogBoxes
from src.ui.ui_components.ui_utils import UiUtils
from src.utils.xml_utils.uuid_regen_utils import UUIDRegenUtils


def regenerate_uuids_with_excel_report(menu_frame):
    """
        Shows a window that allows users to select an XML file. The selected XML file undergoes uuid regeneration
        and the changes are recorded in an Excel report. This helps in converting local landscape XML files
        to a global landscape XML file.

        Args:
            menu_frame (tk.Frame): The frame where the uuid regeneration window will be displayed.
        """

    # Clear the main window
    UiUtils.clear_frame(menu_frame)

    description_label = tk.Label(
        menu_frame,
        text="Warnings:\n\n"
             "1. This function will regenerate the uuids of services and items\n"
             "in your SAP UI Local Landscape Files (XML files), In order to make\n"
             "to make it usable as a Global Landscape File (XML file).\n\n"
             "2. This function will also remove any inclusions of SAPUIGlobalLandscape.xml\n"
             "in your output file, in order to make it usable as a global/central file and avoid errors \n\n"
             "3. This function will also generate an excel report of the changes made to the XML file\n\n",
        font=("Arial", 10, "bold"),
        bg="white",
        anchor='w',
        justify='left'
    )
    description_label.pack(pady=10)

    UiUtils.show_red_warning(menu_frame)

    file_label = tk.Label(menu_frame, text="\n\nPlease enter your local XML file",
                          font=("Arial", 10, "bold"),
                          bg="white")
    file_label.pack(pady=10)
    entry_frame = tk.Frame(menu_frame)
    entry_frame.pack(pady=10)
    xml_path_entry = tk.Entry(entry_frame, width=50)  # Entry widget to input XML file path
    xml_path_entry.pack(side='left')
    browse_button = tk.Button(entry_frame, text="Browse", command=lambda: DialogBoxes.xml_selection(xml_path_entry,
                                                                                                    "Select XML File"),
                              background="black",
                              foreground="white")
    browse_button.pack(side='left', padx=5)

    regenerate_uuids_button = tk.Button(entry_frame, text="Submit",
                                        command=lambda: UUIDRegenUtils.regenerate_uuids_export_excel(xml_path_entry.get()),
                                        background="black", foreground="white")

    regenerate_uuids_button.pack(side="left", pady=5)

    UiUtils.create_exit_restart_back_buttons(menu_frame)
