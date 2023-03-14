from flask_admin.contrib.sqla import ModelView


class ReadOnlyView(ModelView):
    can_create = False
    can_delete = False
    can_edit = False


class DownloadView(ReadOnlyView):
    column_list = ("source", "controler", "download_ts", "error_count", "http_status")

class IncrementView(ReadOnlyView):
    column_list = ("source", "controler", "last_ts")

class ErrorView(ReadOnlyView):
    column_list = ("source","id_data", "controler", "last_ts", "item", "error")
