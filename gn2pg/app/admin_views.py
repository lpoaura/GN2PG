from flask_admin.contrib.sqla import ModelView


class ReadOnlyView(ModelView):
    can_create = False
    can_delete = False
    can_edit = False


class DownloadView(ReadOnlyView):
    column_list = ("source", "controler", "download_ts", "error_count", "http_status")
    # form_columns = ['source', 'controler', 'download_ts', 'error_count', 'http_status']
