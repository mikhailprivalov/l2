from django.db.models import Q

from dynamic_directory.models import Directory


def get_child_directories(root_directory_pk, title_filter=None, recursive=True):
    directories = Directory.objects.filter(root_directory_id=root_directory_pk).order_by('title')

    if title_filter:
        directories = directories.filter(Q(title__istartswith=str(title_filter)) | Q(code__istartswith=str(title_filter)))

    directories = directories.order_by('title')

    result = []

    directory: Directory
    for directory in directories:
        child = get_child_directories(directory.pk, title_filter=title_filter) if recursive else []
        result.append(
            {
                **directory.to_json(),
                "child": child,
            }
        )

    return result
