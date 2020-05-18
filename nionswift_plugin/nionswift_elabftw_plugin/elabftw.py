import typing
import gettext
import asyncio
import os
import multiprocessing
import sys
from datetime import datetime
import io
import json


from nion.utils import Event, Registry
from nion.ui import Declarative
from nion.swift.model import PlugInManager
from nion.swift import Workspace, DocumentController, Panel, Facade
from nion.typeshed import API_1_0

import elabapy

from nionswift_plugin.nionswift_elabftw_plugin.Users import Users
from nionswift_plugin.nionswift_elabftw_plugin.MergeDataConfirmDialog import MergeDataConfirmDialogUI

_ = gettext.gettext

class ElabFTWUIHandler:
    def __init__(self, api: API_1_0.API, event_loop: asyncio.AbstractEventLoop, ui_view: dict):
        self.ui_view = ui_view
        self.__api = api
        self.__event_loop = event_loop
        self.property_changed_event = Event.Event()
        self.undo_metadata = None
        self.last_modified_dataitem = None

    def init_handler(self):
        # Needed for method "spawn" (on Windows) to prevent mutliple Swift instances from being started
        if multiprocessing.get_start_method() == 'spawn':
            multiprocessing.set_executable(os.path.join(sys.exec_prefix, 'pythonw.exe'))
        self.users = Users()
        self.combo.items = self.users.get_users_list()
        self.users.username = self.combo.items[0]
        self.elab_manager = None

        #Check if directory exists or not. Create if it doesn't exist.
        from pathlib import Path
        Path(os.path.expanduser(self.users.settings_dir)).mkdir(parents=True, exist_ok=True)

    def close(self):
        ...

    def setup_config(self):
        # Returns true if config already exists
        # Returns false to allow caller to interrupt action
        # Get IP of Elab Server
        self.config = {}
        with open(os.path.expanduser(self.users.settings_dir)+'/config.txt', 'a+') as f:
            f.seek(0)
            for prop in f:
                prop = prop.rstrip('\n').split('=')
                self.config[prop[0]] = prop[1]
                print(self.config)

            if len(self.config) < 1: #If no config is found
                # Ask for and save IP address
                def save_ip(ip):
                    with open(os.path.expanduser(self.users.settings_dir)+'/config.txt', 'a+') as f:
                        f.write('elabftw_ip_address='+ip+'\n')
                self.__api.application.document_windows[0].show_get_string_message_box('ElabFTW Server Address', 'Enter elabftw URL', save_ip, accepted_text='Save')
                return False
            return True
    def get_experiments_and_set(self):
        self.experiments = self.elab_manager.get_all_experiments()
        self.experiments.append({'id':'-1', 'title':'<Create Experiment>'})

        self.ui_stack.current_index = 1
        self.experiments_combo.items = [x['title'] for x in self.experiments]
        self.current_experiment_id = self.experiments[self.combo.current_index]['id']
        self.get_uploads_for_current_experiment()

    def switch_to_experiments_list(self):
        self.elab_manager = elabapy.Manager(endpoint=self.config['elabftw_ip_address']+"/api/v1/", token=self.users.api_key)
        self.get_experiments_and_set()

    def logout_user_button_clicked(self, widget: Declarative.UIWidget):
        self.users.logout()
        self.combo.items = self.users.get_users_list()
        self.users.username = self.combo.items[0]
        self.ui_stack.current_index = 0

    def create_user_button_clicked(self, widget: Declarative.UIWidget):

        def reject_colon(text):
            if ':' in text:
                raise Exception('There should be no colon ":" in the entry.')

        def accepted_api_dialog(api):
            reject_colon(api)
            self.users.api_key = api
            self.users.create_user()
            self.switch_to_experiments_list()

        def accepted_pass_dialog(password):
            reject_colon(password)
            if self.users.password == password:
                self.__api.application.document_windows[0].show_get_string_message_box('Create User', 'Enter API key', accepted_api_dialog, accepted_text='Create')
            else:
                self.users.password = password
                self.__api.application.document_windows[0].show_get_string_message_box('Create User', 'Repeat password', accepted_pass_dialog, accepted_text='Create')

        def accepted_user_dialog(name):
            reject_colon(name)
            self.users.username = name
            self.__api.application.document_windows[0].show_get_string_message_box('Create User', 'Choose a password', accepted_pass_dialog, accepted_text='Create')

        if self.setup_config():
            self.__api.application.document_windows[0].show_get_string_message_box('Create User', 'Choose a username', accepted_user_dialog, accepted_text='Create')

    def login_user_button_clicked(self, widget: Declarative.UIWidget):

        def on_password_input(password):
            if self.users.login(self.users.username, password):
                self.switch_to_experiments_list()
            else:
                self.__api.application.document_windows[0].show_get_string_message_box('Login', 'Wrong password. Please try again.', on_password_input, accepted_text='Login')

        if self.setup_config():
            self.__api.application.document_windows[0].show_get_string_message_box('Login', 'Enter password', on_password_input, accepted_text='Login')

    def upload_meta_data(self):
        for dataitem in self.__api.application.document_controllers[0]._document_controller.selected_data_items:
            f = io.StringIO(json.dumps(dataitem.metadata, indent=3))
            f.name = dataitem.title+'.json'
            files = {'file': f}
            self.elab_manager.upload_to_experiment(self.current_experiment_id, files) # done uploading

        # Reset current index matching with UI
        self.experiments = self.elab_manager.get_all_experiments()
        self.experiments.append({'id':'-1', 'title':'<Create Experiment>'})
        self.combo.items = [x['title'] for x in self.experiments]
        self.get_uploads_for_current_experiment()

    def on_combo_changed(self, widget: Declarative.UIWidget, current_index: int):
        self.users.username = self.combo.items[current_index]

    def on_uploads_combo_changed(self, widget: Declarative.UIWidget, current_index: int):
        self.current_upload_id = self.uploads[current_index]['id']

    def on_experiments_combo_changed(self, widget: Declarative.UIWidget, current_index: int):
        self.current_experiment_id = self.experiments[current_index]['id']

        if self.current_experiment_id == '-1':
            return
        # sync the uploads with the chosen experiments
        self.get_uploads_for_current_experiment()

    def get_uploads_for_current_experiment(self):
        exp = self.elab_manager.get_experiment(self.current_experiment_id)
        if exp['has_attachment'] == '1':
            self.uploads = [{'real_name':x['real_name'],'id':x['id']} for x in exp['uploads']]
            self.uploads_combo.items = [x['real_name'] for x in self.uploads]
            self.current_upload_id = self.uploads[self.uploads_combo.current_index]['id']
        else:
            self.uploads = []
            self.uploads_combo.items = ['No attachments found!']
            self.current_upload_id = '-1'

    def submit_data_button_clicked(self, widget: Declarative.UIWidget):
        #check if one or more dataitem is selected. Otherwise give an error.
        if len(self.__api.application.document_controllers[0]._document_controller.selected_data_items)<1:
            self.__api.application.document_windows[0].show_get_string_message_box('Error in Dataitem selection', 'Please choose data items to submit to.', lambda x: x)
            return
        if self.current_experiment_id == str(-1):
            def accepted_exp_dialog(experiment_name):
                exp = self.elab_manager.create_experiment()
                params = {'title':experiment_name, 'body':'', 'date':datetime.today().strftime('%Y%m%d')}
                self.elab_manager.post_experiment(exp['id'], params)
                self.current_experiment_id = exp['id'] # set the new experiments' id to upload to
                self.upload_meta_data()
                self.get_experiments_and_set()

            self.__api.application.document_windows[0].show_get_string_message_box('Create Experiment', 'Choose a name for the experiment', accepted_exp_dialog, accepted_text='Create')
        else:
            self.upload_meta_data()

    def fetch_data_button_clicked(self, widget: Declarative.UIWidget):
        document_controller = self.__api.application.document_controllers[0]._document_controller

        #check if one dataitem is selected. Otherwise give an error.
        if len(document_controller.selected_data_items)!=1:
            self.__api.application.document_windows[0].show_get_string_message_box('Error in Dataitem selection', 'Please choose a single data item to fetch to.', lambda x: x)
            return

        selected_dataitem = document_controller.selected_data_items[0]
        self.last_modified_dataitem = selected_dataitem
        self.undo_metadata = selected_dataitem.metadata # save metadata to undo
        metadata_elab = self.elab_manager.get_upload(self.current_upload_id)
        metadata_elab = json.loads(metadata_elab.decode('utf-8'))
        ui_handler = MergeDataConfirmDialogUI().get_ui_handler(api_broker=PlugInManager.APIBroker(), document_controller=document_controller,event_loop=document_controller.event_loop, metadata_elab=metadata_elab, metadata_nion=selected_dataitem.metadata, dataitem=selected_dataitem, title='Merge metedata')
        finishes = list()
        dialog = Declarative.construct(document_controller.ui, document_controller, ui_handler.ui_view, ui_handler, finishes)
        for finish in finishes:
           finish()
        ui_handler._event_loop = document_controller.event_loop

        ui_handler.request_close = dialog.request_close
        dialog.show()

    def undo_change_button_clicked(self, widget: Declarative.UIWidget):
        if self.undo_metadata != None:
            self.last_modified_dataitem.metadata = self.undo_metadata


