import tkinter as tk
import serial
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from math import sqrt, atan, degrees, pi, cos, sin
import pandas as pd
from ttkthemes import ThemedTk
import datetime

pd.set_option("display.max_columns", None)  # Display all columns in DataFrame
port_name = "COM5"

class DotTracker:
    def __init__(self):
        self.run_time = None
        self.root = ThemedTk(theme="arc")  # Set modern theme
        self.root.title('Sprinkler controller - YTP2023')
        self.root.geometry('1200x800')
        self.root.iconbitmap('icon.ico')
        self.commands_to_send = []
        self.currently_executing = False
        # Create a serial connection to the ESP32
        self.serial = serial.Serial(port_name, 115200)

        # Create styles for active and normal buttons
        self.style = ttk.Style()
        self.style.map("Active.Treeview",
                       background=[('active', 'light blue')],
                       foreground=[('active', 'black')])
        self.style.map("Normal.Treeview",
                       background=[('active', 'SystemButtonFace')],
                       foreground=[('active', 'black')])

        # Frame at the top for buttons and label
        self.top_frame = ttk.Frame(self.root)
        self.top_frame.pack(side='top', fill='x')

        # Add a "Run" button
        self.run_button = ttk.Button(self.top_frame, text='Run', command=self.run_servo)
        self.run_button.pack(side='left')
        # Reset button
        self.reset_button = ttk.Button(self.top_frame, text='Reset', command=self.reset_canvas)
        self.reset_button.pack(side='left')

        # Save button
        self.save_button = ttk.Button(self.top_frame, text='Save', command=self.save_data)
        self.save_button.pack(side='left')

        # Tree selection buttons and time input
        self.tree_buttons = []
        self.tree_times = []
        for i in range(1, 4):
            button = ttk.Button(self.top_frame, text=f'Tree {i}', command=lambda i=i-1: self.select_tree(i), style='Normal.TButton')
            button.pack(side='left')
            self.tree_buttons.append(button)
            time_input = ttk.Entry(self.top_frame)
            time_input.pack(side='left')
            time_input.insert(0, str(i*3))
            self.tree_times.append(time_input)

        self.current_tree = 0
        self.tree_buttons[self.current_tree].config(style='Active.TButton')

        # Label for total water use
        self.total_water_use = ttk.Label(self.top_frame, text='Total water use: 0 litre')
        self.total_water_use.pack(side='left')

        # Label for total time
        self.total_time = ttk.Label(self.top_frame, text='Total time: 0 sec')
        self.total_time.pack(side='left')

        self.canvas = tk.Canvas(self.root, width=800, height=600)
        self.canvas.pack()

        # Text widget for showing data
        self.data_text = tk.Text(self.root, state='disabled', height=10)
        self.data_text.pack(side='bottom', fill='x')

        self.red_dot = (400, 595)
        self.canvas.create_oval(self.red_dot[0] - 5, self.red_dot[1] - 5,
                                self.red_dot[0] + 5, self.red_dot[1] + 5,
                                fill='red')
        self.dot_number = 0
        self.data = []

        # Load images and resize them to be 80x80 pixels
        self.tree_images = []
        for i in range(1, 4):
            image = Image.open(f"tree_{i}.png")
            image = image.resize((80, 80), Image.LANCZOS)  # change to LANCZOS
            self.tree_images.append(ImageTk.PhotoImage(image))
        self.current_tree = 0
        # self.tree_buttons[self.current_tree].config(background='light blue')  # Removed line to highlight current tree button

        self.canvas_items = []  # Keep track of all items added to the canvas
        self.canvas.bind('<Button-1>', self.add_dot)
        self.root.bind('<Control-z>', self.undo_last_draw)

        # Draw half-circle
        for i in range(181):
            angle_in_radians = i * pi / 180
            line_length = 400
            line_end_x = self.red_dot[0] + line_length * cos(angle_in_radians)
            line_end_y = self.red_dot[1] - line_length * sin(angle_in_radians)
            self.canvas.create_line(self.red_dot[0], self.red_dot[1], line_end_x, line_end_y, fill='green', dash=(4, 2))

    def add_dot(self, event):
        x, y = event.x, event.y
        image_id = self.canvas.create_image(x, y, image=self.tree_images[self.current_tree], anchor='center')
        self.canvas_items.append(image_id)  # Add id to canvas_items
        line_id = self.canvas.create_line(self.red_dot[0], self.red_dot[1], x, y, fill='black')
        self.canvas_items.append(line_id)  # Add id to canvas_items

        dx, dy = x - self.red_dot[0], self.red_dot[1] - y
        distance = sqrt(dx ** 2 + dy ** 2)
        angle = degrees(atan(abs(dy) / abs(dx))) if dx != 0 else 90.0

        if dx >= 0:  # Quadrant 4 and 1
            degree_right = angle
            degree_left = 180 - angle
        else:  # Quadrant 3 and 2
            degree_left = angle
            degree_right = 180 - degree_left

        out_of_range = 1 if distance > 400 else 0

        self.data.append({
            'dot_no': self.dot_number,
            'distance': distance,
            'degree_left': degree_left,
            'degree_right': degree_right,
            'location_x': x,
            'location_y': y,
            'tree_type': f'tree_{self.current_tree + 1}',
            'time': self.tree_times[self.current_tree].get(),
            'out_of_range': out_of_range,
            'mark_time': datetime.datetime.now(),
            'run_time': self.run_time if self.dot_number != 0 else datetime.datetime.now()
        })

        self.dot_number += 1

        self.update_text()

    def undo_last_draw(self, event):
        if self.canvas_items:
            self.canvas.delete(self.canvas_items[-1])  # Remove last line
            self.canvas.delete(self.canvas_items[-2])  # Remove last image
            self.canvas_items = self.canvas_items[:-2]  # Remove last two items from the list
            if self.data:
                self.data.pop(-1)  # Remove last item from data
            self.dot_number -= 1 if self.dot_number > 0 else 0  # Decrease dot number
            self.update_text()

    def run(self):
        self.root.mainloop()

    def select_tree(self, index):
        self.tree_buttons[self.current_tree].config(style='Normal.TButton')  # Unhighlight previous tree button
        self.current_tree = index
        self.tree_buttons[self.current_tree].config(style='Active.TButton')  # Highlight current tree button

    def reset_canvas(self):
        self.canvas.delete('all')
        self.data = []
        self.dot_number = 0
        self.run_time = datetime.datetime.now()

        # Redraw half-circle
        for i in range(181):
            angle_in_radians = i * pi / 180
            line_length = 400
            line_end_x = self.red_dot[0] + line_length * cos(angle_in_radians)
            line_end_y = self.red_dot[1] - line_length * sin(angle_in_radians)
            self.canvas.create_line(self.red_dot[0], self.red_dot[1], line_end_x, line_end_y, fill='green', dash=(4, 2))

        self.update_text()

    def update_text(self):
        self.data_text.configure(state='normal')
        self.data_text.delete('1.0', 'end')
        df = pd.DataFrame(self.data)
        if 'dot_no' in df.columns:
            df = df.sort_values(by=['dot_no'], ascending=False)
        else:
            print("'dot_no' column is missing in DataFrame.")

        # fill run_time with run_time in dot_no 0
        if 'run_time' not in df.columns:
            df['run_time'] = df.loc[df['dot_no'] == 0, 'run_time'].iloc[0]
        else:
            df['run_time'] = df['run_time'].fillna(df.loc[df['dot_no'] == 0, 'run_time'].iloc[0])
        # display only date hour mind and sec not microsec
        df['run_time'] = df['run_time'].dt.strftime('%Y-%m-%d %H:%M:%S')
        df['mark_time'] = df['mark_time'].dt.strftime('%Y-%m-%d %H:%M:%S')
        # display only 2 decimal places
        df['distance'] = df['distance'].round(2)
        df['degree_left'] = df['degree_left'].round(2)
        df['degree_right'] = df['degree_right'].round(2)

        # df drop out_of_range column
        df = df.drop(columns=['out_of_range', 'location_x', 'location_y'])
        # add line between columns
        self.data_text.insert('end', df.to_markdown(index=False, tablefmt='github'))
        self.data_text.configure(state='disabled')

        total_time = df['time'].astype(float).sum()
        self.total_time.config(text=f'Total time: {total_time} sec')

        total_water_use = total_time * 0.0166
        self.total_water_use.config(text=f'Total water use: {total_water_use:.2f} litre  | ')

    def run_servo(self):
        # Get the data to be sent to the ESP32
        df = pd.DataFrame(self.data)
        if 'dot_no' in df.columns:
            df = df.sort_values(by=['degree_right'])
            for _, row in df.iterrows():
                degree = round(row['degree_right'])
                time = row['time']
                # Send the data to the ESP32
                command = f'{degree},{time}\n'
                print(command)
                self.serial.write(command.encode())
                # add command 0 degree to stop servo
                command = f'0,0\n'
                self.serial.write(command.encode())
        else:
            print("'dot_no' column is missing in DataFrame.")

    def save_data(self):
        df = pd.DataFrame(self.data)
        if 'run_time' not in df.columns:
            print("'run_time' column is missing in DataFrame.")
        else:
            df['run_time'] = df['run_time'].fillna(df.loc[df['dot_no'] == 0, 'run_time'].iloc[0])
        df.to_csv('output.csv', index=False)
        messagebox.showinfo('Information', 'Data saved to output.csv')


if __name__ == "__main__":
    dt = DotTracker()
    try:
        dt.run()
    except tk.TclError:
        pass

#%%
