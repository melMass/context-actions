from pathlib import Path

NAMESPACE = "mtbContext"
VERSION = "v0.0.1"


# region methods
def create_subcommand_key(
    ext: tuple[str],
    namespace: str,
    menu_name: str,
    action: str,
    actions_dir: Path,
    details,
    key_base: str,
    command_prefix="cmd /k",
):
    sub_command = f"{namespace}.{menu_name}.{action}"

    # Correctly escape backslashes
    command = details.get("command")
    script = details.get("script")

    command_formatted = None

    if command:
        command = command.replace("\\", "\\\\")
        command_formatted = command.replace('"', '\\"')

    if script:
        script = str(actions_dir / script).replace("\\", "\\\\")

        command_formatted = (
            f'{command_prefix} \\"\\"{script}\\" \\"%1\\"\\"'
            if command_prefix
            else f'"{script} "%1"'
        )

    entries = [
        f"[{key_base}\\shell\\{sub_command}]",
        f'"MUIVerb"="{details.get("description", action)}"',
        f"[{key_base}\\shell\\{sub_command}\\command]",
        f'@="{command_formatted}"',
    ]
    return "\n".join(entries)


def create_root_menu_key(
    prefix, key_base: str, menu_name: str, actions, install_dir="C:\\context-actions"
):
    icon_path = None
    for action, details in actions.items():
        if "icon" in details:
            icon_path = details["icon"].replace("\\", "\\\\")
            # Assuming all actions under a menu will share the same icon
            break
    if icon_path is None:
        ico = Path(f"bucket/{prefix}.ico")
        if ico.exists():
            install_dir = Path(install_dir)
            icon_path = install_dir / "icons" / ico.name
            icon_path = str(icon_path).replace("\\", "\\\\")

    icon_entry = f'"Icon"="{icon_path}"' if icon_path else ""
    entries = [
        f"[{key_base}]",
        f'"MUIVerb"="{menu_name}"',
        '"SubCommands"=""',  # Empty SubCommands for triggering submenus
        icon_entry,
    ]
    return "\n".join(filter(None, entries))


def create_reg_file(prefix, extensions, version, install_dir="C:\\context-actions"):
    install_dir = Path(install_dir)
    actions_dir = install_dir / "actions"

    file_name = f"dist/install_{prefix}_context_menu_v{version}.reg"

    with open(file_name, "w") as file:
        file.write("Windows Registry Editor Version 5.00\n\n")

        ext_group = extensions.get("exts")
        defs = extensions.get("defs")

        for menu_name, actions in defs.items():
            for ext in ext_group:
                if ext == "directory":
                    key_base = f"HKEY_CURRENT_USER\\Software\\Classes\\Directory\\shell\\{NAMESPACE}.{menu_name}"
                else:
                    key_base = f"HKEY_CURRENT_USER\\Software\\Classes\\SystemFileAssociations\\.{ext}\\shell\\{NAMESPACE}.{menu_name}"

                root_menu_key = create_root_menu_key(
                    prefix, key_base, menu_name, actions
                )
                file.write(root_menu_key + "\n\n")
                for action, details in actions.items():
                    subcommand_key = create_subcommand_key(
                        ext,
                        NAMESPACE,
                        menu_name,
                        action,
                        actions_dir,
                        details,
                        key_base=key_base,
                    )
                    file.write(subcommand_key + "\n\n")

    return file_name


def create_uninstall_reg_file(prefix, extensions, version):
    file_name = f"dist/uninstall_{prefix}_context_menu_v{version}.reg"

    with open(file_name, "w") as file:
        file.write("Windows Registry Editor Version 5.00\n\n")

        ext_group = extensions.get("exts")
        defs = extensions.get("defs")

        for menu_name in defs.keys():
            for ext in ext_group:
                if ext == "directory":
                    key_base = f"HKEY_CURRENT_USER\\Software\\Classes\\Directory\\shell\\{NAMESPACE}.{menu_name}"
                else:
                    key_base = f"HKEY_CURRENT_USER\\Software\\Classes\\SystemFileAssociations\\.{ext}\\shell\\{NAMESPACE}.{menu_name}"

                # Remove root menu key
                file.write(f"[-{key_base}]\n")

                # Remove sub-menu keys
                for action in defs[menu_name]:
                    sub_command = f"{NAMESPACE}.{menu_name}.{action}"
                    file.write(f"[-{key_base}\\shell\\{sub_command}]\n")


