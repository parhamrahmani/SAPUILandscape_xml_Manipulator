import logging
import os
import sys
from tkinter import messagebox, simpledialog, filedialog
import tkinter as tk
from utils.excel_utils import *
import lxml.etree as le
import uuid
import uuid
import xml.etree.ElementTree as ET

from utils.excel_utils import generate_excel_files
import pandas as pd


# Function to regenerate UUIDs for workspaces
def select_xml_file(xml_path_entry):
    """
        Function for opening a file dialog to select an XML file,
        and populating the xml_path_entry field with the chosen file's path.
        """
    xml_file_path = filedialog.askopenfilename(initialdir="/", title="Select source XML file",
                                               filetypes=(("xml files", "*.xml"), ("all files", "*.*")))
    if xml_file_path:
        xml_path_entry.delete(0, tk.END)  # Clear the entry field
        xml_path_entry.insert(tk.END, xml_file_path)  # Insert the selected file path


def open_folder_containing_file(xml_file_path):
    folder_path = os.path.dirname(xml_file_path)
    os.startfile(folder_path)


def regenerate_workspace_uuids(workspaces):
    for workspace in workspaces:
        workspace.set('uuid', str(uuid.uuid4()))
        workspace.set('expanded', str(0))
        if workspace.get('name') == "Local" or workspace.get('name') == "local":
            workspace.set('name', "Default")


# Function to regenerate UUIDs for services and items
def regenerate_service_uuids(root):
    uuid_mapping = {}

    # Regenerate UUIDs for services
    for service in root.findall(".//Service"):
        old_uuid = service.get('uuid')
        new_uuid = str(uuid.uuid4())
        uuid_mapping[old_uuid] = new_uuid
        service.set('uuid', new_uuid)

    # Regenerate UUIDs for items and update service IDs
    for item in root.findall(".//Item"):
        item_uuid = item.get('uuid')
        new_item_uuid = str(uuid.uuid4())
        uuid_mapping[item_uuid] = new_item_uuid
        item.set('uuid', new_item_uuid)

        service_id = item.get('serviceid')
        if service_id in uuid_mapping:
            new_service_id = uuid_mapping[service_id]
            item.set('serviceid', new_service_id)


# Function to remove includes with URLs containing "SAPUILandscapeGlobal.xml"
def remove_global_includes(root):
    includes = root.findall(".//Include")
    filtered_includes = []

    for include in includes:
        include_url = include.get("url")
        if "SAPUILandscapeGlobal.xml" not in include_url:
            filtered_includes.append(include)

    if len(filtered_includes) < len(includes):

        root.findall(".//Includes")[0][:] = filtered_includes
        return True

    else:
        return False


def regenerate_uuids_export_excel(xml_file_path):
    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()

        workspaces = root.findall(".//Workspace")

        regenerate_workspace_uuids(workspaces)

        # Regenerating UUIDs
        for node in root.findall(".//Node"):
            node.set('uuid', str(uuid.uuid4()))

        regenerate_service_uuids(root)

        if remove_global_includes(root):
            messagebox.showinfo("Info", "The Inclusion of an URL containing 'SAPUILandscapeGlobal.xml' has been "
                                        "removed.")
        else:
            messagebox.showinfo("Info", "The XML file does not include 'SAPUILandscapeGlobal.xml'. No changes "
                                        "were made.")

        output_path = os.path.dirname(xml_file_path)
        output_name = os.path.basename(xml_file_path).split('.')[0] + "_modified"
        output_file = os.path.join(output_path, output_name + '.xml')

        for elem in root.iter('address'):
            elem.text = output_file

        tree.write(output_file)

        # Process the XML file and generate Excel files
        general_excel_file, duplicates_excel_file = generate_excel_files(output_file)

        messagebox.showinfo("Info", "The XML file has been successfully exported to: \n" + output_file
                            + "\n\n" + "General Excel file generated: \n" + general_excel_file
                            + "\n\n" + "Duplicates Excel file generated: \n" + duplicates_excel_file)

        open_folder_containing_file(output_file)

    except Exception as e:
        messagebox.showerror("Error!", f"An error occurred while processing the XML file: {str(e)}")
        logging.error(f"An error occurred while processing the XML file: {str(e)}")


