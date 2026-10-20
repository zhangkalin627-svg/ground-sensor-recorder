"""Ground sensor recorder 0.2.0. Standard library only; no control outputs."""
import csv
import math
import time
from pathlib import Path
from datetime import datetime
from bisect import bisect_left
from collections import deque
from dataclasses import dataclass, asdict

FIELDS = ('t_s', 'ax_m_s2', 'ay_m_s2', 'az_m_s2', 'gx_deg_s', 'gy_deg_s', 'gz_deg_s', 'pressure_pa')
MAX_ROWS = 100000

class SessionWriter:
    """Append-only capture with immediate flush; unique directory per session."""
    def __init__(self, base):
        import uuid
        self.directory = Path(base) / (datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:8])
        self.directory.mkdir(parents=True)
        self.data = self.events = None
        try:
            self.data = (self.directory/'samples.csv').open('w', newline='', encoding='utf-8-sig')
            self.events = (self.directory/'events.csv').open('w', newline='', encoding='utf-8-sig')
            self.writer = csv.DictWriter(self.data, fieldnames=FIELDS)
            self.writer.writeheader()
            self.event_writer = csv.writer(self.events)
            self.event_writer.writerow(['local_time', 'event'])
            self.event('模拟采集开始')
            self.data.flush()
        except OSError:
            self.close()
            raise

    def append(self, sample):
        self.writer.writerow(asdict(sample))
        self.data.flush()

    def event(self, text):
        self.event_writer.writerow([datetime.now().isoformat(timespec='milliseconds'), text])
        self.events.flush()

    def close(self):
        for f in (self.data, self.events):
            if f is not None: f.close()

@dataclass(frozen=True)
class Sample:
    t_s: float
    ax_m_s2: float
    ay_m_s2: float
    az_m_s2: float
    gx_deg_s: float
    gy_deg_s: float
    gz_deg_s: float
    pressure_pa: float

    @classmethod
    def parse(cls, row):
        values = [float(row[k]) for k in FIELDS]
        if not all(math.isfinite(v) for v in values):
            raise ValueError('数据含 NaN 或无穷值')
        if values[0] < 0 or values[-1] <= 0:
            raise ValueError('时间必须非负，气压必须为正')
        return cls(*values)

def simulated(t):
    # Synthetic bench motion, not a flight or navigation model.
    return Sample(t, .4*math.sin(t), .3*math.cos(t*.7), 9.81+.2*math.sin(t*2),
                  12*math.sin(t*.6), 8*math.cos(t*.4), 5*math.sin(t*.8),
                  101325+30*math.sin(t*.2))

def save_csv(path, rows):
    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(asdict(s) for s in rows)

