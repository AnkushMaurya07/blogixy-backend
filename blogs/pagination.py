from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class BlogPageNumberPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50

    def get_paginated_response(self, data):
        page_size = self.get_page_size(self.request) or self.page_size
        return Response(
            {
                'results': data,
                'count': self.page.paginator.count,
                'page': self.page.number,
                'page_size': page_size,
                'has_next': self.page.has_next(),
            }
        )