# Function to add a new custom application server type of system to xml file
# Your find_custom_system() function is updated to return None when no service is found
def find_custom_system(xml_file_path, applicationServer, instanceNumber,
                       systemID):
    try:
        server_address = applicationServer + ":32" + instanceNumber
        sap_system = None
        # Parse the source XML file
        tree = ET.parse(xml_file_path)
        root = tree.getroot()

        for service in root.findall(".//Service"):
            if service.get('server') == server_address and service.get('systemid') == systemID:
                sap_system = service
                break
        return sap_system
    except Exception as e:
        messagebox.showwarning("Error in find_custom_system():", str(e))
        return None


def find_router(xml_file_path, routerid):
    # Parse the source XML file
    tree = ET.parse(xml_file_path)
    root = tree.getroot()
    for router in root.findall(".//Router"):
        if router.get('uuid') == routerid:
            return router


def find_message_server(xml_file_path, msid):
    # Parse the source XML file
    tree = ET.parse(xml_file_path)
    root = tree.getroot()
    for ms in root.findall(".//MessageServer"):
        if ms.get('uuid') == msid:
            return ms


def list_all_workspaces(xml_file_path):
    try:
        # Parse the destination XML file
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        workspaces = root.findall(".//Workspace")

        return workspaces

    except Exception as e:
        messagebox.showwarning("Error in list_all_workspaces():", str(e))
        logging.error(f"Error in list_all_workspaces(): {str(e)}")
        return None


def list_nodes_of_workspace(xml_file_path, workspace_name):
    try:
        # Parse the destination XML file
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        workspaces = root.findall(".//Workspace")
        node_names = []
        for ws in workspaces:
            if ws.get('name') == workspace_name:
                for node in ws.findall(".//Node"):
                    node_names.append(node.get('name'))
        return node_names
    except Exception as e:
        messagebox.showwarning("Error in list_nodes_of_workspace():", str(e))
        logging.error(f"Error in list_nodes_of_workspace(): {str(e)}")
        return []  # Return an empty list instead of None


def add_custom_system(sap_system, root_xml_path, destination_xml_path, workspace_name, node_name):
    try:
        status = False
        # Parse the destination XML file
        tree = ET.parse(destination_xml_path)
        root = tree.getroot()
        # Parse the root XML file
        source_tree = ET.parse(root_xml_path)
        source_root = source_tree.getroot()
        # Add service to the destination XML file
        if len(root.find(".//Services")) == 0:
            # Should throw exception if no services found
            raise Exception("No services element found in the destination XML file."
                            "Please make sure that the destination XML file is a "
                            "valid SAPUILandscape.xml file.")
        else:
            sap_system.set('uuid', str(uuid.uuid4()))
            root.find(".//Services").append(sap_system)
        # Check if there is Routers mentioned the SAP system, and they are also in the destination file
        if sap_system.get('routerid') is not None:
            for router in source_root.findall(".//Router"):
                if router.get('uuid') == sap_system.get('routerid'):
                    # Check if the router is already in the destination file
                    if find_router(destination_xml_path, router.get('uuid')) is None:
                        root.find(".//Routers").append(router)
                        break
                    break
        # Check for Message Servers
        if sap_system.get('msid') is not None:
            for ms in source_root.findall(".//MessageServer"):
                if ms.get('uuid') == sap_system.get('msid'):
                    # Check if the message server is already in the destination file
                    if find_message_server(destination_xml_path, ms.get('uuid')) is None:
                        root.find(".//MessageServers").append(ms)
                        break
                    break
        # Creating an Item and adding it to the specified Workspace and Node in the destination XML file
        for workspace in root.findall(".//Workspace"):
            if workspace.get('name') == workspace_name:
                for node in workspace.findall(".//Node"):
                    if node.get('name') == node_name:
                        item = ET.SubElement(node, 'Item')
                        item.set('uuid', sap_system.get('uuid'))
                        item.set('serviceid', sap_system.get('uuid'))
        # Save the destination XML file
        tree.write(destination_xml_path)
        # Check if the sap system is successfully added to the destination XML file
        for item in root.findall(".//Item"):
            if item.get('serviceid') == sap_system.get('uuid'):
                for service in root.findall(".//Service"):
                    if service.get('uuid') == sap_system.get('uuid'):
                        status = True
                        messagebox.showinfo("Success", "The SAP system is successfully added to the destination XML "
                                                       "file.\n"
                                                       "Output file: " + destination_xml_path)
                        if messagebox.askyesno("Question", "Do you want to open the destination XML file?"):
                            open_folder_containing_file(destination_xml_path)
                            python = sys.executable
                            os.execl(python, python, *sys.argv)
                        return status
        return status

    except Exception as e:
        messagebox.showwarning("Error in add_custom_system():", str(e))
        logging.error(f"Error in add_custom_system(): {str(e)}")
        return False


