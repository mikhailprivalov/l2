import os

base = '/Users/mp/prj/pool-core/'
extensions = ('.json', '.js')
exclude_directories = {'node_modules'}
n = 0
s = ""
for dname, dirs, files in os.walk(base):
    dirs[:] = [d for d in dirs if d not in exclude_directories]
    for fname in files:
        if fname.lower().endswith(extensions):
            n += 1
            fpath = os.path.join(dname, fname)
            fpath_r = os.path.join(dname, fname).replace(base, '')
            with open(fpath, 'r', encoding="utf-8") as content_file:
                content = content_file.read()
                s += f"Файл {n}\n"
                s += f"{fpath_r}\n"
                s += content
                s += "\n\n"
print(s)