def load_csv(path):
    rows = []
    with open(path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        if tuple(reader.fieldnames or ()) != FIELDS:
            raise ValueError('CSV 表头不匹配，请使用本程序导出的格式')
        for line, row in enumerate(reader, 2):
            if len(rows) >= MAX_ROWS:
                raise ValueError('文件超过 100000 行限制')
            try:
                sample = Sample.parse(row)
                if rows and sample.t_s <= rows[-1].t_s:
                    raise ValueError('时间必须严格递增')
                rows.append(sample)
            except (ValueError, TypeError, KeyError) as e:
                raise ValueError(f'第 {line} 行：{e}') from e
    if not rows:
        raise ValueError('文件没有数据')
    return rows

class App:
    def __init__(self, root):
        import tkinter as tk
        from tkinter import ttk
        self.root, self.tk = root, tk
        root.title('地面传感器记录器 · v0.2.0')
        root.geometry('1080x760')
        self.mode = 'idle'
        self.rows, self.replay = [], []
        self.window = deque(maxlen=400)
        self.index = 0
        self.last_rx = None
        self.session = None
        self.interrupted = False
        self.save_status = tk.StringVar(value='自动保存：新建采集时选择目录')
        self.started = time.monotonic()
        self.drop = tk.BooleanVar(value=False)
        self.channel = tk.StringVar(value='az_m_s2')
        self.status = tk.StringVar(value='就绪 · 尚未采集')
        self.latest = tk.StringVar(value='暂无数据')
        self.count = tk.StringVar(value='0 条')
        ttk.Label(root, text='地面传感器与数据记录', font=('', 20, 'bold')).pack(anchor='w', padx=20, pady=12)
        ttk.Label(root, text='模拟数据 / 文件回放 · 本版无硬件连接 · 无姿态解算与控制输出').pack(anchor='w', padx=20)
        bar = ttk.Frame(root)
        bar.pack(fill='x', padx=20, pady=12)
        for label, fn in [('新建模拟采集', self.start), ('停止 / 暂停', self.stop), ('继续回放', self.resume), ('保存 CSV', self.export), ('载入 CSV 回放', self.import_file)]:
            ttk.Button(bar, text=label, command=fn).pack(side='left', padx=3)
        ttk.Checkbutton(root, text='模拟数据中断（超过 1 秒提示）', variable=self.drop).pack(anchor='w', padx=20)
        ttk.Label(root, textvariable=self.status, font=('', 13, 'bold')).pack(anchor='w', padx=20, pady=8)
        ttk.Label(root, textvariable=self.count).pack(anchor='w', padx=20)
        ttk.Label(root, textvariable=self.save_status, wraplength=1000).pack(anchor='w', padx=20)
        seekbar = ttk.Frame(root)
        seekbar.pack(fill='x', padx=20)
        ttk.Label(seekbar, text='回放定位 %').pack(side='left')
        self.seek = tk.DoubleVar(value=0)
        ttk.Scale(seekbar, from_=0, to=100, variable=self.seek).pack(side='left', fill='x', expand=True)
        ttk.Button(seekbar, text='跳转并暂停', command=self.seek_replay).pack(side='left')
        ttk.Label(root, textvariable=self.latest, font=('Courier', 11)).pack(anchor='w', padx=20, pady=8)
        select = ttk.Combobox(root, textvariable=self.channel, values=FIELDS[1:], state='readonly')
        select.pack(anchor='w', padx=20)
        select.bind('<<ComboboxSelected>>', lambda e: self.draw())
        self.canvas = tk.Canvas(root, background='#101b2b', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True, padx=20, pady=12)
        self.canvas.bind('<Configure>', lambda e: self.draw())
        ttk.Label(root, text='曲线仅显示最近 400 点，纵轴自动缩放；模拟目标 20 Hz，实际采样时间写入文件。').pack(anchor='w', padx=20, pady=6)
        root.protocol('WM_DELETE_WINDOW', self.close)
        root.after(50, self.tick)

    def confirm_discard(self):
        from tkinter import messagebox
        return not self.rows or messagebox.askyesno('保留记录', '将替换当前记录；需要的数据请先保存。继续？')

    def start(self):
        from tkinter import filedialog, messagebox
        if not self.confirm_discard(): return
        base = filedialog.askdirectory(title='选择自动保存目录（每次采集创建独立子目录）')
        if not base: return
        try: new_session = SessionWriter(base)
        except OSError as e:
            messagebox.showerror('无法创建采集文件', str(e)); return
        self.close_session('被新采集替换')
        self.session = new_session
        self.save_status.set('自动保存：'+str(new_session.directory))
        self.interrupted = False
        self.rows, self.replay = [], []
        self.window.clear()
        self.mode, self.started, self.last_rx = 'sim', time.monotonic(), None
        self.drop.set(False)
        self.draw()

    def stop(self):
        if self.mode == 'replay':
            self.replay_elapsed = time.monotonic()-self.started
            self.mode = 'paused'
        elif self.mode != 'paused':
            self.mode = 'idle'
            self.close_session('用户停止采集')
        self.status.set('已停止 / 已暂停 · 数据保留')

    def close_session(self, reason):
        if self.session:
            try: self.session.event(reason)
            except OSError: self.save_status.set('事件日志写入失败；请检查磁盘')
            finally:
                try: self.session.close()
                except OSError: self.save_status.set('关闭文件失败；请检查磁盘')
                self.session = None

    def seek_replay(self):
        if not self.replay: return
        t0, t1 = self.replay[0].t_s, self.replay[-1].t_s
        target = t0+(t1-t0)*self.seek.get()/100
        self.index = min(bisect_left([s.t_s for s in self.replay], target)+1, len(self.replay))
        self.window.clear()
        self.window.extend(self.replay[max(0,self.index-400):self.index-1])
        self.replay_elapsed = self.replay[self.index-1].t_s-t0
        self.mode = 'paused'
        self.receive(self.replay[self.index-1])
        self.status.set(f'回放已定位并暂停 · {self.index}/{len(self.replay)}')

    def resume(self):
        if self.mode == 'paused':
            self.started = time.monotonic()-self.replay_elapsed
            self.mode = 'replay'

    def export(self):
        from tkinter import filedialog, messagebox
        if not self.rows:
            messagebox.showinfo('保存', '当前没有数据'); return
        path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV', '*.csv')])
        if path:
            try:
                save_csv(path, self.rows)
                messagebox.showinfo('保存', f'已保存 {len(self.rows)} 条记录')
            except OSError as e: messagebox.showerror('保存失败', str(e))

    def import_file(self):
        from tkinter import filedialog, messagebox
        path = filedialog.askopenfilename(filetypes=[('CSV', '*.csv')])
        if not path: return
        try: data = load_csv(path)
        except (OSError, ValueError, csv.Error, UnicodeError) as e:
            messagebox.showerror('读取失败', str(e)); return
        if not self.confirm_discard(): return
        self.close_session('切换到文件回放')
        self.replay, self.rows = data, list(data)
        self.window.clear()
        self.index, self.started, self.mode = 0, time.monotonic(), 'replay'
        self.draw()

    def receive(self, sample):
        self.window.append(sample)
        self.last_rx = time.monotonic()
        self.latest.set(f't={sample.t_s:.2f} s   a=({sample.ax_m_s2:.3f}, {sample.ay_m_s2:.3f}, {sample.az_m_s2:.3f}) m/s²\n'
                        f'ω=({sample.gx_deg_s:.2f}, {sample.gy_deg_s:.2f}, {sample.gz_deg_s:.2f}) °/s   p={sample.pressure_pa:.1f} Pa')
        self.draw()

    def tick(self):
        now = time.monotonic()
        if self.mode == 'sim':
            if not self.drop.get():
                sample = simulated(now-self.started)
                self.rows.append(sample)
                try:
                    if self.interrupted:
                        self.session.event('模拟数据恢复')
                        self.interrupted = False
                    self.session.append(sample)
                except OSError as e:
                    self.mode = 'idle'
                    self.close_session('写入错误停止')
                    self.status.set('自动保存失败，已停止；内存数据仍可手动导出')
                    self.save_status.set(str(e))
                    self.root.after(50, self.tick)
                    return
                self.receive(sample)
                self.status.set('模拟采集中 · 数据正常')
                if len(self.rows) >= MAX_ROWS:
                    self.mode = 'idle'
                    self.close_session('达到记录上限')
                    self.status.set('达到 100000 条上限 · 已停止，请保存')
            elif now-(self.last_rx or self.started) > 1:
                self.status.set('数据中断 · 超过 1 秒未收到样本（模拟）')
                if not self.interrupted:
                    self.interrupted = True
                    try: self.session.event('模拟数据中断超过 1 秒')
                    except OSError:
                        self.mode = 'idle'
                        self.close_session('日志写入失败')
                        self.status.set('日志写入失败，已停止')
        elif self.mode == 'replay':
            elapsed = now-self.started
            # Bounded work per event loop to retain responsiveness.
            for _ in range(500):
                if self.index >= len(self.replay) or self.replay[self.index].t_s-self.replay[0].t_s > elapsed: break
                self.receive(self.replay[self.index])
                self.index += 1
            self.status.set(f'文件回放 · {self.index}/{len(self.replay)}')
            if self.index == len(self.replay):
                self.mode = 'idle'
                self.status.set('文件回放完成')
        self.count.set(f'记录 {len(self.rows)} 条 · 当前来源：'+('模拟' if not self.replay else 'CSV 文件'))
        self.root.after(50, self.tick)

    def draw(self):
        c = self.canvas
        c.delete('all')
        w, h = max(c.winfo_width(), 200), max(c.winfo_height(), 150)
        key = self.channel.get()
        c.create_text(12, 14, text=key, anchor='w', fill='#bcd2ec')
        if not self.window: return
        points = list(self.window)
        lo = min(getattr(s, key) for s in points)
        hi = max(getattr(s, key) for s in points)
        pad = max((hi-lo)*.1, .01)
        lo, hi = lo-pad, hi+pad
        t0, t1 = points[0].t_s, points[-1].t_s
        for j in range(5):
            y = 35+(h-65)*j/4
            c.create_line(85, y, w-15, y, fill='#29374b')
            c.create_text(78, y, text=f'{hi-(hi-lo)*j/4:.2f}', anchor='e', fill='#a6bad1')
        xy = []
        for s in points:
            xy.extend((85+(w-100)*(s.t_s-t0)/max(t1-t0,.05), 35+(h-65)*(hi-getattr(s,key))/(hi-lo)))
        if len(xy) >= 4: c.create_line(*xy, fill='#52d5bf', width=2)
        c.create_text(85,h-13,text=f'{t0:.2f} s',anchor='w',fill='#a6bad1')
        c.create_text(w-15,h-13,text=f'{t1:.2f} s',anchor='e',fill='#a6bad1')

    def close(self):
        from tkinter import messagebox
        if self.rows and not messagebox.askyesno('退出', '需要的数据请先保存。确定退出？'): return
        self.close_session('窗口关闭')
        self.root.destroy()

if __name__ == '__main__':
    import tkinter as tk
    App(tk.Tk())
    tk.mainloop()
