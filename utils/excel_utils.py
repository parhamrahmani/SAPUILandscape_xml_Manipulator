import xml.etree.ElementTree as ET
import pandas as pd


def generate_excel_files(xml_file_path):
    def generate_excel_file(file_path):
        # Parse the XML file
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Create a dictionary to store the data
        data_sheet_1 = {
            'Workspace': [],
            'Parent Node': [],
            'Child Node': [],
            'System Name': [],
            'System Description': [],
            'System Id': [],
            'System Type': [],
            'System Client': [],
            'System URL': [],
            'System Server': [],
            'Router Address': [],
            'Message Server Name': [],
            'Message Server Host': [],
            'Is Duplicate': [],
            'Item UUID': [],
            'Service UUID': []
        }

        def add_service_data(workspace_name, parent_node_name, child_node_name, item):
            service_id = item.get('serviceid')

            for service in services:
                service_uuid = service.get('uuid')

                if service_uuid == service_id:
                    service_type = service.get('type')
                    service_name = service.get('name')
                    service_description = service.get('description')
                    service_sid = service.get('systemid')
                    service_client = service.get('client')
                    service_url = service.get('url')
                    service_server = service.get('server')

                    router_address = ''
                    for router in routers:
                        router_uuid = router.get('uuid')
                        service_router = service.get('routerid')

                        if service_router == router_uuid:
                            router_address = router.get('router')
                            break

                    messageserver_address = ''
                    messageserver_name = ''
                    for messageserver in messageservers:
                        messageserver_uuid = messageserver.get('uuid')
                        service_messageserver = service.get('msid')

                        if service_messageserver == messageserver_uuid:
                            messageserver_address = messageserver.get('host')
                            messageserver_name = messageserver.get('name')
                            break

                    data_sheet_1['Workspace'].append(workspace_name)
                    data_sheet_1['Parent Node'].append(parent_node_name)
                    data_sheet_1['Child Node'].append(child_node_name)
                    data_sheet_1['System Name'].append(service_name)
                    data_sheet_1['System Description'].append(service_description)
                    data_sheet_1['System Id'].append(service_sid)
                    data_sheet_1['System Type'].append(service_type)
                    data_sheet_1['System Client'].append(service_client)
                    data_sheet_1['System URL'].append(service_url)
                    data_sheet_1['System Server'].append(service_server)
                    data_sheet_1['Router Address'].append(router_address)
                    data_sheet_1['Message Server Name'].append(messageserver_name)
                    data_sheet_1['Message Server Host'].append(messageserver_address)
                    data_sheet_1['Is Duplicate'].append('')
                    data_sheet_1['Item UUID'].append(item.get('uuid'))
                    data_sheet_1['Service UUID'].append(service_uuid)

        if root is not None:
            all_items = root.findall('.//Item')
            node_items = root.findall('.//Node/Item')
            child_node_items = root.findall('.//Node/Node/Item')
            workspaces = root.findall('.//Workspace')
            services = root.findall('.//Service')
            routers = root.findall('.//Router')
            messageservers = root.findall('.//MessageServer')

            for workspace in workspaces:
                workspace_name = workspace.get('name')

                for node in workspace.findall('.//Node'):
                    parent_node_name = node.get('name')

                    for item_node in node.findall('.//Item'):
                        if item_node not in child_node_items:
                            add_service_data(workspace_name, parent_node_name, '', item_node)

                    for child_node in node.findall('.//Node'):
                        child_node_name = child_node.get('name')

                        for child_item_node in child_node.findall('.//Item'):
                            add_service_data(workspace_name, parent_node_name, child_node_name, child_item_node)

                for item in all_items:
                    if item not in node_items and item not in child_node_items:
                        add_service_data(workspace_name, '', '', item)

        # Create a DataFrame from the data dictionary
        df = pd.DataFrame(data_sheet_1)

        # Mark duplicates in the 'System Server' column if system type is 'SAPGUI'
        df.loc[df['System Type'] == 'SAPGUI', 'Is Duplicate'] = df.duplicated(
            subset=['System Server', 'System Id', 'System Name'], keep=False)

        # Mark duplicates in the 'System URL' column if system type is not 'SAPGUI'
        df.loc[df['System Type'] != 'SAPGUI', 'Is Duplicate'] = df.duplicated(
            subset=['System URL', 'System Id', 'System Name'], keep=False)

        # Save the DataFrame to Excel
        output_file_path = file_path.replace('.xml', '.xlsx')
        df.to_excel(output_file_path, index=False)

        return output_file_path

    # Call the original generate_excel_file function to generate the general Excel file
    general_file_path = generate_excel_file(xml_file_path)

    # Read the general Excel file into a DataFrame
    df = pd.read_excel(general_file_path)

    # Filter the DataFrame to keep only duplicate rows
    duplicates_df = df[df['Is Duplicate']]

    # Generate the duplicate file path
    duplicate_file_path = general_file_path.replace('.xlsx', '_duplicates.xlsx')

    # Save the duplicate DataFrame to a new Excel file
    duplicates_df.to_excel(duplicate_file_path, index=False)

    return general_file_path, duplicate_file_path

