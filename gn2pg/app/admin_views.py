from flask_admin.contrib.sqla import ModelView

from gn2pg.app.utils.admin_views import add_class_ctn_row_long_text_formatter, json_formatter


class ReadOnlyView(ModelView):
    can_create = False
    can_delete = False
    can_edit = False

class EditOnlyView(ReadOnlyView):
    can_edit = True

class DownloadView(ReadOnlyView):
    column_list = ("source", "controler", "download_ts", "error_count", "http_status")


class IncrementView(EditOnlyView):
    column_list = ("source", "controler", "last_ts")
    edit_modal = True
    form_excluded_columns = ['source', 'controler']


class ErrorView(ReadOnlyView):
    column_list = ("source", "id_data", "controler", "last_ts", "item", "error")
    column_formatters = dict(item=json_formatter, error=add_class_ctn_row_long_text_formatter)
    column_filters = ['source','id_data']

