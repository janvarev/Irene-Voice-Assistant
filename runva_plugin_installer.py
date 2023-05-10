# Plugin installer

# alpha version

import subprocess
import os
import sys
import importlib.util
import shlex
import platform
import json



commandline_args = os.environ.get('COMMANDLINE_ARGS', "")
sys.argv += shlex.split(commandline_args)

python = sys.executable
git = os.environ.get('GIT', "git")
index_url = os.environ.get('INDEX_URL', "")
stored_commit_hash = None


def commit_hash():
    global stored_commit_hash

    if stored_commit_hash is not None:
        return stored_commit_hash

    try:
        stored_commit_hash = run(f"{git} rev-parse HEAD").strip()
    except Exception:
        stored_commit_hash = "<none>"

    return stored_commit_hash


def run(command, desc=None, errdesc=None, custom_env=None, live=False):
    if desc is not None:
        print(desc)

    if live:
        result = subprocess.run(command, shell=True, env=os.environ if custom_env is None else custom_env)
        if result.returncode != 0:
            raise RuntimeError(f"""{errdesc or 'Error running command'}.
Command: {command}
Error code: {result.returncode}""")

        return ""

    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True,
                            env=os.environ if custom_env is None else custom_env)

    if result.returncode != 0:
        message = f"""{errdesc or 'Error running command'}.
Command: {command}
Error code: {result.returncode}
stdout: {result.stdout.decode(encoding="utf8", errors="ignore") if len(result.stdout) > 0 else '<empty>'}
stderr: {result.stderr.decode(encoding="utf8", errors="ignore") if len(result.stderr) > 0 else '<empty>'}
"""
        raise RuntimeError(message)

    return result.stdout.decode(encoding="utf8", errors="ignore")


def check_run(command):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    return result.returncode == 0


def is_installed(package):
    try:
        spec = importlib.util.find_spec(package)
    except ModuleNotFoundError:
        return False

    return spec is not None


def run_python(code, desc=None, errdesc=None):
    return run(f'"{python}" -c "{code}"', desc, errdesc)

def run_pip(command, desc=None, live=False):

    index_url_line = f' --index-url {index_url}' if index_url != '' else ''
    return run(f'"{python}" -m pip {command} --prefer-binary{index_url_line}', desc=f"Installing {desc}",
               errdesc=f"Couldn't install {desc}", live=live)


def check_run_python(code):
    return check_run(f'"{python}" -c "{code}"')


def git_clone(url, dir, name, commithash=None):
    # TODO clone into temporary dir and move if successful

    if os.path.exists(dir):
        if commithash is None:
            return

        current_hash = run(f'"{git}" -C "{dir}" rev-parse HEAD', None,
                           f"Couldn't determine {name}'s hash: {commithash}").strip()
        if current_hash == commithash:
            return

        run(f'"{git}" -C "{dir}" fetch', f"Fetching updates for {name}...", f"Couldn't fetch {name}")
        run(f'"{git}" -C "{dir}" checkout {commithash}', f"Checking out commit for {name} with hash: {commithash}...",
            f"Couldn't checkout commit {commithash} for {name}")
        return

    run(f'"{git}" clone "{url}" "{dir}"', f"Cloning {name} into {dir}...", f"Couldn't clone {name}", live=True)

    if commithash is not None:
        run(f'"{git}" -C "{dir}" checkout {commithash}', None, "Couldn't checkout {name}'s hash: {commithash}")


def git_pull_recursive(dir):
    for subdir, _, _ in os.walk(dir):
        if os.path.exists(os.path.join(subdir, '.git')):
            try:
                output = subprocess.check_output([git, '-C', subdir, 'pull', '--autostash'])
                print(f"Pulled changes for repository in '{subdir}':\n{output.decode('utf-8').strip()}\n")
            except subprocess.CalledProcessError as e:
                print(f"Couldn't perform 'git pull' on repository in '{subdir}':\n{e.output.decode('utf-8').strip()}\n")

temp_plugin_git_path = 'temp/temp_git_plugin'

def install_plugin(url):
    import os
    import shutil

    git_clone(url, temp_plugin_git_path, "...cloning from GIT")

    import subprocess
    import shutil
    import os
    import stat
    from os import path

    for root, dirs, files in os.walk("./"+temp_plugin_git_path):
        for dir in dirs:
            os.chmod(path.join(root, dir), stat.S_IRWXU)
        for file in files:
            os.chmod(path.join(root, file), stat.S_IRWXU)

    shutil.rmtree(temp_plugin_git_path+"/.git")

    if os.path.exists(temp_plugin_git_path+"/requirements.txt"):
        print("Устанавливаем зависимости...")
        run_pip(f"install -r {temp_plugin_git_path}/requirements.txt", "requirements.txt", True)

    from os import listdir
    from os.path import isfile, join
    onlyfiles = [f for f in listdir(temp_plugin_git_path) if isfile(join(temp_plugin_git_path, f)) and f.startswith("plugin_") and f.endswith(".py")]




    for file in onlyfiles:
        print(f"Копируем {file}...")
        shutil.copyfile(temp_plugin_git_path+"/"+file,"plugins/"+file)

    remove_temp_plugin_git_folder()

    print("Завершено!")

def remove_temp_plugin_git_folder():
    import os
    import shutil

    if os.path.exists(temp_plugin_git_path) and os.path.isdir(temp_plugin_git_path):
        shutil.rmtree(temp_plugin_git_path)



if __name__ == "__main__":
    remove_temp_plugin_git_folder()

    # approved_plugins_list = [
    #     {"name": "plugin_boltalka_openai",
    #      "plugin_file_check": "plugin_boltalka_openai.py",
    #      "url": "https://github.com/janvarev/irene_plugin_boltalka_openai",
    #      "description": "Болталка с OpenAI",
    #      "added": "2023-05-10"},
    #     ]

    # import urllib.request
    #
    # with urllib.request.urlopen('https://raw.githubusercontent.com/wiki/janvarev/Irene-Voice-Assistant/PluginsJSON.md',) as f:
    #     html = f.read().decode('utf-8')
    with open('plugins_catalog.json', 'r', encoding="utf-8") as f:
        s = f.read()

    #print(s)

    import json

    json_info = json.loads(s)
    approved_plugins_list = json_info["plugins"]


    #run_pip("install deep_translator",None,True)
    #git_clone("https://github.com/Mmm-Vvv/Romeo_plugins","temp/Romeo_plugins","Romeo plugins")
    print("Менеджер плагинов Ирины (альфа-версия)")
    print("*"*40)
    print("ВНИМАНИЕ: Предложенные плагины поддерживаются сторонними разработчиками и они могут дополняться и изменяться!\nАвтор Ирины не несёт ответственности за их содержание!")
    print("*" * 40)

    print("Выберите плагин для установки:")
    print("0) Самостоятельно задать адрес Github-проекта с плагином")
    for i in range(len(approved_plugins_list)):
        cur_pl = approved_plugins_list[i]
        print("{0}) {1} | {2}".format(i+1,cur_pl["name"],cur_pl["url"]))
        print("  ",cur_pl["description"])

    print()
    print("Введите номер плагина> ", end='')
    user_choice = int(input())
    if user_choice > 0:
        choice = user_choice-1
        print("Начинаем установку плагина {0}".format(approved_plugins_list[choice]["description"]))
        install_plugin(approved_plugins_list[choice]["url"])
    elif user_choice == 0:
        print("Введите URL проекта плагина на Гитхабе> ", end='')
        user_url = input()
        print("Начинаем установку...")
        install_plugin(user_url)
