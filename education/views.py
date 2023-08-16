from education.sql_func import get_connection_params, get_all_enrollee


def create_connection_string(settings_name: str):
    connection_params = get_connection_params(settings_name)[0]
    connection_string = f"DRIVER={connection_params.driver}; SERVER={connection_params.ip_address}; DATABASE={connection_params.database}; Encrypt={connection_params.encrypt}; " \
                        f"UID={connection_params.login}; PWD={connection_params.password}"
    return connection_string


def get_enrollee():
    connection_string = create_connection_string('MMIS')
    result = get_all_enrollee(connection_string)
    return result
