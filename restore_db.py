import sys
import os
import subprocess
import importlib.util

if len(sys.argv) < 2:
    print('Использование: python restore_db.py <путь_к_sql_файлу>')
    sys.exit(1)

sql_path = sys.argv[1]
if not os.path.isfile(sql_path):
    print(f'Файл не найден: {sql_path}')
    sys.exit(1)

settings_path = os.path.join('laboratory', 'local_settings.py')
spec = importlib.util.spec_from_file_location('local_settings', settings_path)
settings = importlib.util.module_from_spec(spec)
spec.loader.exec_module(settings)

db = settings.DATABASES['default']

psql_cmd = [
    'psql',
    '-h', db['HOST'],
    '-p', str(db['PORT']),
    '-U', db['USER'],
    '-d', db['NAME'],
    '-f', sql_path
]

env = os.environ.copy()
if db['PASSWORD']:
    env['PGPASSWORD'] = db['PASSWORD']

print('Восстанавливаю базу данных...')
try:
    subprocess.run(psql_cmd, check=True, env=env)
    print('База данных успешно восстановлена!')
except subprocess.CalledProcessError as e:
    print('Ошибка при восстановлении базы данных!')
    sys.exit(e.returncode) 