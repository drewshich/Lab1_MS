from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

from .examples import EXAMPLE_BUILDERS
from .io_json import save_game_to_file, save_solution_to_file
from .models import Game
from .renderer_graph import render_game_to_file
from .solver import BackwardInductionResult
from .workflows import (
    RandomGameConfig,
    SolveWorkflowError,
    build_solution_report,
    solve_example_game,
    solve_game_from_path,
    solve_random_game,
)


class DynamicGamesApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title('Dynamic Games Lab')
        self.root.geometry('1220x760')
        self.root.minsize(1020, 680)

        self.source_mode = tk.StringVar(value='example')
        self.example_name = tk.StringVar(value=sorted(EXAMPLE_BUILDERS)[0])
        self.file_path = tk.StringVar(value=str(Path('examples_json') / 'centipede.json'))
        self.random_players = tk.StringVar(value='3')
        self.random_depth = tk.StringVar(value='4')
        self.random_branching = tk.StringVar(value='2')
        self.random_seed = tk.StringVar(value='42')
        self.random_title = tk.StringVar(value='Random dynamic game')
        self.epsilon = tk.StringVar(value='0.0')
        self.show_tree = tk.BooleanVar(value=True)
        self.show_steps = tk.BooleanVar(value=True)
        self.status = tk.StringVar(value='Выберите источник игры и нажмите "Решить".')

        self.current_game: Game | None = None
        self.current_result: BackwardInductionResult | None = None
        self.current_report: str = ''

        self.example_combo: ttk.Combobox | None = None
        self.file_entry: ttk.Entry | None = None
        self.file_browse_button: ttk.Button | None = None
        self.random_entries: list[ttk.Entry] = []
        self.random_labels: list[ttk.Label] = []
        self.export_button: ttk.Button | None = None
        self.report_button: ttk.Button | None = None
        self.solution_button: ttk.Button | None = None
        self.graph_button: ttk.Button | None = None
        self.output: scrolledtext.ScrolledText | None = None

        self._build_layout()
        self._update_source_state()
        self._set_result_actions_enabled(False)

    def _build_layout(self) -> None:
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        controls = ttk.Frame(self.root, padding=12)
        controls.grid(row=0, column=0, sticky='nsw')
        controls.columnconfigure(0, weight=1)

        output_panel = ttk.Frame(self.root, padding=(0, 12, 12, 12))
        output_panel.grid(row=0, column=1, sticky='nsew')
        output_panel.columnconfigure(0, weight=1)
        output_panel.rowconfigure(1, weight=1)

        source_frame = ttk.LabelFrame(controls, text='Источник игры', padding=10)
        source_frame.grid(row=0, column=0, sticky='ew')
        source_frame.columnconfigure(1, weight=1)

        ttk.Radiobutton(
            source_frame,
            text='Встроенный пример',
            value='example',
            variable=self.source_mode,
            command=self._update_source_state,
        ).grid(row=0, column=0, sticky='w', columnspan=2)
        ttk.Label(source_frame, text='Пример:').grid(row=1, column=0, sticky='w', pady=(6, 0))
        self.example_combo = ttk.Combobox(
            source_frame,
            textvariable=self.example_name,
            values=sorted(EXAMPLE_BUILDERS),
            state='readonly',
        )
        self.example_combo.grid(row=1, column=1, sticky='ew', pady=(6, 0))

        ttk.Radiobutton(
            source_frame,
            text='JSON-файл',
            value='file',
            variable=self.source_mode,
            command=self._update_source_state,
        ).grid(row=2, column=0, sticky='w', columnspan=2, pady=(10, 0))
        ttk.Label(source_frame, text='Файл:').grid(row=3, column=0, sticky='w', pady=(6, 0))
        file_row = ttk.Frame(source_frame)
        file_row.grid(row=3, column=1, sticky='ew', pady=(6, 0))
        file_row.columnconfigure(0, weight=1)
        self.file_entry = ttk.Entry(file_row, textvariable=self.file_path)
        self.file_entry.grid(row=0, column=0, sticky='ew')
        self.file_browse_button = ttk.Button(file_row, text='Обзор...', command=self._browse_json_file)
        self.file_browse_button.grid(row=0, column=1, padx=(6, 0))

        ttk.Radiobutton(
            source_frame,
            text='Случайная игра',
            value='random',
            variable=self.source_mode,
            command=self._update_source_state,
        ).grid(row=4, column=0, sticky='w', columnspan=2, pady=(10, 0))

        random_fields = [
            ('Игроков:', self.random_players),
            ('Глубина:', self.random_depth),
            ('Ветвление:', self.random_branching),
            ('Seed:', self.random_seed),
            ('Название:', self.random_title),
        ]
        for offset, (label_text, variable) in enumerate(random_fields, start=5):
            label = ttk.Label(source_frame, text=label_text)
            label.grid(row=offset, column=0, sticky='w', pady=(6, 0))
            entry = ttk.Entry(source_frame, textvariable=variable)
            entry.grid(row=offset, column=1, sticky='ew', pady=(6, 0))
            self.random_labels.append(label)
            self.random_entries.append(entry)

        options_frame = ttk.LabelFrame(controls, text='Параметры вывода', padding=10)
        options_frame.grid(row=1, column=0, sticky='ew', pady=(12, 0))
        options_frame.columnconfigure(1, weight=1)

        ttk.Label(options_frame, text='Epsilon:').grid(row=0, column=0, sticky='w')
        ttk.Entry(options_frame, textvariable=self.epsilon).grid(row=0, column=1, sticky='ew')
        ttk.Checkbutton(options_frame, text='Показывать дерево игры', variable=self.show_tree).grid(
            row=1, column=0, columnspan=2, sticky='w', pady=(8, 0)
        )
        ttk.Checkbutton(options_frame, text='Показывать шаги алгоритма', variable=self.show_steps).grid(
            row=2, column=0, columnspan=2, sticky='w', pady=(4, 0)
        )

        actions_frame = ttk.LabelFrame(controls, text='Действия', padding=10)
        actions_frame.grid(row=2, column=0, sticky='ew', pady=(12, 0))
        actions_frame.columnconfigure(0, weight=1)

        ttk.Button(actions_frame, text='Решить', command=self._solve_selected_game).grid(row=0, column=0, sticky='ew')
        self.export_button = ttk.Button(actions_frame, text='Сохранить игру в JSON', command=self._save_game_json)
        self.export_button.grid(row=1, column=0, sticky='ew', pady=(8, 0))
        self.report_button = ttk.Button(actions_frame, text='Сохранить текстовый отчёт', command=self._save_report)
        self.report_button.grid(row=2, column=0, sticky='ew', pady=(8, 0))
        self.solution_button = ttk.Button(
            actions_frame, text='Сохранить решение в JSON', command=self._save_solution_json
        )
        self.solution_button.grid(row=3, column=0, sticky='ew', pady=(8, 0))
        self.graph_button = ttk.Button(actions_frame, text='Сохранить граф/решение', command=self._save_graph)
        self.graph_button.grid(row=4, column=0, sticky='ew', pady=(8, 0))

        tk.Label(output_panel, text='Результат', font=('Segoe UI', 12, 'bold')).grid(row=0, column=0, sticky='w')
        self.output = scrolledtext.ScrolledText(output_panel, wrap='word', font=('Consolas', 10))
        self.output.grid(row=1, column=0, sticky='nsew', pady=(8, 0))
        self.output.insert('1.0', 'Здесь появится отчёт по игре.\n')
        self.output.configure(state='disabled')

        tk.Label(output_panel, textvariable=self.status, anchor='w', fg='#1f3a5f').grid(
            row=2, column=0, sticky='ew', pady=(8, 0)
        )

    def _update_source_state(self) -> None:
        mode = self.source_mode.get()
        if self.example_combo is not None:
            self.example_combo.configure(state='readonly' if mode == 'example' else 'disabled')
        if self.file_entry is not None:
            self.file_entry.configure(state='normal' if mode == 'file' else 'disabled')
        if self.file_browse_button is not None:
            self.file_browse_button.configure(state='normal' if mode == 'file' else 'disabled')

        random_state = 'normal' if mode == 'random' else 'disabled'
        for entry in self.random_entries:
            entry.configure(state=random_state)

    def _set_result_actions_enabled(self, enabled: bool) -> None:
        state = 'normal' if enabled else 'disabled'
        for button in [self.export_button, self.report_button, self.solution_button, self.graph_button]:
            if button is not None:
                button.configure(state=state)

    def _browse_json_file(self) -> None:
        path = filedialog.askopenfilename(
            title='Выберите JSON-файл игры',
            filetypes=[('JSON files', '*.json'), ('All files', '*.*')],
        )
        if path:
            self.file_path.set(path)

    def _parse_epsilon(self) -> float:
        raw_value = self.epsilon.get().strip() or '0.0'
        try:
            return float(raw_value)
        except ValueError as exc:
            raise ValueError('Epsilon должен быть числом.') from exc

    def _random_config_from_form(self) -> RandomGameConfig:
        seed_text = self.random_seed.get().strip()
        seed = None if not seed_text else int(seed_text)
        title = self.random_title.get().strip() or 'Random dynamic game'
        return RandomGameConfig(
            players=int(self.random_players.get().strip()),
            depth=int(self.random_depth.get().strip()),
            branching=int(self.random_branching.get().strip()),
            seed=seed,
            title=title,
        )

    def _solve_selected_game(self) -> None:
        try:
            epsilon = self._parse_epsilon()
            mode = self.source_mode.get()
            if mode == 'example':
                solved = solve_example_game(self.example_name.get(), epsilon=epsilon)
            elif mode == 'file':
                input_path = self.file_path.get().strip()
                if not input_path:
                    raise ValueError('Выберите JSON-файл игры.')
                solved = solve_game_from_path(input_path, epsilon=epsilon)
            else:
                solved = solve_random_game(self._random_config_from_form(), epsilon=epsilon)
        except ValueError as exc:
            self._set_status(str(exc))
            messagebox.showerror('Ошибка параметров', str(exc), parent=self.root)
            return
        except SolveWorkflowError as exc:
            self._set_status(str(exc))
            messagebox.showerror('Ошибка решения', str(exc), parent=self.root)
            return

        self.current_game = solved.game
        self.current_result = solved.result
        self.current_report = build_solution_report(
            solved.game,
            solved.result,
            include_tree=self.show_tree.get(),
            include_steps=self.show_steps.get(),
        )
        self._update_output(self.current_report)
        self._set_result_actions_enabled(True)
        self._set_status(f'Игра "{solved.game.title}" успешно решена.')

    def _update_output(self, text: str) -> None:
        if self.output is None:
            return
        self.output.configure(state='normal')
        self.output.delete('1.0', tk.END)
        self.output.insert('1.0', text)
        self.output.configure(state='disabled')

    def _save_game_json(self) -> None:
        if self.current_game is None:
            return
        path = filedialog.asksaveasfilename(
            title='Сохранить игру в JSON',
            defaultextension='.json',
            filetypes=[('JSON files', '*.json'), ('All files', '*.*')],
            initialfile='game.json',
        )
        if not path:
            return
        save_game_to_file(self.current_game, path)
        self._set_status(f'Игра сохранена: {path}')

    def _save_report(self) -> None:
        if not self.current_report:
            return
        path = filedialog.asksaveasfilename(
            title='Сохранить текстовый отчёт',
            defaultextension='.txt',
            filetypes=[('Text files', '*.txt'), ('All files', '*.*')],
            initialfile='report.txt',
        )
        if not path:
            return
        Path(path).write_text(self.current_report, encoding='utf-8')
        self._set_status(f'Отчёт сохранён: {path}')

    def _save_solution_json(self) -> None:
        if self.current_result is None:
            return
        path = filedialog.asksaveasfilename(
            title='Сохранить решение в JSON',
            defaultextension='.json',
            filetypes=[('JSON files', '*.json'), ('All files', '*.*')],
            initialfile='solution.json',
        )
        if not path:
            return
        save_solution_to_file(self.current_result, path)
        self._set_status(f'Решение сохранено: {path}')

    def _save_graph(self) -> None:
        if self.current_game is None or self.current_result is None:
            return
        path = filedialog.asksaveasfilename(
            title='Сохранить изображение графа',
            defaultextension='.png',
            filetypes=[('PNG files', '*.png'), ('DOT files', '*.dot'), ('All files', '*.*')],
            initialfile='game_solution.png',
        )
        if not path:
            return
        output_path = render_game_to_file(self.current_game, path, self.current_result.first_optimal_path)
        self._set_status(f'Граф сохранён: {output_path}')
        messagebox.showinfo('Готово', f'Файл сохранён:\n{output_path}', parent=self.root)

    def _set_status(self, message: str) -> None:
        self.status.set(message)


def run_gui() -> None:
    root = tk.Tk()
    style = ttk.Style(root)
    if 'clam' in style.theme_names():
        style.theme_use('clam')
    DynamicGamesApp(root)
    root.mainloop()
