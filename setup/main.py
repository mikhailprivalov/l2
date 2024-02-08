import ast
import datetime
import json
import sys
import tempfile
import traceback
import os
import shutil
import subprocess
import uuid

import boto3
from prompt_toolkit.shortcuts import radiolist_dialog, input_dialog, yes_no_dialog, ProgressBar, message_dialog
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import dotenv_values

from take_release import get_current_version

L2_SETUPS_S3_BUCKET = 'l2-setups'
ROOT_DIR = os.path.abspath(os.curdir)
config = dotenv_values(os.path.join(ROOT_DIR, '.env'))


def copytree(src, dst, symlinks=False, ignore=None):
    if not os.path.exists(dst):
        os.makedirs(dst)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            copytree(s, d, symlinks, ignore)
        else:
            if not os.path.exists(d) or os.stat(s).st_mtime - os.stat(d).st_mtime > 1:
                shutil.copy2(s, d)


def which_tool(name):
    from shutil import which

    return which(name)


def copy_and_overwrite(from_path, to_path):
    if os.path.isdir(from_path):
        if os.path.exists(to_path):
            shutil.rmtree(to_path)
        shutil.copytree(from_path, to_path)
    else:
        if os.path.exists(to_path):
            os.remove(to_path)
        shutil.copyfile(from_path, to_path)


def upload_folder_to_s3(s3, dn, s3p):
    try:
        for path, subdirs, files in os.walk(dn):
            for file in files:
                dest_path = path.replace(dn, "")
                __s3file = os.path.normpath(s3p + '/' + dest_path + '/' + file)
                __local_file = os.path.join(path, file)
                print("Uploading:", __local_file, "to Target:", __s3file, end="")
                s3.upload_file(__local_file, L2_SETUPS_S3_BUCKET, __s3file)
                print(" ...Success")
    except Exception as e:
        print("S3 Failed")
        print(e)
        raise e


def get_s3_content(s3):
    print('Getting', L2_SETUPS_S3_BUCKET, 'directories')
    c = s3.list_objects_v2(Bucket=L2_SETUPS_S3_BUCKET, Prefix='l2-config_', Delimiter='/')
    for v in c.get('CommonPrefixes', []):
        yield str(v['Prefix']).rstrip('/')


def get_s3_file(s3, config, file):
    k = f"{config}/{file}"
    print("Getting", k, 'from S3')
    get_object_response = s3.get_object(Bucket=L2_SETUPS_S3_BUCKET, Key=k)
    return get_object_response['Body'].read()


def get_s3_objects(s3, prefix):
    print('Getting', L2_SETUPS_S3_BUCKET + '/' + prefix, 'files')
    c = s3.list_objects_v2(Bucket=L2_SETUPS_S3_BUCKET, Prefix=prefix + '/')['Contents']
    for v in c:
        yield v['Key']


def get_tool_path(tool, output_check, check_args='--version'):
    print(f'Checking {tool}...')

    tool_path = which_tool(tool)

    if tool_path:
        print(tool, 'is ok!')
    else:
        tool_is_ok = False
        while not tool_is_ok:
            tool_path = input_dialog(title='pg_dump path', text=f'Enter path to {tool}:', ok_text='Check', default=tool_path or '').run()

            try:
                result = subprocess.run([tool_path, check_args], stdout=subprocess.PIPE)
                result = result.stdout.decode('utf-8')
                tool_is_ok = result.startswith(output_check)
            except Exception as e:
                print(e)

            if not tool_is_ok:
                try_again = yes_no_dialog(title=f'{tool} executable not found', text=f'{tool_path}\nDo you want to try again?').run()

                if not try_again:
                    sys.exit()
            print('Custom', tool, 'path is ok', tool_path)

    if os.name == 'nt':
        tool_path = f'"{tool_path}"'
    return tool_path


