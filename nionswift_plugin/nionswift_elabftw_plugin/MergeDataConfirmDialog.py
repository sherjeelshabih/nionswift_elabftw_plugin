import typing
import asyncio
import json

from nion.swift.model import PlugInManager
from nion.ui import Declarative
from nion.utils import Event, Converter
from nion.typeshed import API_1_0

from nionswift_plugin.nionswift_elabftw_plugin.ConflictCheckDialog import ConflictCheckDialogUI

class MergeDataConfirmDialogUIHandler:
    def __init__(self, api: API_1_0.API, ui_view: dict, document_controller=None, metadata_elab: dict=None, metadata_nion: dict=None, dataitem = None):
        self.__api = api
        self.ui_view = ui_view
        self.on_closed = None
        self.on_merge = None
        self.on_overwrite = None
        self.elabftw_data_dict = metadata_elab
        self.nion_data_dict = metadata_nion
        self.elabftw_data = json.dumps(metadata_elab, indent=3)
        self.nion_data = json.dumps(metadata_nion, indent=3)
        self.dataitem = dataitem
        self.document_controller = document_controller

    def init_handler(self):
        pass

    def on_load(self, widget: Declarative.UIWidget):
        if hasattr(self, 'request_close') and callable(self.request_close):
            self.request_close()

    def close(self):
        if callable(self.on_closed):
            self.on_closed()

    def on_overwrite_clicked(self, widget: Declarative.UIWidget):
        if callable(self.on_overwrite):
            self.on_overwrite()
        else:
            self.dataitem.metadata = self.elabftw_data_dict
            self.request_close()

    def on_merge_clicked(self, widget: Declarative.UIWidget):
        if callable(self.on_merge):
            self.on_merge()
        else:
            conflict_keys = conflict_check_dicts(self.nion_data_dict, self.elabftw_data_dict)
            if len(conflict_keys)>0:
                self.show_conflict_check_dialog(self.document_controller, self.elabftw_data_dict, self.nion_data_dict, self.dataitem, conflict_keys)
            else:
                d = self.dataitem.metadata
                d.update(self.elabftw_data_dict)
                self.dataitem.metadata = d
                self.request_close()

    def show_conflict_check_dialog(self, document_controller, metadata_elab, metadata_nion, dataitem, conflict_keys):
        ui_handler = ConflictCheckDialogUI().get_ui_handler(api_broker=PlugInManager.APIBroker(),event_loop=document_controller.event_loop, metadata_elab=metadata_elab, metadata_nion=metadata_nion, dataitem=dataitem, conflict_keys=conflict_keys, title='Resolve conflicts')
        finishes = list()
        dialog = Declarative.construct(document_controller.ui, document_controller, ui_handler.ui_view, ui_handler, finishes)
        for finish in finishes:
           finish()
        ui_handler._event_loop = document_controller.event_loop

        ui_handler.request_close = dialog.request_close
        ui_handler.parent_request_close = self.request_close
        dialog.show()

# Get all conflicts between two merge_dicts
def conflict_check_dicts(d1, d2, path=None):
    if path is None: path = []
    try:
        # Python 2
        intersection = d1.viewkeys() & d2
    except AttributeError:
        # Python 3
        intersection = d1.keys() & d2

    conflict_keys = []
    for shared in intersection:
        if isinstance(d1[shared], dict) and isinstance(d2[shared], dict):
            conflicted_deep = conflict_check_dicts(d1[shared], d2[shared], path+[str(shared)])
            if len(conflicted_deep)>0:
                conflict_keys = conflict_keys + conflicted_deep
        elif d1[shared] != d2[shared]:
            conflict_keys.insert(0, shared) if len(path)==0 else conflict_keys.insert(0, '/'.join(path)+'/'+shared)
    return conflict_keys

class MergeDataConfirmDialogUI:
    def get_ui_handler(self, api_broker: PlugInManager.APIBroker=None, document_controller=None, event_loop: asyncio.AbstractEventLoop=None, metadata_elab: dict=None, metadata_nion: dict=None, dataitem = None, **kwargs):
        api = api_broker.get_api('~1.0')
        ui = api_broker.get_ui('~1.0')

        ui_view = self.__create_ui_view(ui, title=kwargs.get('title'))
        return MergeDataConfirmDialogUIHandler(api, ui_view, document_controller, metadata_elab, metadata_nion, dataitem)

    def __create_ui_view(self, ui: Declarative.DeclarativeUI, title: str=None, **kwargs) -> dict:
        elabftw_text_field = ui.create_text_edit(editable=False, text='elabftw_data', width=400, height=500)
        elabftw_tab = ui.create_tab(label='Elabftw', content=elabftw_text_field)

        nion_text_field = ui.create_text_edit(editable=False, text='nion_data', width=400, height=500)
        nion_tab = ui.create_tab(label='Nion Swift', content=nion_text_field)
        tabs = ui.create_tabs(elabftw_tab, nion_tab)

        overwrite_button = ui.create_push_button(text='Overwrite', on_clicked='on_overwrite_clicked')
        merge_button = ui.create_push_button(text='Merge', on_clicked='on_merge_clicked')
        buttons_row = ui.create_row(overwrite_button, merge_button, spacing=8, margin=4)
        content = ui.create_column(tabs, buttons_row, ui.create_stretch(), spacing=8, margin=4)
        return ui.create_modeless_dialog(content, title=title, margin=4)
