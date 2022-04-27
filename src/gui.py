import tkinter as tk
import tkinter.font as fnt
from tkinter import ttk, filedialog, messagebox, Menu
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image, ImageTk
import cv2
import os
import threading
import sys
import numpy as np
import time
import skimage
import math     # do not touch - needed for parameters values
from src.validation import Validation
from src.helpers import ParamType, get_traceback_data, format_errors


class App(TkinterDnD.Tk):

    class CustomButton(tk.Button):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.configure(bg='white', fg='black')

    def __init__(self):
        super().__init__()

        self.title('Image processing by Paweł Pytlowski')
        self.state('zoomed')

        self.validation = Validation()
        algorithms, error_type, config_errors = self.validation.get_algorithms('../config.yaml')

        if config_errors:
            if algorithms is not None and len(algorithms) > 0:

                response = messagebox.askyesno('Config error', format_errors(f'{str(error_type)} errors occurred:\n', config_errors) +
                                               f'\n\nDo you wish to continue with validated algorithms only? ({len(algorithms)})')
                if not response:
                    exit()
            else:
                messagebox.showerror('Config error', format_errors(f'{str(error_type)} errors occurred:\n', config_errors) +
                                     '\n\nNo validated algorithms found.')
                exit()

        if algorithms is None or len(algorithms) == 0:
            messagebox.showerror('Config error', 'No valid algorithms found in config file.')
            self.destroy()
            exit()
        else:
            self.ALGORITHMS = algorithms

            # region basic config
            self.processing_image_thread = None

            self.IMG_SIZE = self.winfo_screenheight() / 2
            self.IMG_EXTENSIONS = ('.png', '.jpg')
            self.GIF_SIZE = 100
            self.PARAM_NAME_MAX_LENGTH = 20

            self.BG_COLOR = '#bfbcb4'
            self.DARK_COLOR = 'black'

            self.configure(background=self.BG_COLOR)
            # endregion

            #region loading animation variables
            self.gif_frames = []
            self.gif_frames_count = 0
            self.loading_indicator_animation_obj = None
            self.init_loading_indicator('assets/loading-indicator.gif')
            self.current_gif_frame = None
            #endregion

            self.data = {
                'image_before': None,
                'image_after': None,
                'parameters': []
            }

            self.input_image_displayed = None
            self.output_image_displayed = None

            self.input_canvas_image = None
            self.output_canvas_image = None
            self.output_canvas_button = None

            self.rowconfigure(0, weight=1)
            self.columnconfigure(0, weight=1)
            self.rowconfigure(2, weight=1)
            self.columnconfigure(2, weight=1)

            self.main_frame = tk.Frame(self, bg=self.BG_COLOR)
            self.main_frame.grid(row=1, column=1, padx=20, pady=20)

            self.buttons_frame = tk.Frame(self.main_frame, bg=self.BG_COLOR)

            # buttons
            self.my_font = fnt.Font(size=13)
            self.my_font_bigger = fnt.Font(size=16)

            self.select_image_btn = self.CustomButton(self.buttons_frame, text='Load image', font=self.my_font,
                                                      width=28, command=self.open_file_dialog)
            self.select_image_btn.pack(side=tk.LEFT, padx=10)

            self.select_parameters_btn = self.CustomButton(self.buttons_frame, text='Select parameters', font=self.my_font,
                                                   width=20, command=self.open_select_parameters_window)

            self.selected_algorithm_var = tk.StringVar()
            self.selected_algorithm_var.trace('w', lambda x, y, z: self.on_combobox_change())

            self.select_algorithm_combobox = ttk.Combobox(self.buttons_frame, width=20, font=self.my_font_bigger,
                                                     state="readonly", textvar=self.selected_algorithm_var)
            self.select_algorithm_combobox['values'] = [a['name'] for a in self.ALGORITHMS]
            self.option_add("*TCombobox*Font", self.my_font)

            self.selected_algorithm_var.set(self.select_algorithm_combobox['values'][0])
            self.select_algorithm_combobox.bind("<<ComboboxSelected>>", lambda e: self.focus())

            self.select_algorithm_combobox.pack(side=tk.LEFT, padx=10)
            self.select_parameters_btn.pack(side=tk.LEFT, padx=10)

            self.clear_btn = self.CustomButton(self.buttons_frame, text='✖', font=self.my_font, width=5, command=self.clear_data)
            self.clear_btn.pack(side=tk.LEFT, padx=10)

            # images
            self.images_frame = tk.Frame(self.main_frame, bg=self.BG_COLOR)
            # self.images_frame = tk.Frame(self.main_frame, bg='red')

            self.input_canvas = tk.Canvas(self.images_frame, width=self.IMG_SIZE, height=self.IMG_SIZE,
                                          highlightthickness=1, bg='white', highlightbackground=self.DARK_COLOR)
            self.output_canvas = tk.Canvas(self.images_frame, width=self.IMG_SIZE, height=self.IMG_SIZE,
                                           highlightthickness=1, bg='white', highlightbackground=self.DARK_COLOR)

            self.input_canvas.drop_target_register(DND_FILES)
            self.input_canvas.dnd_bind('<<Drop>>', self.on_file_drop)

            self.input_canvas.bind("<Button-3>", lambda e: self.open_context_menu(e, self.input_canvas))
            self.output_canvas.bind("<Button-3>", lambda e: self.open_context_menu(e, self.output_canvas))

            self.output_canvas.bind("<Enter>", lambda x: self.show_save_output_button())
            self.output_canvas.bind("<Leave>", lambda x: self.hide_save_output_button())

            self.algorithm_btn = self.CustomButton(self.images_frame, text='➡', font=fnt.Font(size=32), width=4,
                                           command=self.on_start_processing_image)

            self.input_canvas.pack(side=tk.LEFT)
            self.algorithm_btn.pack(side=tk.LEFT, padx=10)
            self.output_canvas.pack(side=tk.LEFT)

            self.buttons_frame.pack()
            tk.Frame(self.main_frame, height=20, bg=self.BG_COLOR).pack()
            self.images_frame.pack()

            self.icon = tk.PhotoImage(file='assets/save_icon24.png')
            self.save_output_btn = self.CustomButton(self.output_canvas, image=self.icon, height=36, width=36,
                                                     command=self.open_save_dialog)
            self.output_canvas_button = self.output_canvas.create_window(self.IMG_SIZE-10, self.IMG_SIZE-10, anchor=tk.SE,
                                                                         window=self.save_output_btn)
            self.output_canvas.itemconfigure(self.output_canvas_button, state=tk.HIDDEN)

            self.parameters_window = None
            self.parameter_variables = []

    def open_context_menu(self, event, canvas):
        if canvas == self.input_canvas:
            image = self.data['image_before']
        else:
            image = self.data['image_after']

        if image is not None:
            m = Menu(canvas, tearoff=0)
            m.add_command(label="Open in external program", command=lambda: self.open_in_external_program(image))

            try:
                m.tk_popup(event.x_root, event.y_root)
            finally:
                m.grab_release()

    def on_combobox_change(self):
        self.init_params_by_algorithm()
        if len(self.data['parameters']) > 0:
            self.select_parameters_btn['state'] = tk.NORMAL
        else:
            self.select_parameters_btn['state'] = tk.DISABLED

    def init_params_by_algorithm(self):
        selected_alg = self.get_selected_algorithm_object()
        param_strings = [param.get('default', None) for param in selected_alg['params']]
        self.data['parameters'] = ['1' if p == 'True' else '0' if p == 'False' else p for p in param_strings]

    def load_image_from_path(self, path):
        img = cv2.imread(path)

        if img is not None:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            self.data['image_before'] = img
            img_output = self.get_displayable_image(self.data['image_before'])
            self.input_img = ImageTk.PhotoImage(image=Image.fromarray(img_output))
            self.input_canvas_image = self.input_canvas.create_image(self.IMG_SIZE / 2, self.IMG_SIZE / 2,
                                                                     anchor=tk.CENTER, image=self.input_img)
            self.clear_output_canvas()
        else:
            messagebox.showerror('Error', 'An error occurred while selecting image.')

    def open_file_dialog(self):
        path = filedialog.askopenfilename(initialdir=os.getcwd() + '/input_images',
                                          filetypes=[('Images', self.IMG_EXTENSIONS)])
        if path:
            self.load_image_from_path(path)

    def open_save_dialog(self):
        if self.output_image_displayed:
            path = filedialog.asksaveasfilename(initialdir=os.getcwd() + '/output_images',
                                                defaultextension="*.*",
                                                filetypes=[('JPG (*.jpg)', '.jpg'), ('PNG (*.png)', '.png')])
            if path:
                image_to_save = self.data['image_after']
                if len(image_to_save.shape) == 3:
                    image_to_save = cv2.cvtColor(image_to_save, cv2.COLOR_RGB2BGR)

                cv2.imwrite(path, image_to_save)

    def on_file_drop(self, event):
        path = event.data
        if ' ' in path:
            messagebox.showwarning('Warning', 'You can only drag a single image file.')
            return

        if '.' + path.split('.')[-1] in self.IMG_EXTENSIONS:
            self.load_image_from_path(path)
        else:
            messagebox.showerror('Error', 'This file type is not supported.')

    def get_displayable_image(self, image):
        max_dim = max(*(image.shape[:2]))
        diff = self.IMG_SIZE / max_dim

        if diff < 1:
            return cv2.resize(image, (0, 0), fx=diff, fy=diff)
        return image

    def on_start_processing_image(self):
        if self.data.get('image_before', None) is None:
            messagebox.showerror('Error', 'No image selected.')
            return

        self.algorithm_btn['state'] = tk.DISABLED
        self.output_canvas.delete(self.output_canvas_image)
        self.output_canvas.itemconfigure(self.output_canvas_button, state=tk.HIDDEN)
        # self.processing_image_thread = threading.Thread(target=self.run_process_image)

        self.loading_animation(0)
        self.processing_image_thread = KillableThread(target=self.run_process_image, daemon=True)
        self.processing_image_thread.start()
        self.after(20, self.check_processing_thread)

    def run_process_image(self):
        # self.loading_animation(0)

        selected = self.get_selected_algorithm_object()
        param_types = [p['type'] for p in selected['params']]
        parameters = [self.evaluate_string_parameter(type, param) for type, param in zip(param_types, self.data['parameters'])]

        for i, p in enumerate(parameters):
            if p is None:
                self.stop_loading_animation()
                messagebox.showerror('Error', f"Parameter #{i+1} ({selected['params'][i]['name']}) is null.")
                self.algorithm_btn['state'] = tk.NORMAL
                return

        process_result = None
        try:
            process_result = selected['method'](self.data['image_before'], *parameters)
        except Exception as e:
            self.stop_loading_animation()
            self.data['image_after'] = None
            time.sleep(0.1)
            messagebox.showerror('Error', f"Error while processing input image with algorithm '{selected['name']}':\n"
                                          f"{get_traceback_data(e, ignore_file=sys.argv[0])}")
            self.algorithm_btn['state'] = tk.NORMAL
            self.processing_image_thread.kill()

        error = self.validation.validate_image(process_result)

        if error is None:
            img_output = self.get_displayable_image(process_result)
            self.data['image_after'] = process_result
            self.render_right_image(img_output)
        else:
            messagebox.showerror('Error', error)

        self.algorithm_btn['state'] = tk.NORMAL

    def check_processing_thread(self):
        if self.processing_image_thread.is_alive():
            self.after(20, self.check_processing_thread)
        else:
            self.stop_loading_animation()

    def open_select_parameters_window(self):
        self.select_parameters_btn['state'] = tk.DISABLED
        self.select_algorithm_combobox['state'] = tk.DISABLED

        self.parameters_window = tk.Toplevel(self)
        self.parameters_window.protocol("WM_DELETE_WINDOW", lambda: self.on_parameters_window_close())

        self.parameters_window.title("Select algorithm parameters")
        self.parameters_window.geometry("800x400")
        self.parameters_window.configure(bg=self.BG_COLOR)

        self.parameters_window.rowconfigure(0, weight=1)
        self.parameters_window.columnconfigure(0, weight=1)
        self.parameters_window.rowconfigure(2, weight=1)
        self.parameters_window.columnconfigure(2, weight=1)

        self.parameter_variables = []

        parameters_window_main_frame = tk.Frame(self.parameters_window, bg=self.BG_COLOR)
        parameters_window_main_frame.grid(row=1, column=1)

        parameters_frame = tk.Frame(parameters_window_main_frame, bg=self.BG_COLOR)
        parameters_frame.pack(pady=10)

        for i, param in enumerate(self.get_selected_algorithm_object()['params']):
            param_name = param['name'] if len(param['name']) <= self.PARAM_NAME_MAX_LENGTH \
                    else param['name'][:self.PARAM_NAME_MAX_LENGTH-3] + '...'
            label = tk.Label(parameters_frame, text=param_name, font=self.my_font, bg=self.BG_COLOR)
            label.grid(row=i, column=0, padx=10, sticky=tk.W)

            if param.get('description', None):
                self.CustomToolTip(label, text=param['name'] + ':\n' + param['description'])

            curr_value = self.data['parameters'][i]

            if param.get('type', None) == ParamType.BOOL:
                var = tk.IntVar()
                if curr_value is not None:
                    var.set(int(curr_value))
                checkbox = tk.Checkbutton(parameters_frame, variable=var, bg=self.BG_COLOR)
                checkbox.grid(row=i, column=1, padx=10, pady=10, sticky=tk.W)
                self.parameter_variables.append(var)
            else:
                var = tk.StringVar()
                if curr_value is not None:
                    var.set(curr_value)
                entry = tk.Entry(parameters_frame, textvariable=var, width=50)
                entry.grid(row=i, column=1, padx=10, pady=10, sticky=tk.W)
                self.parameter_variables.append(var)

        self.CustomButton(parameters_window_main_frame, text='Save', font=self.my_font_bigger, width=10,
                          command=self.validate_and_set_parameters).pack(pady=10)

    def on_parameters_window_close(self):
        if self.parameters_window:
            self.select_parameters_btn['state'] = tk.NORMAL
            self.select_algorithm_combobox['state'] = "readonly"
            self.parameters_window.destroy()

    def get_selected_algorithm_object(self):
        selected_algorithm = self.select_algorithm_combobox.get()
        return list(filter(lambda a: a['name'] == selected_algorithm, self.ALGORITHMS))[0]

    def validate_and_set_parameters(self):
        param_values = []
        for i, (variable, param) in enumerate(zip(self.parameter_variables, self.get_selected_algorithm_object()['params'])):
            try:
                param_type = param['type']
                variable_value = str(variable.get())
                self.evaluate_string_parameter(param_type, variable_value)
                param_values.append(variable_value)
            except Exception as e:
                messagebox.showerror('Evaluation error', f"'Parameter #{i+1} ({param['name']}): {e}", parent=self.parameters_window)
                return

        self.data['parameters'] = param_values
        self.parameter_variables = []
        self.on_parameters_window_close()

    def evaluate_string_parameter(self, param_type: ParamType, value: str):
        if value is None:
            return None
        return {
            ParamType.INT: int,
            ParamType.FLOAT: float,
            ParamType.BOOL: bool,
            ParamType.NPARRAY: np.asarray,
        }.get(param_type, int)(eval(value))

    def clear_data(self):
        self.clear_input_canvas()
        self.clear_output_canvas()

        self.stop_loading_animation()
        self.init_params_by_algorithm()

        self.on_parameters_window_close()

        self.algorithm_btn['state'] = tk.NORMAL
        # self.selected_algorithm_var.set(self.select_algorithm_combobox['values'][0])

        if self.processing_image_thread:
            self.processing_image_thread.kill()

    def show_save_output_button(self):
        if self.data['image_after'] is not None:
            self.output_canvas.itemconfigure(self.output_canvas_button, state=tk.NORMAL)

    def hide_save_output_button(self):
        if self.data['image_after'] is not None:
            self.output_canvas.itemconfigure(self.output_canvas_button, state=tk.HIDDEN)

    def render_right_image(self, image):
        self.output_image_displayed = ImageTk.PhotoImage(image=Image.fromarray(image))
        self.output_canvas_image = self.output_canvas.create_image(self.IMG_SIZE / 2, self.IMG_SIZE / 2,
                                                                   anchor=tk.CENTER, image=self.output_image_displayed)

    def clear_input_canvas(self):
        self.input_canvas.delete(self.input_canvas_image)
        self.input_canvas_image = None
        self.input_image_displayed = None
        self.data['image_before'] = None

    def clear_output_canvas(self):
        self.output_canvas.delete(self.output_canvas_image)
        self.output_canvas_image = None
        self.output_image_displayed = None
        self.output_canvas.itemconfigure(self.output_canvas_button, state=tk.HIDDEN)
        self.output_canvas.delete(self.current_gif_frame)
        self.current_gif_frame = None
        self.data['image_after'] = None

    def init_loading_indicator(self, file):
        gif = Image.open(file)
        frames = gif.n_frames
        self.gif_frames = [tk.PhotoImage(file=file, format=f"gif -index {i}") for i in range(frames)]
        self.gif_frames_count = gif.n_frames

    def loading_animation(self, i):
        gif_frame = self.gif_frames[i]

        self.output_canvas.delete(self.current_gif_frame)
        self.current_gif_frame = self.output_canvas.create_image(self.IMG_SIZE / 2, self.IMG_SIZE / 2,
                                                                 anchor=tk.CENTER, image=gif_frame)
        i += 1
        if i == self.gif_frames_count:
            i = 0
        self.loading_indicator_animation_obj = self.after(20, lambda: self.loading_animation(i))

    def stop_loading_animation(self):
        if self.loading_indicator_animation_obj:
            self.after_cancel(self.loading_indicator_animation_obj)
            self.output_canvas.delete(self.current_gif_frame)
            self.current_gif_frame = None

    def open_in_external_program(self, image):
        if image is not None:
            to_be_shown = Image.fromarray(image)
            to_be_shown.show()

    def CustomToolTip(self, widget, text):
        toolTip = ToolTip(widget)

        def enter(event):
            toolTip.showtip(text)

        def leave(event):
            toolTip.hidetip()

        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)


class ToolTip(object):
    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

    def showtip(self, text):
        "Display text in tooltip window"
        self.text = text
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x  + self.widget.winfo_pointerx()
        y = y + cy + self.widget.winfo_rooty() + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                      background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                      font=(None, 10))
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()


class KillableThread(threading.Thread):
    """A subclass of threading.Thread, with a kill() method."""
    def __init__(self, *args, **keywords):
        threading.Thread.__init__(self, *args, **keywords)
        self.killed = False

    def start(self):
        """Start the thread."""
        self.__run_backup = self.run
        self.run = self.__run      # Force the Thread to install our trace.
        threading.Thread.start(self)

    def __run(self):
        """Hacked run function, which installs the trace."""
        sys.settrace(self.globaltrace)
        self.__run_backup()
        self.run = self.__run_backup

    def globaltrace(self, frame, why, arg):
        if why == 'call':
            return self.localtrace
        else:
            return None

    def localtrace(self, frame, why, arg):
        if self.killed:
            if why == 'line':
                raise SystemExit()
            return self.localtrace

    def kill(self):
        self.killed = True


if __name__ == "__main__":
    app = App()
    app.mainloop()