def enter():
    mode = radiolist_dialog(
        title="L2 setup mode",
        text="What mode of operation is required?",
        values=[
            ("setup", "Setup a new L2 instance"),
            ("save-config", "Create new setup config"),
        ],
    ).run()

    s3 = None

    print('Selected mode:', mode)

    if mode in ('setup', 'save-config'):
        is_s3_ok = False
        s3_id = config.get('S3_ACCESS_KEY_ID') or ''
        s3_secret = config.get('S3_SECRET_ACCESS_KEY') or ''

        while not is_s3_ok:
            s3_id = input_dialog(title='S3 settings', text='Enter access_key_id:', ok_text='Next', default=s3_id).run()

            s3_secret = input_dialog(title='S3 settings', text='Enter secret_access_key:', ok_text='Check', default=s3_secret).run()

            try:
                with ProgressBar(title='Checking S3 credentials') as pb:
                    steps = iter(pb(range(4)))

                    next(steps)
                    boto_session = boto3.session.Session()

                    next(steps)
                    s3 = boto_session.client(
                        service_name='s3', endpoint_url='https://storage.yandexcloud.net', region_name='ru-central1', aws_access_key_id=s3_id, aws_secret_access_key=s3_secret
                    )

                    next(steps)
                    has_bucket = False
                    resp = s3.list_buckets()
                    for bucket in resp['Buckets']:
                        if bucket['Name'] == L2_SETUPS_S3_BUCKET:
                            has_bucket = True

                    next(steps)
                    if not has_bucket:
                        s3.create_bucket(Bucket=L2_SETUPS_S3_BUCKET)

                    try:
                        next(steps)
                    except StopIteration:
                        pass

                    is_s3_ok = True
            except Exception as e:
                print(e)
                print(traceback.format_exc())

            if not is_s3_ok:
                try_again = yes_no_dialog(title='Credentials is invalid', text='Do you want to try again?').run()

                if not try_again:
                    sys.exit()

        go_to_next = yes_no_dialog(title='Credentials is ok', text=f'Do you want to continue in {mode} mode?').run()

        if not go_to_next:
            sys.exit()

        if mode == 'save-config':
            current_version = get_current_version()
            message_dialog(title='L2 system check', text=f'L2 version for saving config: {current_version}\n{ROOT_DIR}').run()

            import laboratory.settings as l2_settings

            db_settings = l2_settings.DATABASES["default"]
            DB_HOST = db_settings.get("HOST", '127.0.0.1')
            DB_PORT = db_settings.get('PORT', 5432)
            DB_NAME = db_settings.get('NAME', '<default>')
            DB_USER = db_settings.get('USER', '<default>')
            DB_PASSWORD = db_settings.get('PASSWORD')

            lines = [
                ('DB host', DB_HOST),
                ('DB port', DB_PORT),
                ('DB name', DB_NAME),
                ('DB user', DB_USER),
                ('DB password', '*********' if DB_PASSWORD else '<empty>'),
            ]

            message_dialog(
                title='L2 system check',
                text='\n'.join([f'{x[0]}: {x[1]}' for x in lines]),
            ).run()

            print('Checking DB connection')

            try:
                with psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD) as conn:
                    with conn.cursor() as cursor:
                        cursor.execute('SELECT VERSION()')
                        row = cursor.fetchone()
                        print(row[0])

                        with tempfile.TemporaryDirectory(suffix='_l2_setup') as dn:
                            print('Copying local_settings.py')
                            shutil.copyfile(os.path.join(ROOT_DIR, 'laboratory', 'local_settings.py'), os.path.join(dn, 'local_settings.py'))

                            print('Searching applications...')
                            applications = []
                            for a in l2_settings.INSTALLED_APPS:
                                if not a.startswith('django.'):
                                    n = a.split('.')[0]
                                    p = os.path.join(ROOT_DIR, n)
                                    if os.path.isdir(p):
                                        applications.append((n, p))
                                        print(n, p)

                            migrations_to_copy = []

                            for a in applications:
                                md = os.path.join(a[1], 'migrations')
                                if os.path.isdir(md):
                                    migrations_to_copy.append((a[0], md))

                            migrations_folder = os.path.join(dn, 'migrations')

                            with ProgressBar(title=f"Copying project generated migrations to temporary dir {dn}") as pb:
                                for md in pb(migrations_to_copy):
                                    pd = os.path.join(migrations_folder, md[0])
                                    os.makedirs(pd, exist_ok=True)
                                    pmd = os.path.join(pd, 'migrations')
                                    copytree(md[1], pmd)
                                    try:
                                        shutil.rmtree(os.path.join(pmd, '__pycache__'))
                                    except OSError:
                                        pass
                                    try:
                                        shutil.rmtree(os.path.join(pmd, 'migrations', '__pycache__'))
                                    except OSError:
                                        pass
                            print('Dump postgresql database', DB_NAME)
                            pg_dump_path = get_tool_path('pg_dump', 'pg_dump (PostgreSQL)')

                            command_for_dumping = (
                                f'{pg_dump_path} -v --host={DB_HOST} '
                                f'--port={DB_PORT} '
                                f'--dbname={DB_NAME} '
                                f'--username={DB_USER} '
                                f'--no-password '
                                f' | gzip > {os.path.join(dn, "dump.sql.gz")} '
                            )
                            print('Starting pg_dump...')
                            print(command_for_dumping)
                            dump_success = False
                            try:
                                proc = subprocess.Popen(command_for_dumping, shell=True, env={'PGPASSWORD': DB_PASSWORD or ''})
                                proc.communicate()
                                dump_success = True
                            except Exception as e:
                                print('Exception happened during dump')
                                print(e)

                            if not dump_success:
                                sys.exit()

                            config_name = input_dialog(title='Result saved to temporary folder', text='Optionally enter config name suffix:', ok_text='Ok', default='').run()

                            config_desc = input_dialog(title='Result saved to temporary folder', text='Optionally enter config description:', ok_text='Ok', default='').run()

                            config_name = config_name or str(uuid.uuid4())
                            generated_at = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                            config_name = f'l2-config_{generated_at}_{current_version.replace(".", "-").replace("+", "_")}_{config_name}'
                            cfg = {"name": config_name, "description": config_desc, "generatedAt": generated_at, "version": current_version}

                            with open(os.path.join(dn, 'config.json'), 'w', encoding='utf-8') as f:
                                json.dump(cfg, f, ensure_ascii=False, indent=4)

                            print('Saving to S3...')

                            upload_folder_to_s3(s3, dn, config_name)

                            print()
                            print('Config')
                            print(json.dumps(cfg, ensure_ascii=False, indent=4))
                            print()
            except Exception as e:
                print(e)
        elif mode == 'setup':
            values = list(get_s3_content(s3))
            values.sort(reverse=True)

            cfg = None
            ok = False
            while not ok:
                config_selected = radiolist_dialog(title="Select config for continue", text="One of configs, available in S3 (latest on top):", values=[(x, x) for x in values]).run()

                if not config_selected:
                    sys.exit()

                cfg = json.loads(get_s3_file(s3, config_selected, 'config.json'))

                if not cfg.get('name') or not cfg.get('generatedAt') or not cfg.get('version'):
                    message_dialog(
                        title='CONFIG IS INVALID',
                        text=json.dumps(cfg, ensure_ascii=False, indent=2),
                    ).run()
                    continue

                lines = [
                    ('Config name', cfg['name']),
                    ('Config description', cfg['description']),
                    ('Config generatedAt', cfg['generatedAt']),
                    ('Config L2 version', cfg['version']),
                    '',
                    'Config is ok?',
                ]

                go_to_next = yes_no_dialog(
                    title='L2 config details',
                    text='\n'.join([x if isinstance(x, str) else f'{x[0]}: {x[1]}' for x in lines]),
                ).run()

                if go_to_next:
                    ok = True

            need_version_checkout = yes_no_dialog(
                title='Do you want to checking out the version?',
                text=f'{cfg["version"]}',
            ).run()
            if need_version_checkout:
                print('Checking out version', cfg['version'])

                if os.name == 'nt':
                    proc = subprocess.Popen(['powershell', os.path.join(ROOT_DIR, 'checkout_version.ps1'), cfg['version']], shell=True)
                else:
                    proc = subprocess.Popen(os.path.join(ROOT_DIR, 'checkout_version.sh') + ' ' + cfg['version'], shell=True)
                proc.communicate()
                exit_code = proc.wait()
                checkout_result = exit_code == 0

                if not checkout_result:
                    print('Version checkout error')
                    go_to_next = yes_no_dialog(
                        title=f'Version {cfg["version"]} checkout error',
                        text='Do you want to continue without checking out the version?\n'
                             'This may not work correctly!\n'
                             'Your migrations and local_settings.py files will be replaced with setup!',
                    ).run()
                    if not go_to_next:
                        sys.exit()
            else:
                checkout_result = False

            with tempfile.TemporaryDirectory(suffix='_l2_setup') as dn:
                fl = list(get_s3_objects(s3, cfg['name']))
                files_to_copy = []
                sql_backup_file = None
                with ProgressBar(title=f"Downloading setup files to {dn}") as pb:
                    for f in pb(fl):
                        f_fixed = str(f).replace('/', os.path.sep)
                        file_dir, fn = os.path.split(os.path.join(dn, f_fixed))

                        os.makedirs(file_dir, exist_ok=True)
                        full_n = str(os.path.join(file_dir, fn))
                        s3.download_file(L2_SETUPS_S3_BUCKET, f, full_n)
                        if f_fixed.startswith(os.path.join(cfg['name'], 'migrations')) or f_fixed.endswith('local_settings.py'):
                            p, ln = os.path.split(full_n)
                            if p.endswith(os.path.sep + 'migrations'):
                                cn = p
                            else:
                                cn = full_n
                            if cn not in files_to_copy:
                                files_to_copy.append(cn)
                        elif f_fixed == os.path.join(cfg['name'], 'dump.sql.gz'):
                            sql_backup_file = full_n

                if not sql_backup_file:
                    message_dialog(
                        title='Database dump not found!',
                        text='File dump.sql.gz not found. Exit from setup.',
                    ).run()
                    sys.exit()

                base = os.path.join(dn, cfg['name'])
                local_settings_path = None

                with ProgressBar(title='Copying files from setup to L2') as pb:
                    for f in pb(files_to_copy):
                        dst = f.replace(base + os.path.sep, '')
                        if dst.startswith('migrations' + os.path.sep):
                            dst = dst.split(os.path.sep, maxsplit=1)[1]

                        if dst == 'local_settings.py':
                            dst = os.path.join(ROOT_DIR, 'laboratory', dst)
                            local_settings_path = dst
                        else:
                            dst = os.path.join(ROOT_DIR, dst)

                        copy_and_overwrite(f, dst)

                print('Starting configuring database connections')

                if not local_settings_path and os.path.isfile(os.path.join(ROOT_DIR, 'laboratory', 'local_settings.py')):
                    local_settings_path = os.path.join(ROOT_DIR, 'laboratory', 'local_settings.py')

                if not local_settings_path:
                    print('local_settings.py not found!')
                    sys.exit()

                db_content_lines = []
                settings_lines = []

                with open(local_settings_path, encoding='utf-8') as ls_file:
                    open_brackets_count = 0
                    close_brackets_count = 0
                    has_db_start = False
                    has_db_end = False
                    skip_add_line = False
                    for line in ls_file:
                        skip_add_line = False
                        if not has_db_end:
                            if line.startswith('DATABASES = {'):
                                has_db_start = True
                            if has_db_start:
                                db_content_lines.append(line.rstrip())
                                open_brackets_count += line.count('{')
                                close_brackets_count += line.count('}')
                                if close_brackets_count == open_brackets_count:
                                    has_db_end = True
                                    skip_add_line = True
                        if (not has_db_start or has_db_end) and not skip_add_line:
                            settings_lines.append(line.rstrip())

                DB = {
                    'NAME': 'l2',
                    'USER': 'postgres',
                    'HOST': '127.0.0.1',
                    'PORT': '5432',
                    'PASSWORD': '',
                }

                if db_content_lines:
                    db_content = ast.literal_eval('\n'.join(db_content_lines).lstrip('DATABASES = '))
                    print('Current DB settings:')
                    print(db_content)

                    for k in DB:
                        DB[k] = db_content.get('default', {}).get(k)
                else:
                    print('DATABASE not found in local_settings.py')

                db_is_ok = False
                while not db_is_ok:
                    for k in DB:
                        DB[k] = input_dialog(title=f'Enter {k} for database settings', text=f'{k}:', ok_text='Next', default=DB[k] or '').run()

                    lines = [
                        *[(k, v) for k, v in DB.items()],
                        '',
                        'Config is ok?',
                    ]

                    go_to_next = yes_no_dialog(
                        title='L2 database config details',
                        text='\n'.join([x if isinstance(x, str) else f'{x[0]}: {x[1]}' for x in lines]),
                    ).run()

                    if go_to_next:
                        db_is_ok = True

                    try:
                        print(f'Connecting to database {DB["NAME"]}...')
                        with psycopg2.connect(host=DB['HOST'], port=DB['PORT'], dbname=DB['NAME'], user=DB['USER'], password=DB['PASSWORD'] or None) as conn:
                            with conn.cursor() as cursor:
                                cursor.execute("SELECT PG_CLIENT_ENCODING()")
                                client_encoding = cursor.fetchone()[0]
                                print("Client Encoding:", client_encoding)

                            with conn.cursor() as cursor:
                                cursor.execute('SELECT VERSION()')
                                row = cursor.fetchone()
                                print('Postgresql version:', row[0])
                    except Exception as e:
                        m = str(e)
                        print(m)
                        traceback.print_exc()

                        if f'database "{DB["NAME"]}" does not exist' in m:
                            go_to_next = yes_no_dialog(
                                title=f'Database {DB["NAME"]} does not exist',
                                text='Do you want to try to create this database?',
                            ).run()

                            if not go_to_next:
                                sys.exit()

                            print('Connecting to default db...')
                            try:
                                connection = psycopg2.connect(host=DB['HOST'], port=DB['PORT'], user=DB['USER'], password=DB['PASSWORD'] or None)
                                connection.set_client_encoding('UTF8')
                                connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                                cursor = connection.cursor()
                                cursor.execute(sql.SQL("CREATE DATABASE {dbname}").format(dbname=sql.Identifier(DB['NAME'])))
                                cursor.close()
                                with psycopg2.connect(host=DB['HOST'], port=DB['PORT'], dbname=DB['NAME'], user=DB['USER'], password=DB['PASSWORD'] or None) as conn:
                                    with conn.cursor() as cursor:
                                        cursor.execute("SELECT PG_CLIENT_ENCODING()")
                                        client_encoding = cursor.fetchone()[0]
                                        print("Client Encoding:", client_encoding)
                                    with conn.cursor() as cursor:
                                        cursor.execute('SELECT VERSION()')
                                        row = cursor.fetchone()
                                        print('Postgresql version:', row[0])
                                        print('Database successfully created!')
                            except Exception as e:
                                print(e)
                                traceback.print_exc()
                                db_is_ok = False
                                go_to_next = yes_no_dialog(
                                    title='Failed to create database',
                                    text=f'{m}\nTry again?',
                                ).run()

                                if not go_to_next:
                                    sys.exit()
                            finally:
                                if connection:
                                    connection.close()
                        else:
                            db_is_ok = False
                            go_to_next = yes_no_dialog(
                                title='Failed to connect database',
                                text=f'{m}\nTry again?',
                            ).run()

                            if not go_to_next:
                                sys.exit()

                psql_path = get_tool_path('psql', 'psql (PostgreSQL)')
                print(psql_path)

                pv = which_tool('pv')
                pv_retry = not pv and os.name != 'nt'
                while pv_retry:
                    pv_retry = yes_no_dialog(
                        title='Command pv not found',
                        text='pv is a useful tool that allows you to track the process of unpacking a dump.\nYou can install it with:\nsudo apt install pv\nor\nbrew install pv\n\n'
                        'Do you want to try again after installing it?\nUse another terminal for installation.',
                    ).run()
                    if pv_retry:
                        pv = which_tool('pv')
                        pv_retry = not pv

                gunzip = which_tool('gunzip')
                gzip = which_tool('gzip')
                zcat = which_tool('zcat')

                if not gunzip and not zcat and not gzip:
                    print('gunzip or zcat not found in system')
                    sys.exit()

                if zcat:
                    unzip_command = f'{zcat} {sql_backup_file}'
                elif gunzip:
                    unzip_command = f'{gunzip} < {sql_backup_file}'
                else:
                    unzip_command = f'{gzip} -d -c {sql_backup_file}'
                if pv:
                    unzip_command = f'{pv} {sql_backup_file} | {zcat or gunzip}'

                if os.name == 'nt':
                    psql_command = f'{psql_path} -P pager=off -h {DB["HOST"]} -p {DB["PORT"]} -U {DB["USER"]} -d {DB["NAME"]} --no-password'
                else:
                    psql_command = f'{psql_path} {DB["NAME"]} -P pager=off --host={DB["HOST"]} --port={DB["PORT"]} --username={DB["USER"]} --no-password'

                restore_success = False
                try:
                    if os.name == 'nt':
                        print('Starting restoring...')
                        print(unzip_command)
                        print('piped to')
                        print(psql_command)
                        proc_unzip = subprocess.Popen(unzip_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        proc_psql = subprocess.Popen(psql_command, shell=True, stdin=proc_unzip.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        proc_unzip.stdout.close()
                        proc_unzip.stderr.close()
                        while True:
                            output = proc_psql.stdout.readline()
                            if output == b'' and proc_psql.poll() is not None:
                                break
                            if output:
                                print(output.strip())
                        proc_psql.communicate()
                    else:
                        command_for_restoring = f'{unzip_command} | {psql_command}'
                        print('Starting restoring...')
                        print(command_for_restoring)
                        env_s = {'PGPASSWORD': DB['PASSWORD'] or ''}
                        proc = subprocess.Popen(command_for_restoring, shell=True, env=env_s)
                        proc.communicate()
                    restore_success = True
                except Exception as e:
                    print('Exception happened during restoring')
                    print(e)

                if not restore_success:
                    sys.exit()
                print('Saving database config to local_settings.py')
                settings_lines.append('')
                settings_lines.append('DATABASES = {')
                settings_lines.append("    'default': {")
                settings_lines.append("        'ENGINE': 'django.db.backends.postgresql_psycopg2',")
                settings_lines.append(f"        'NAME': '{DB['NAME']}',")
                settings_lines.append(f"        'USER': '{DB['USER']}',")
                if DB['PASSWORD']:
                    settings_lines.append(f"        'PASSWORD': '{DB['PASSWORD']}',")
                settings_lines.append(f"        'HOST': '{DB['HOST']}',")
                settings_lines.append(f"        'PORT': '{DB['PORT']}',")
                settings_lines.append("    }")
                settings_lines.append("}")
                settings_lines.append('')

                settings = '\n'.join(settings_lines)
                with open(local_settings_path, 'w', encoding='utf-8') as f:
                    f.write(settings)

                message_dialog(title='Success', text='Setup successfully finished.\nmigrations: copied\nlocal_settings.py: copied\ndb config: is ok\ndatabase dump: restored').run()
                post_install = yes_no_dialog(
                    title='Post install',
                    text='Do you want to run post install scripts (migrations, collect static)?',
                ).run()

                if post_install:
                    if checkout_result:
                        proc = subprocess.Popen("make postinstall", shell=True)
                    else:
                        proc = subprocess.Popen("make postinstall_with_build_front", shell=True)
                    proc.communicate()
