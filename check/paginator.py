from django.core.paginator import Paginator


class ValidPaginator(Paginator):

    def validate_number(self, number):
        try:
            number = int(number)
        except (ValueError, TypeError):
            number = 1

        if number < 1:
            number = 1
        elif number > self.num_pages:
            number = self.num_pages
        return number