def extract_from_nodes(xml_file_path):
    try:
        print("Processing XML file...")
        # Parse the XML file
        tree = ET.parse(xml_file_path)
        root = tree.getroot()

        # Get all Items
        all_items = root.findall('.//Item')

        # Create a new workspace element
        workspace = ET.SubElement(root.find('.//Workspaces'), 'Workspace')
        workspace.set('name', 'Extracted from Nodes')
        workspace.set('uuid', str(uuid.uuid4()))
        workspace.set('expanded', '0')

        # Move the Item elements to the workspace
        for item in all_items:
            workspace.append(item)

        # Remove other workspaces
        workspaces_to_delete = []
        for ws in root.findall('.//Workspace'):
            if ws.get('name') != 'Extracted from Nodes':
                workspaces_to_delete.append(ws.get('uuid'))

        temp_xml_file_path = r"C:\Users\PR106797\PycharmProjects\uuid_manipulator\cache\temp.xml"
        tree.write(temp_xml_file_path)

        # Modify the temporary XML file
        temp_root = remove_elements_from_xml(temp_xml_file_path, workspaces_to_delete, 'Workspace')

        # Prompt user for output file path and name
        output_file_path = input("Enter the output file path: ")
        output_file_name = input("Enter the output file name: ")

        # Save the modified XML to the specified location
        output_file_path_with_name = os.path.join(output_file_path, output_file_name + '.xml')
        temp_tree = ET.ElementTree(temp_root)
        temp_tree.write(output_file_path_with_name)
        print(f"XML file saved successfully at {output_file_path_with_name}")

    except Exception as e:
        print(f"An error occurred while processing the XML file: {str(e)}")


def remove_elements_from_xml(xml_file_path, elements_to_remove, element_name):
    # Parse the XML file
    tree = le.parse(xml_file_path)
    root = tree.getroot()

    # Remove elements
    for elem_id in elements_to_remove:
        elements_to_remove = root.xpath(f".//{element_name}[@uuid='{elem_id}']")
        for elem in elements_to_remove:
            parent = elem.getparent()
            parent.remove(elem)

    return root


def remove_a_system(xml_file_path, sap_system):
    try:
        item_to_remove = None
        status = False
        # Parse the XML file
        tree = ET.parse(xml_file_path)
        root = tree.getroot()

        # Remove the SAP system from the XML file
        for item in root.findall(".//Item"):
            if item.get('serviceid') == sap_system.get('uuid'):
                item_to_remove = item
                root.find(".//Services").remove(sap_system)
                status = True
                break

        # Save the XML file
        tree.write(xml_file_path)
        # Check if the SAP system is successfully removed from the XML file
        for item in root.findall(".//Item"):
            if item.get('serviceid') == sap_system.get('uuid'):
                status = False
                break
            else:
                status = True
                # Remove the Item as well
                root.find(".//Items").remove(item_to_remove)
                # Save the destination XML file
                tree.write(xml_file_path)
                # show success message
                messagebox.showinfo("Success", "The SAP system is successfully removed from the XML file.\n")
                if messagebox.askyesno("Question", "Do you want to open the XML file?"):
                    open_folder_containing_file(xml_file_path)
                    python = sys.executable
                    os.execl(python, python, *sys.argv)
        return status

    except Exception as e:
        messagebox.showwarning("Error in remove_a_system():", str(e))
        logging.error(f"Error in remove_a_system(): {str(e)}")
        return False


