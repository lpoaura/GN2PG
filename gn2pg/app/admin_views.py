"""Admin model views"""

from flask_admin.contrib.sqla import ModelView

from gn2pg.app.utils.admin_views import add_class_ctn_row_long_text_formatter, json_formatter


class ReadOnlyView(ModelView):
    """Generic read only admin model view"""

    can_create = False
    can_delete = False
    can_edit = False


class EditOnlyView(ReadOnlyView):
    """Generic edit only admin model view"""

    can_edit = True


class ImportView(ReadOnlyView):
    """Download log view"""

    column_list = (
        "id",
        "source",
        "controler",
        "xfer_type",
        "xfer_status",
        "xfer_start_ts",
        "xfer_end_ts",
        "api_count_items",
        "api_count_errors",
        "data_count_upserts",
        "data_count_delete",
        "data_count_errors",
        "metadata_count_upserts",
        "metadata_count_errors",
        "xfer_http_status",
        "xfer_filters",
        "comment",
    )
    column_default_sort = ("id", True)
    column_filters = ("source", "xfer_type")
    column_formatters = {
        "xfer_filters": add_class_ctn_row_long_text_formatter,
        "comment": add_class_ctn_row_long_text_formatter,
    }
    can_delete = True


class ErrorView(ReadOnlyView):
    """Error log view"""

    column_list = ("source", "uuid", "controler", "last_ts", "item", "error", "import_id")
    column_formatters = {"item": json_formatter, "error": add_class_ctn_row_long_text_formatter}
    column_filters = ["source", "uuid", "controler", "import_id"]
