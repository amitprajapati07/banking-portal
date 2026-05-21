from rest_framework.pagination import CursorPagination, PageNumberPagination

class TransactionCursorPagination(CursorPagination):
    """
    Cursor-based pagination for high-performance timeline traversal.
    Prevents duplicate items when new transactions are added.
    """
    page_size = 20
    ordering = "-timestamp"
    cursor_query_param = "cursor"

class AccountPagePagination(PageNumberPagination):
    """
    Standard offset pagination for account listing.
    """
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50
