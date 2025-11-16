from django.utils.deprecation import MiddlewareMixin
from .models import Employee

class BranchMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Set branch for authenticated users
        if request.user.is_authenticated:
            try:
                employee = Employee.objects.get(user=request.user)
                request.branch = employee.branch
                request.employee = employee
            except Employee.DoesNotExist:
                request.branch = None
                request.employee = None
        else:
            request.branch = None
            request.employee = None



