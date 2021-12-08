import tkinter as tk
import tkinter.font as fnt
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image, ImageTk
import cv2
import os
import algorithms
import threading


class ParamTypes:
    INT = 0
    FLOAT = 1
    BOOL = 2


class App(TkinterDnD.Tk):

    class CustomButton(tk.Button):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.configure(bg='white', fg='black')

    def __init__(self):
        super().__init__()

        self.title('Improving image quality')
        self.state('zoomed')

        self.processing_image_thread = None

        self.IMG_SIZE = self.winfo_screenheight() / 2
        self.IMG_EXTENSIONS = ('.png', '.jpg')
        self.GIF_SIZE = 100

        self.BG_COLOR = '#FFF8E5'
        self.DARK_COLOR = 'black'

        self.configure(background=self.BG_COLOR)

        self.ALGORITHMS = [
            {
                'name': 'Algo 1',
                'params': [
                    {
                        'name': 'Parameter int',
                        'description': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.',
                        'type': ParamTypes.INT,
                        'default_value': 1234
                    }, {
                        'name': 'Parameter float',
                        'description': 'This parameter is shit',
                        'type': ParamTypes.FLOAT,
                        'default_value': 789.123
                    }, {
                        'name': 'Parameter bool',
                        'type': ParamTypes.BOOL,
                        'default_value': True
                    }
                ]
            }, {
                'name': 'Algo 2',
                'params': [
                    {
                        'name': 'Parameter int',
                        'type': ParamTypes.INT,
                        'default_value': 1
                    }, {
                        'name': 'Parameter int2',
                        'type': ParamTypes.INT,
                        'default_value': 2
                    }, {
                        'name': 'Parameter int3',
                        'type': ParamTypes.INT,
                        'default_value': 3
                    },
                ]
            }

        ]

        self.gif_frames = []
        self.gif_frames_count = 0
        self.loading_indicator_animation_obj = None
        self.init_loading_indicator('assets/loading-indicator.gif')
        self.current_gif_frame = None

        self.image_data = {
            'image_before': None,
            'image_after': None,
            'algorithm': tk.StringVar(self),
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

        # self.select_algorithm_btn = tk.Button(self.buttons_frame, text='Pick algorithm', font=self.my_font, width=20)
        # self.select_algorithm_btn['command'] = self.pick_algorithm
        # self.select_algorithm_btn.pack(side=tk.LEFT, padx=10)

        self.select_algorithm_combobox = ttk.Combobox(self.buttons_frame, width=20, font=self.my_font_bigger,
                                                      textvariable=self.image_data['algorithm'], state="readonly")
        self.select_algorithm_combobox['values'] = [a['name'] for a in self.ALGORITHMS]
        self.option_add("*TCombobox*Font", self.my_font)
        self.select_algorithm_combobox.current(0)
        self.select_algorithm_combobox.bind("<<ComboboxSelected>>", lambda e: self.focus())
        self.select_algorithm_combobox.pack(side=tk.LEFT, padx=10)

        self.select_parameters_btn = self.CustomButton(self.buttons_frame, text='Select parameters', font=self.my_font,
                                               width=20, command=self.select_parameters)
        self.select_parameters_btn.pack(side=tk.LEFT, padx=10)

        self.clear_btn = self.CustomButton(self.buttons_frame, text='✖', font=self.my_font, width=5, command=self.clear_data)
        self.clear_btn.pack(side=tk.LEFT, padx=10)

        # images
        self.images_frame = tk.Frame(self.main_frame, bg=self.BG_COLOR)

        self.input_canvas = tk.Canvas(self.images_frame, width=self.IMG_SIZE, height=self.IMG_SIZE,
                                      highlightthickness=1, bg='white', highlightbackground=self.DARK_COLOR)
        self.output_canvas = tk.Canvas(self.images_frame, width=self.IMG_SIZE, height=self.IMG_SIZE,
                                       highlightthickness=1, bg='white', highlightbackground=self.DARK_COLOR)

        self.input_canvas.drop_target_register(DND_FILES)
        self.input_canvas.dnd_bind('<<Drop>>', self.on_file_drop)
        self.input_canvas.bind("<Double-Button-1>",
                               lambda x: self.open_in_external_program(self.image_data['image_before']))
        self.output_canvas.bind("<Double-Button-1>",
                                lambda x: self.open_in_external_program(self.image_data['image_after']))
        self.output_canvas.bind("<Enter>", lambda x: self.show_save_output_button())
        self.output_canvas.bind("<Leave>", lambda x: self.hide_save_output_button())

        self.algorithm_btn = self.CustomButton(self.images_frame, text='➡', font=fnt.Font(size=32), width=4,
                                       command=self.start_processing_image)

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

    def load_image_from_path(self, path):
        img = cv2.imread(path)

        if img is not None:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            self.image_data['image_before'] = img
            img_output = self.get_displayable_image(self.image_data['image_before'])
            self.input_img = ImageTk.PhotoImage(image=Image.fromarray(img_output))
            self.input_canvas_image = self.input_canvas.create_image(self.IMG_SIZE / 2, self.IMG_SIZE / 2,
                                                                     anchor=tk.CENTER, image=self.input_img)
            self.clear_output_canvas()
        else:
            messagebox.showinfo('Warning', 'An error occurred while selecting image.')

    def open_file_dialog(self):
        path = filedialog.askopenfilename(initialdir=os.getcwd() + '/input_images',
                                          filetypes=[('Images', self.IMG_EXTENSIONS)])
        if path:
            self.load_image_from_path(path)

    def open_save_dialog(self):
        if self.output_image_displayed:
            path = filedialog.asksaveasfilename(initialdir=os.getcwd() + '/output_images',
                                                filetypes=[('JPG (*.jpg)', '.jpg'), ('PNG (*.png)', '.png')])
            print(path)
            if path:
                cv2.imwrite(path, cv2.cvtColor(self.image_data['image_after'], cv2.COLOR_RGB2BGR))

    def on_file_drop(self, event):
        path = event.data
        if ' ' in path:
            messagebox.showinfo('Warning', 'You can only drag a single image file.')
            return

        if '.' + path.split('.')[-1] in self.IMG_EXTENSIONS:
            self.load_image_from_path(path)
        else:
            messagebox.showinfo('Warning', 'This file type is not supported.')

    def get_displayable_image(self, image):
        h, w, _ = image.shape
        max_dim = max(h, w)
        diff = self.IMG_SIZE / max_dim

        if diff < 1:
            return cv2.resize(image, (0, 0), fx=diff, fy=diff)
        return image

    def start_processing_image(self):
        # if self.image_data.get('image_before', None) is None:
        #     messagebox.showinfo('Warning', 'No image selected.')
        #     return
        #
        # elif not self.image_data['algorithm'].get():
        #     messagebox.showinfo('Warning', 'No algorithm selected.')
        #     return
        #
        # elif self.image_data.get('parameters', None) is None:
        #     messagebox.showinfo('Warning', 'No parameters selected.')
        #     return
        #
        # else:
        self.algorithm_btn['state'] = tk.DISABLED
        self.output_canvas.delete(self.output_canvas_image)
        self.output_canvas.itemconfigure(self.output_canvas_button, state=tk.HIDDEN)
        self.loading_animation(0)
        self.processing_image_thread = threading.Thread(target=self.run_process_image)
        self.processing_image_thread.daemon = True
        self.processing_image_thread.start()
        self.after(20, self.check_processing_thread)

    def run_process_image(self):
        self.image_data['image_after'] = algorithms.process_image(self.image_data['image_before'])
        img_output = self.get_displayable_image(self.image_data['image_after'])
        self.render_right_image(img_output)
        self.algorithm_btn['state'] = tk.NORMAL

    def check_processing_thread(self):
        if self.processing_image_thread.is_alive():
            self.after(20, self.check_processing_thread)
        else:
            self.stop_loading_animation()

    def select_parameters(self):
        self.parameters_window = tk.Toplevel(self)
        self.parameters_window.title("Select algorithm parameters")
        self.parameters_window.geometry("500x500")
        self.parameters_window.configure(bg=self.BG_COLOR)

        self.parameters_window.rowconfigure(0, weight=1)
        self.parameters_window.columnconfigure(0, weight=1)
        self.parameters_window.rowconfigure(2, weight=1)
        self.parameters_window.columnconfigure(2, weight=1)

        parameters_window_main_frame = tk.Frame(self.parameters_window, bg=self.BG_COLOR)
        parameters_window_main_frame.grid(row=1, column=1)

        parameters_frame = tk.Frame(parameters_window_main_frame, bg=self.BG_COLOR)
        parameters_frame.pack(pady=10)

        selected_algorithm = self.select_algorithm_combobox.get()
        selected_algorithm_object = list(filter(lambda a: a['name'] == selected_algorithm, self.ALGORITHMS))[0]

        for i, param in enumerate(selected_algorithm_object['params']):
            label = tk.Label(parameters_frame, text=param['name'], font=self.my_font, bg=self.BG_COLOR)
            label.grid(row=i, column=0, padx=10, sticky=tk.W)

            if param.get('description', None):
                self.CreateToolTip(label, text=param['description'])

            if param.get('type', None) == ParamTypes.INT:
                entry = tk.Entry(parameters_frame, validate='key')
                entry['validatecommand'] = (entry.register(self.validateInt), '%P', '%d')
                entry.grid(row=i, column=1, padx=10, pady=10, sticky=tk.W)
                entry.insert(tk.END, param.get('default_value', None))
                self.image_data['parameters'].append(entry)

            elif param.get('type', None) == ParamTypes.FLOAT:
                entry = tk.Entry(parameters_frame, validate='key')
                entry['validatecommand'] = (entry.register(self.validateFloat), '%P', '%d')
                entry.grid(row=i, column=1, padx=10, pady=10, sticky=tk.W)
                entry.insert(tk.END, param.get('default_value', None))
                self.image_data['parameters'].append(entry)

            elif param.get('type', None) == ParamTypes.BOOL:
                var = tk.IntVar()
                checkbox = tk.Checkbutton(parameters_frame, variable=var, bg=self.BG_COLOR)
                checkbox.grid(row=i, column=1, padx=10, pady=10, sticky=tk.W)
                self.image_data['parameters'].append(var)

        # tk.Label(parameters_frame, text="Parameter A", font=self.my_font_bigger).grid(row=0, column=0, padx=10)
        # tk.Entry(parameters_frame, width=2, font=self.my_font_bigger).grid(row=0, column=1, padx=10, pady=10)
        #
        # tk.Label(parameters_frame, text="Parameter B", font=self.my_font_bigger).grid(row=1, column=0)
        # tk.Entry(parameters_frame, width=2, font=self.my_font_bigger).grid(row=1, column=1, pady=10)
        #
        # tk.Label(parameters_frame, text="Parameter C", font=self.my_font_bigger).grid(row=2, column=0)
        # tk.Entry(parameters_frame, width=2, font=self.my_font_bigger).grid(row=2, column=1, pady=10)

        save_btn = self.CustomButton(parameters_window_main_frame, text='Save', font=self.my_font_bigger, width=10)
        save_btn['command'] = self.set_parameters
        save_btn.pack(pady=10)

    def validateInt(self, inStr, acttyp):
        if acttyp == '1':  # insert
            if not inStr.isdigit():
                return False
        return True

    def validateFloat(self, inStr, acttyp):
        if acttyp == '1':  # insert
            try:
                float(inStr)
                return True
            except ValueError:
                return False
        return True

    def set_parameters(self):
        self.image_data['parameters'] = []
        self.parameters_window.destroy()

    def clear_data(self):
        self.image_data['algorithm'].set('')
        self.image_data['parameters'] = []

        self.clear_input_canvas()
        self.clear_output_canvas()

        self.stop_loading_animation()

        self.algorithm_btn['state'] = tk.NORMAL
        self.select_algorithm_combobox.current(0)

    def show_save_output_button(self):
        if self.output_canvas_image:
            self.output_canvas.itemconfigure(self.output_canvas_button, state=tk.NORMAL)

    def hide_save_output_button(self):
        if self.output_canvas_image:
            self.output_canvas.itemconfigure(self.output_canvas_button, state=tk.HIDDEN)

    def render_right_image(self, image):
        self.output_image_displayed = ImageTk.PhotoImage(image=Image.fromarray(image))
        self.output_canvas_image = self.output_canvas.create_image(self.IMG_SIZE / 2, self.IMG_SIZE / 2,
                                                                   anchor=tk.CENTER, image=self.output_image_displayed)

    def clear_input_canvas(self):
        self.input_canvas.delete(self.input_canvas_image)
        self.input_canvas_image = None
        self.input_image_displayed = None
        self.image_data['image_before'] = None

    def clear_output_canvas(self):
        self.output_canvas.delete(self.output_canvas_image)
        self.output_canvas_image = None
        self.output_image_displayed = None
        self.output_canvas.itemconfigure(self.output_canvas_button, state=tk.HIDDEN)
        self.output_canvas.delete(self.current_gif_frame)
        self.current_gif_frame = None
        self.image_data['image_after'] = None

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
        self.loading_indicator_animation_obj = self.after(15, lambda: self.loading_animation(i))

    def stop_loading_animation(self):
        if self.loading_indicator_animation_obj:
            self.after_cancel(self.loading_indicator_animation_obj)
            self.output_canvas.delete(self.current_gif_frame)
            self.current_gif_frame = None

    def open_in_external_program(self, image):
        if image is not None:
            to_be_shown = Image.fromarray(image)
            to_be_shown.show()

    def CreateToolTip(self, widget, text):
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


if __name__ == "__main__":
    app = App()
    app.mainloop()
