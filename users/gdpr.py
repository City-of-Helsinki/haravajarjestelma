from django.contrib.auth import get_user_model
from helsinki_gdpr.types import ErrorResponse
from typing import Optional


def get_user(user: get_user_model()) -> get_user_model():
    """
    Function used by the Helsinki Profile GDPR API to get the "user" instance from the "GDPR Model"
    instance. Since in our case the GDPR Model and the user are one and the same, we simply return
    the same User instance that is given as a parameter.

    :param user: the User instance whose GDPR data is being queried
    :return: the same User instance
    """  # noqa: E501
    return user


def delete_data(user: get_user_model(), dry_run: bool) -> Optional[ErrorResponse]:
    """
    Function used by the Helsinki Profile GDPR API to delete all GDPR data collected of the user.
    The GDPR API package will run this within a transaction.

    :param  user: the User instance to be deleted along with related GDPR data
    :param dry_run: a boolean telling if this is a dry run of the function or not
    """  # noqa: E501

    user.delete()

    return None
