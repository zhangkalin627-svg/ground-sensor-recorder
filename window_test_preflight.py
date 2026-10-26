"""Check whether Tk window smoke tests can start in this environment."""
import importlib
import os
import sys


def check_tk_environment(tk_module=None, environ=None, platform=None):
    """Return (available, explanation) without leaving a Tk window open."""
    env = os.environ if environ is None else environ
    system = sys.platform if platform is None else platform

    if tk_module is None:
        try:
            tk_module = importlib.import_module('tkinter')
        except Exception as exc:
            return False, f'Tkinter 不可用：{exc}'

    if system not in ('win32', 'darwin') and not env.get('DISPLAY'):
        return False, '未设置 DISPLAY；请在图形会话中运行，或使用 xvfb-run -a。'

    try:
        root = tk_module.Tk()
    except Exception as exc:
        return False, f'Tk 无法启动显示环境：{exc}'

    try:
        root.withdraw()
    except Exception as exc:
        try:
            root.destroy()
        except Exception:
            pass
        return False, f'Tk 无法启动显示环境：{exc}'

    try:
        root.destroy()
    except Exception as exc:
        return False, f'Tk 测试窗口无法关闭：{exc}'

    return True, 'Tk 和显示环境可用。'


def main():
    available, message = check_tk_environment()
    print(message)
    return 0 if available else 2


if __name__ == '__main__':
    raise SystemExit(main())
