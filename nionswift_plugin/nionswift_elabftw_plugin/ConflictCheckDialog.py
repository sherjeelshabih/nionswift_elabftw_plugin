import typing
import asyncio

from nion.swift.model import PlugInManager
from nion.ui import Declarative
from nion.utils import Event, Converter
from nion.typeshed import API_1_0


class ConflictCheckDialogUIHandler:
    def __init__(self, api: API_1_0.API, ui_view: dict, metadata_elab: dict=None, metadata_nion: dict=None, dataitem = None, conflict_keys: dict=None):
        self.__api = api
        self.ui_view = ui_view
        self.on_closed = None
        self.nion_data_dict = metadata_nion
        self.elabftw_data_dict = metadata_elab
        self.dataitem = dataitem
        self.conflict_keys = conflict_keys
        self.nion_text = conflict_keys[0] + ' : ' + str(get_value_from_dict_path(self.nion_data_dict, conflict_keys[0]))
        self.elabftw_text = conflict_keys[0] + ' : ' + str(get_value_from_dict_path(self.elabftw_data_dict, conflict_keys[0]))
        self.done = False
        self.conflict_index = 0
        self.parent_request_close = None

    def init_handler(self):
        pass

    def close(self):
        if callable(self.on_closed):
            self.on_closed()

    def next(self):
        if self.conflict_index < len(self.conflict_keys)-1:
            self.conflict_index = self.conflict_index + 1
            self.nion_text_field.text = self.conflict_keys[self.conflict_index] + ' : ' + str(get_value_from_dict_path(self.nion_data_dict, self.conflict_keys[self.conflict_index]))
            self.elabftw_text_field.text = self.conflict_keys[self.conflict_index] + ' : ' + str(get_value_from_dict_path(self.elabftw_data_dict, self.conflict_keys[self.conflict_index]))
        else:
            d = self.dataitem.metadata
            d.update(self.elabftw_data_dict)
            self.dataitem.metadata = d
            self.request_close()
            self.parent_request_close()

    def on_nion_button_clicked(self, widget: Declarative.UIWidget):
        set_value_from_dict_path(self.elabftw_data_dict, self.conflict_keys[self.conflict_index], get_value_from_dict_path(self.nion_data_dict, self.conflict_keys[self.conflict_index]))
        self.next()

    def on_elabftw_button_clicked(self, widget: Declarative.UIWidget):
        set_value_from_dict_path(self.elabftw_data_dict, self.conflict_keys[self.conflict_index], get_value_from_dict_path(self.elabftw_data_dict, self.conflict_keys[self.conflict_index]))
        self.next()

def get_value_from_dict_path(d, path): # change this so that the dictionary is taken along and updated then returned. Right now this returns None
    if isinstance(path, str):
        path = path.split('/')
        return get_value_from_dict_path(d, path)
    elif isinstance(path, list):
        pos = path.pop(0)
        if isinstance(d[pos], dict):
            return get_value_from_dict_path(d[pos], path)
        else:
            return d[pos]

def set_value_from_dict_path(d, path, value):
    if isinstance(path, str):
        path = path.split('/')
        return set_value_from_dict_path(d, path, value)
    elif isinstance(path, list):
        pos = path.pop(0)
        if isinstance(d[pos], dict):
            d[pos] = set_value_from_dict_path(d[pos], path, value)
            return d
        else:
            d[pos] = value
            return d

class ConflictCheckDialogUI:
    def get_ui_handler(self, api_broker: PlugInManager.APIBroker=None, event_loop: asyncio.AbstractEventLoop=None, metadata_elab: dict=None, metadata_nion: dict=None, dataitem = None, conflict_keys: dict=None, **kwargs):
        api = api_broker.get_api('~1.0')
        ui = api_broker.get_ui('~1.0')

        ui_view = self.__create_ui_view(ui, title=kwargs.get('title'))
        return ConflictCheckDialogUIHandler(api, ui_view, metadata_elab, metadata_nion, dataitem, conflict_keys)

    def __create_ui_view(self, ui: Declarative.DeclarativeUI, title: str=None, **kwargs) -> dict:
        nion_text_field = ui.create_text_edit(editable=False, text='nion_text',name='nion_text_field', width=200, height=100)
        elabftw_text_field = ui.create_text_edit(editable=False, text='elabftw_text', name='elabftw_text_field', width=200, height=100)
        text_row = ui.create_row(nion_text_field, elabftw_text_field,spacing=8, margin=4)

        nion_button = ui.create_push_button(text='Keep Local', on_clicked='on_nion_button_clicked')
        elabftw_button = ui.create_push_button(text='Keep Elabftw', on_clicked='on_elabftw_button_clicked')
        button_row = ui.create_row(nion_button, elabftw_button,spacing=8, margin=4)

        content = ui.create_column(text_row, button_row, ui.create_stretch(), spacing=8, margin=4)

        return ui.create_modeless_dialog(content, title=title, margin=4)