def create_batch_files(
    prefix, install_reg, uninstall_reg, script_dir, target_dir, version
):
    # Create install.bat
    with open(f"install_{prefix}_v{version}.bat", "w") as file:
        file.write("@echo off\n")

        # check_version_script = check_version_in_registry_strict(prefix)
        # file.write(f"{check_version_script}\n")
        # file.write("IF %ERRORLEVEL% EQU 1 (\n")
        # file.write("    ECHO The current version ({VERSION}) is already installed.\n")
        # file.write("    pause\n")
        # file.write("    exit /b 1\n")
        # file.write(")\n")
        check_version_script = check_version_in_registry(prefix)
        file.write(f"{check_version_script}\n")
        file.write("IF %ERRORLEVEL% EQU 1 (\n")
        file.write(
            f"    ECHO A version of {prefix} is already installed. Please uninstall the previous version before installing a new one.\n"
        )
        file.write("    pause\n")
        file.write("    exit /b 1\n")
        file.write(")\n")

        # make install dir
        file.write(f'if not exist "{target_dir}" mkdir "{target_dir}"\n')
        # add actions subdir
        file.write(
            f'if not exist "{target_dir}\\actions" mkdir "{target_dir}\\actions"\n'
        )
        # copy scripts to actions dir
        file.write(f'xcopy "{script_dir}\\*" "{target_dir}\\actions\\" /I /Y\n')
        # copy uninstall bat file to install dir
        file.write(f'xcopy "uninstall_{prefix}.bat" "{target_dir}\\" /I /Y\n')
        # create a dist dir in install dir
        file.write(f'if not exist "{target_dir}\\dist" mkdir "{target_dir}\\dist"\n')
        # copy the reg uninstall used by the bat
        file.write(
            f'xcopy "dist\\uninstall_{prefix}_context_menu.reg" "{target_dir}\\dist\\" /I /Y\n'
        )
        if Path(f"bucket/{prefix}.ico").exists():
            file.write(
                f'if not exist "{target_dir}\\icons" mkdir "{target_dir}\\icons"\n'
            )
            file.write(f'xcopy "bucket\\{prefix}.ico" "{target_dir}\\icons\\" /I /Y\n')

        # import the install reg file
        file.write(f'reg import "{install_reg}"\n')
        reg_version_key = f"HKEY_CURRENT_USER\\Software\\{NAMESPACE}.{prefix}\\Version"
        file.write(f'reg add "{reg_version_key}" /v "Version" /d "{version}" /f\n')
        file.write("echo Installation complete.\n")
        file.write("pause\n")

    # Create uninstall.bat
    with open(f"uninstall_{prefix}_v{version}.bat", "w") as file:
        file.write("@echo off\n")
        # Move scripts to trash using PowerShell
        # file.write(
        #     f'PowerShell -ExecutionPolicy Bypass -File "{ps_script}" -targetDir "{target_dir}"\n'
        # )

        check_version_script = check_version_in_registry(prefix)
        file.write(f"{check_version_script}\n")
        file.write("IF %ERRORLEVEL% EQU 0 (\n")
        file.write(f"    ECHO No installation of {prefix} found. Aborting.")
        file.write("    pause\n")
        file.write("    exit /b 1\n")
        file.write(")\n")
        # Remove registry settings
        file.write(f'reg import "{uninstall_reg}"\n')
        file.write("echo Uninstallation complete.\n")
        file.write("pause\n")


def import_definitions(file_name):
    import json

    with open(file_name, "r") as file:
        return json.load(file)


def check_version_in_registry_strict(prefix, version):
    reg_version_key = f"HKEY_CURRENT_USER\\Software\\{NAMESPACE}.{prefix}\\Version"
    check_version_script = f"PowerShell -Command \"& {{if ((Get-ItemProperty -Path 'Registry::{reg_version_key}' -Name Version -ErrorAction SilentlyContinue).Version -eq '{version}') {{exit 1}} else {{exit 0}} }}\""
    return check_version_script


def check_version_in_registry(prefix):
    reg_base_key = f"HKEY_CURRENT_USER\\Software\\{NAMESPACE}.{prefix}"
    check_version_script = f"PowerShell -Command \"& {{if (Test-Path 'Registry::{reg_base_key}') {{exit 1}} else {{exit 0}} }}\""
    return check_version_script


def old_version_check(file, prefix):
    file.write('SET KEY_NAME="HKEY_CURRENT_USER\\Software\\%s"\n' % prefix)
    file.write("REG QUERY %KEY_NAME% >nul 2>nul\n")
    file.write("IF %ERRORLEVEL% EQU 0 (\n")
    file.write(
        "    ECHO An existing version of %s is installed. Please uninstall the previous version before installing a new one.\n"
        % prefix
    )
    file.write("    pause\n")
    file.write("    exit /b 1\n")
    file.write(")\n")


# endregion

if __name__ == "__main__":
    import argparse
    from pathlib import Path

    Path("dist").mkdir(parents=True, exist_ok=True)

    parser = argparse.ArgumentParser("context menu generator")
    parser.add_argument("definition_file", help="path to definition file")
    parser.add_argument("--version", default=VERSION, help="the version to generate")

    args = parser.parse_args()
    def_file = Path(args.definition_file)
    if not def_file.exists():
        print(f"Definition file {def_file} does not exist.")

    file_associations = import_definitions(args.definition_file)
    version = args.version[1:] if args.version.startswith("v") else args.version
    prefix = def_file.stem

    print(f"Generating install files for {NAMESPACE}.{prefix} v{version}")

    install_reg = create_reg_file(prefix, file_associations, version)
    uninstall_reg = create_uninstall_reg_file(prefix, file_associations, version)

    create_batch_files(
        prefix,
        install_reg,
        uninstall_reg,
        script_dir="actions",
        target_dir="C:\\context-actions",
        version=version,
    )

    print(f"Installation and uninstallation files for {prefix} created.")