def get_stats(xml_file_path):
    # Parse the XML file
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    all_items = root.findall('.//Item')
    node_items = root.findall('.//Node/Item')
    child_node_items = root.findall('.//Node/Node/Item')
    workspaces = root.findall('.//Workspace')
    services = root.findall('.//Service')
    routers = root.findall('.//Router')
    messageservers = root.findall('.//Messageserver')

    stats = {
        "workspaces": len(workspaces),
        "items": len(all_items),
        "items in nodes": len(node_items),
        "items in child nodes": len(child_node_items),
        "services": len(services),
        "routers": len(routers),
        "message servers": len(messageservers)
    }

    return stats


# Function to remove duplications in the XML file
def remove_duplicates(xml_file_path):
    try:

        # Parse the XML file
        tree = le.parse(xml_file_path)
        root = tree.getroot()

        # Create a DataFrame from the XML data
        data = []  # List to store XML data

        for item in root.findall(".//Item"):
            item_id = item.get('uuid')
            service_id = item.get('serviceid')

            for service in root.findall(".//Service"):
                if service.get('uuid') == service_id:
                    service_name = service.get('name')
                    service_sid = service.get('systemid')

                    if service.get('type') == 'SAPGUI':
                        service_server = service.get('server')
                    else:
                        service_server = service.get('url')

                    data.append([
                        item_id,
                        service_id,
                        service_name,
                        service_sid,
                        service_server
                    ])

        df = pd.DataFrame(data, columns=['Item Id', 'Service Id', 'Service Name', 'Service SID', 'Service Server'])

        # Identify duplicate items based on service name, SID, and server
        duplicates = df[df.duplicated(subset=['Service SID', 'Service Server'], keep=False)].copy()

        # Get unique UUIDs of duplicate items and services to remove
        item_uuids = duplicates['Item Id'].unique().tolist()
        service_uuids = duplicates['Service Id'].unique().tolist()

        # Remove duplicate items and services
        for item_id in item_uuids:
            elements_to_remove = root.xpath(f".//Item[@uuid='{item_id}']")
            for elem in elements_to_remove:
                parent = elem.getparent()
                parent.remove(elem)

        for service_id in service_uuids:
            elements_to_remove = root.xpath(f".//Service[@uuid='{service_id}']")
            for elem in elements_to_remove:
                parent = elem.getparent()
                parent.remove(elem)

        output_path = os.path.dirname(xml_file_path)
        output_name = os.path.basename(xml_file_path).split('.')[0] + "_without_duplications"
        output_file = os.path.join(output_path, output_name + '.xml')
        tree.write(output_file)
        messagebox.showinfo("Success!", f"Duplications removed. Output file saved to: {output_file}")
        open_folder_containing_file(output_file)

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while removing duplications: {str(e)}")
        logging.error(f"An error occurred while removing duplications: {str(e)}")


def list_system_ids_for_group_server_connection_entry(xml_file_path):
    try:
        # Parse the XML file
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        system_ids = []

        for service in root.findall(".//Service"):
            if service.get('msid') is not None:
                system_ids.append(service.get('systemid'))

        return system_ids

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while listing system IDs: {str(e)}")
        logging.error(f"An error occurred while listing system IDs: {str(e)}")


def find_message_server_based_on_system_id(xml_file_path, systemid):
    try:
        # Parse the XML file
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        message_server_id = None
        message_server = None
        message_servers = root.findall(".//Messageserver")
        services = root.findall(".//Service")

        for service in services:
            if service.get('msid') is not None:
                if service.get('systemid') == systemid:
                    message_server_id = service.get('msid')
                    break
        for ms in message_servers:
            if ms.get('uuid') == message_server_id:
                message_server = ms
                break
        return message_server

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while finding message server: {str(e)}")
        logging.error(f"An error occurred while finding message server: {str(e)}")


