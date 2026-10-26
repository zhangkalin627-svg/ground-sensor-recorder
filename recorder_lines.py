"""Recorder window with one extra button: import a text line log (v0.41.0).

Run:  python recorder_lines.py
It is the 0.2.0 recorder window (recorder.App) plus a read-only import of a
text line log through replay_session. The log is parsed, bad lines are listed
in anomalies.csv, and the good samples replay in the chart. After an import the
window keeps one status line with the bad line count. No hardware is opened and
nothing is written to any device. Needs a display (Tk).
"""
import time

from recorder import App
import replay_session
import import_status


class LineApp(App):
    def __init__(self, root):
        super().__init__(root)
        from tkinter import StringVar, ttk
        root.title('地面传感器记录器 · v0.41.0（文本行导入）')
        ttk.Button(root, text='导入文本行日志并回放（只读）',
                   command=self.import_lines).pack(anchor='w', padx=20, pady=2)
        self.lines_status = StringVar(value='最近一次导入：尚未导入')
        ttk.Label(root, textvariable=self.lines_status).pack(
            anchor='w', padx=20, pady=2)

    def update_lines_status(self, result):
        """Keep the latest import summary visible in the recorder window."""
        self.lines_status.set(import_status.status_from_result(result))

    def import_lines(self):
        from tkinter import filedialog, messagebox
        path = filedialog.askopenfilename(
            filetypes=[('文本日志', '*.txt *.log *.csv'), ('所有文件', '*.*')])
        if not path:
            return
        base = filedialog.askdirectory(
            title='选择保存目录（生成 samples.csv、anomalies.csv、device.json）')
        if not base:
            return
        if not self.confirm_discard():
            return
        try:
            result = replay_session.import_lines(path, base)
        except (OSError, ValueError) as e:
            self.lines_status.set('最近一次导入：失败，' + str(e))
            messagebox.showerror('导入失败', str(e))
            return
        self.close_session('切换到文本行回放')
        self.replay, self.rows = result.samples, list(result.samples)
        self.window.clear()
        self.index, self.started, self.mode = 0, time.monotonic(), 'replay'
        self.save_status.set('已保存：' + str(result.directory))
        self.update_lines_status(result)
        self.draw()
        messagebox.showinfo('导入完成', replay_session.summary_text(result))


if __name__ == '__main__':
    import tkinter as tk
    LineApp(tk.Tk())
    tk.mainloop()