class ElabFTWUI:
    def __init__(self):
        self.panel_type = 'elabftw-panel'

    def get_ui_handler(self, api_broker: PlugInManager.APIBroker=None, event_loop: asyncio.AbstractEventLoop=None, **kwargs):
        api = api_broker.get_api('~1.0')
        ui = api_broker.get_ui('~1.0')
        ui_view = self.__create_ui_view(ui)
        return ElabFTWUIHandler(api, event_loop, ui_view)

    def __create_ui_view(self, ui: Declarative.DeclarativeUI) -> dict:
        # login UI
        create_user_button = ui.create_push_button(name='left_button', text='Create', on_clicked='create_user_button_clicked')
        login_user_button = ui.create_push_button(name='right_button', text='Login', on_clicked='login_user_button_clicked')
        buttons_row = ui.create_row(create_user_button, login_user_button, spacing=8, margin=4)
        users_combo = ui.create_combo_box(name='combo', on_current_index_changed='on_combo_changed')
        users_field = ui.create_label(name='combo_label', text='Choose user:')
        users_row = ui.create_row(users_field, users_combo)
        login_column = ui.create_column(users_row, buttons_row, ui.create_stretch(), spacing=8, margin=4)

        # manage metadata UI
        logout_user_button = ui.create_push_button(name='logout_button', text='Logout', on_clicked='logout_user_button_clicked')
        submit_data_button = ui.create_push_button(name='submit_button', text='Submit', on_clicked='submit_data_button_clicked')
        undo_change_button = ui.create_push_button(name='undo_change_button', text='Undo', on_clicked='undo_change_button_clicked')
        fetch_data_button = ui.create_push_button(name='fetch_button', text='Fetch', on_clicked='fetch_data_button_clicked')
        experiments_combo = ui.create_combo_box(name='experiments_combo', on_current_index_changed='on_experiments_combo_changed')
        experiments_field = ui.create_label(text='Choose experiment:')
        experiments_row = ui.create_row(experiments_field, experiments_combo)

        uploads_field = ui.create_label(text='Files:')
        uploads_combo = ui.create_combo_box(name='uploads_combo', on_current_index_changed='on_uploads_combo_changed')
        uploads_row = ui.create_row(uploads_field, uploads_combo, spacing=8, margin=4)
        data_buttons_row_1 = ui.create_row(undo_change_button, fetch_data_button, spacing=8, margin=4)
        data_buttons_row_2 = ui.create_row(logout_user_button, submit_data_button, spacing=8, margin=4)
        data_buttons_column = ui.create_column(data_buttons_row_1, data_buttons_row_2)
        data_column  = ui.create_column(experiments_row, uploads_row, data_buttons_column, ui.create_stretch(), spacing=8, margin=4)

        content = ui.create_stack(login_column, data_column, name="ui_stack")
        return content

class ElabFTWPanel(Panel.Panel):
    def __init__(self, document_controller: DocumentController.DocumentController, panel_id: str, properties: dict):
        super().__init__(document_controller, panel_id, 'elabftw-panel')
        panel_type = properties.get('panel_type')
        for component in Registry.get_components_by_type('elabftw-panel'):
            if component.panel_type == panel_type:
                ui_handler = component.get_ui_handler(api_broker=PlugInManager.APIBroker(), event_loop=document_controller.event_loop)
                self.widget = Declarative.DeclarativeWidget(document_controller.ui, document_controller.event_loop, ui_handler)


def run():
    Registry.register_component(ElabFTWUI(), {'elabftw-panel'})
    panel_properties = {'panel_type': 'elabftw-panel'}
    Workspace.WorkspaceManager().register_panel(ElabFTWPanel, 'elabftw-control-panel', _('ElabFTW'), ['left', 'right'], 'left', panel_properties)