def get_all_routers(xml_file_path):
    try:
        # Parse the XML file
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        routers = root.findall(".//Router")
        return routers

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while finding message server: {str(e)}")
        logging.error(f"An error occurred while finding message server: {str(e)}")


def get_all_urls(xml_file_path):
    try:
        # Parse the XML file
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        services = root.findall(".//Service")
        urls = []
        for service in services:
            # Assuming the service name is also an attribute of the Service node
            if service.get('url') is not None and service.get('name') is not None:
                urls.append({'name': service.get('name'), 'url': service.get('url')})

        # Return the list of URLs
        return urls

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while finding NWBC/FIORI system urls: {str(e)}")
        logging.error(f"An error occurred while finding NWBC/FIORI system urls: {str(e)}")


def get_all_custom_sap_gui_info(xml_file_path):
    # Parse the XML file
    tree = ET.parse(xml_file_path)
    root = tree.getroot()
    services = root.findall(".//Service")
    sap_gui_server_addresses = []
    sap_gui_system_ids = []
    sap_gui_instance_numbers = []
    for service in services:
        if service.get('type') == 'SAPGUI':
            if service.get('server') is not None:
                server = service.get('server')
                if ':32' in server:
                    address, port_with_extra_32 = server.split(':')
                    port = port_with_extra_32.split("32")[1]
                    sap_gui_server_addresses.append(address)
                    if port not in sap_gui_instance_numbers:
                        sap_gui_instance_numbers.append(port)
                    sap_gui_system_ids.append(service.get('systemid'))

    return sap_gui_server_addresses, sap_gui_instance_numbers, sap_gui_system_ids


def find_all_system_ids_based_on_server_address(xml_file_path, server_address, server_instance_number):
    try:
        # Parse the XML file
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        server = server_address + ":32" + server_instance_number
        system_ids = []

        for service in root.findall(".//Service"):
            if service.get('server') is not None:
                if service.get('server') == server:
                    system_ids.append(service.get('systemid'))


        return system_ids

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while listing system IDs: {str(e)}")
        logging.error(f"An error occurred while listing system IDs: {str(e)}")


def find_all_instance_numbers_based_on_server_address(xml_file_path, server_address):
    try:
        # Parse the XML file
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        instance_numbers = []

        for service in root.findall(".//Service"):
            if service.get('server') is not None:
                if server_address in service.get('server'):
                    server = service.get('server')
                    if ':32' in server:
                        address, port_with_extra_32 = server.split(':')
                        port = port_with_extra_32.split("32")[1]
                        if port not in instance_numbers:
                            instance_numbers.append(port)

        return instance_numbers

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while listing instance numbers: {str(e)}")
        logging.error(f"An error occurred while listing instance numbers: {str(e)}")


def find_group_server_connections(xml_file_path, system_id, message_server, router):
    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        possible_connections = []
        message_server_id = None
        router_id = None
        candidate_connection = None
        final_result = None

        for service in root.findall(".//Service"):
            if service.get('msid') is not None:
                if service.get('systemid') == system_id:
                    possible_connections.append({'serviceid': service.get('uuid'),
                                                 'msid': service.get('msid'),
                                                 'routerid': service.get('routerid')})
        for ms in root.findall(".//Messageserver"):
            if ms.get('host') == message_server:
                message_server_id = ms.get('uuid')
        for rt in root.findall(".//Router"):
            if rt.get('name') == router:
                router_id = rt.get('uuid')
        for gsc in possible_connections:
            if gsc.get('msid') == message_server_id and gsc.get('routerid') == router_id:
                candidate_connection = gsc

        if candidate_connection is not None:  # Add this check
            for service in root.findall(".//Service"):
                if service.get('uuid') == candidate_connection.get('serviceid'):
                    final_result = service

        return final_result, message_server, router

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while finding group/server connection: {str(e)}")
        logging.error(f"An error occurred while finding group/server connection: {str(e)}")

