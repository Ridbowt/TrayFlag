# run_trayflag.py
import os
import sys
import subprocess
import ctypes

try:
    # Определяем пути относительно нашего .exe
    base_path = os.path.dirname(os.path.abspath(sys.executable))
    bin_path = os.path.join(base_path, 'bin')
    main_executable_path = os.path.join(bin_path, 'TrayFlag_core.exe')

    # Проверяем, на месте ли ядро
    if not os.path.exists(main_executable_path):
         raise FileNotFoundError(f"Core executable not found at:\n{main_executable_path}")

    # Создаем окружение для дочернего процесса
    env = os.environ.copy()
    # Добавляем папку 'bin' в PATH. Это ключ к успеху.
    env['PATH'] = bin_path + os.pathsep + env.get('PATH', '')
    
    # Устанавливаем рабочую директорию, чтобы .ini создавался где надо
    working_directory = base_path

    # Запускаем ядро как новый, независимый процесс
    subprocess.Popen(
        [main_executable_path], 
        env=env, 
        cwd=working_directory,
        creationflags=0x08000000  # CREATE_NO_WINDOW
    )

except Exception as e:
    # Если что-то пошло не так, мы увидим ошибку!
    error_message = f"Failed to launch TrayFlag Core:\n\n{e}"
    ctypes.windll.user32.MessageBoxW(0, error_message, "Launcher Error", 16) # 16 = MB_ICONERROR