from rest_framework import serializers
from rest_framework.reverse import reverse


class TaskDetailHyperlink(serializers.HyperlinkedIdentityField):
    # We define these as class attributes, so we don't need to pass them as arguments.
    def get_url(self, obj, view_name, request, format):
        url_kwargs = {"pk": obj.project.pk, "task_id": obj.pk}
        return reverse(view_name, kwargs=url_kwargs, request=request, format=format)
