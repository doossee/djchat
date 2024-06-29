from django.db.models import Count

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, AuthenticationFailed

from .models import Server
from .serializers import ServerSerializer
from .schema import server_list_docs
from .pagination import ServerListPagination


class ServerListViewSet(viewsets.ViewSet):
    """
    A viewset for listing servers with various filtering options.

    Raises:
        AuthenticationFailed: If the request requires authentication but the user is not authenticated.
        ValidationError: If the server ID provided is not found.
        ValidationError: If the server ID provided is not an integer.
        ValidationError: If the quantity provided is not an integer.

    Returns:
        Response: A DRF response containing the serialized server data.
    """

    queryset = Server.objects.all()
    serializer_class = ServerSerializer
    pagination_class = ServerListPagination

    @server_list_docs
    def list(self, request):
        """
        Lists servers based on query parameters.

        Query Parameters:
            - category (str): Filter servers by category name.
            - qty (str): Limit the number of servers returned.
            - by_user (str): If "true", filter servers by the current user's membership.
            - by_serverid (str): Filter servers by server ID.
            - with_num_members (str): If "true", include the number of members in the response.

        Returns:
            Response: A response containing the serialized server data.
        """
        queryset = self.get_filtered_queryset(request)

        # Implement pagination
        page = self.paginate_queryset(queryset, request, view=self)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)

        # Serialize the queryset
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def get_filtered_queryset(self, request):
        """
        Apply filters to the queryset based on request query parameters.
        """
        queryset = self.queryset

        # Retrieve query parameters
        category = request.query_params.get("category")
        qty = request.query_params.get("qty")
        by_user = request.query_params.get("by_user") == "true"
        by_serverid = request.query_params.get("by_serverid")
        with_num_members = request.query_params.get("with_num_members") == "true"

        # Filter by category if provided
        if category:
            queryset = queryset.filter(category__name=category)

        # Filter by the current user if 'by_user' is true
        if by_user:
            if request.user.is_authenticated:
                queryset = queryset.filter(member=request.user.id)
            else:
                raise AuthenticationFailed()

        # Annotate the queryset with the number of members if 'with_num_members' is true
        if with_num_members:
            queryset = queryset.annotate(num_members=Count("member"))

        # Filter by server ID if 'by_serverid' is provided
        if by_serverid:
            queryset = self.filter_by_server_id(queryset, by_serverid)

        # Limit the number of results if 'qty' is provided
        if qty:
            queryset = self.limit_results(queryset, qty)

        return queryset

    def filter_by_server_id(self, queryset, by_serverid):
        """
        Filter the queryset by server ID.
        """
        if not self.request.user.is_authenticated:
            raise AuthenticationFailed()

        try:
            queryset = queryset.filter(id=by_serverid)
            if not queryset.exists():
                raise ValidationError(detail=f"Server with id-{by_serverid} not found")
        except ValueError:
            raise ValidationError(detail="Server id must be an integer")

        return queryset

    def limit_results(self, queryset, qty):
        """
        Limit the number of results in the queryset.
        """
        try:
            queryset = queryset[: int(qty)]
        except ValueError:
            raise ValidationError(detail="qty must be an integer")
        return queryset
