import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import re
import time

# -------------------------
# Clases de modelo
# -------------------------
class Error:
    def __init__(self, tipo, mensaje):
        self.tipo = tipo
        self.mensaje = mensaje

class Transicion:
    #Representación de una transición
    def __init__(self, estado_origen, simbolo_lectura, estado_destino, simbolo_escritura, movimiento):
        self.estado_origen = estado_origen
        self.simbolo_lectura = simbolo_lectura
        self.estado_destino = estado_destino
        self.simbolo_escritura = simbolo_escritura
        self.movimiento = movimiento  # 'L', 'R' o 'S'

class MaquinaTuring:
    BLANK = '_'  # símbolo de celda vacía

    def __init__(self):
        self.cinta = []
        self.head = 0
        self.estado = 'q0'
        self.pasos = 0
        self.halted = False
        self.accept = None
        self.transiciones = {}  # dict (estado, simbolo)->Transicion (opcional)

    def construir_cinta(self, entrada, padding=20):
        #Construye la cinta con padding de celdas en blanco a ambos lados.
        self.cinta = [self.BLANK] * padding + list(entrada) + [self.BLANK] * padding
        self.head = padding
        self.estado = 'q0'
        self.pasos = 0
        self.halted = False
        self.accept = None

    def paso_simulacion(self):
    
        #Realiza un 'paso' de la simulación visual.
        
        if self.halted:
            return None

        simbolo = self.cinta[self.head] if 0 <= self.head < len(self.cinta) else self.BLANK
        info = ''
        if self.estado == 'q0':
            info = f"Estado q0: lectura inicial en posición {self.head}"
            self.estado = 'q_scan'
        elif self.estado == 'q_scan':
            if simbolo == self.BLANK:
                self.estado = 'q_final'
                self.halted = True
                info = "Se detectó BLANK: detención para evaluación final"
                self.pasos += 1
                return {"cinta": list(self.cinta), "head": self.head, "estado": self.estado, "info": info, "halted": True}
            else:
                info = f"Lectura '{simbolo}' en pos {self.head}; avanzando a la derecha"
                self.head += 1
        else:
            info = f"Estado {self.estado}"
            self.halted = True

        self.pasos += 1
        return {"cinta": list(self.cinta), "head": self.head, "estado": self.estado, "info": info, "halted": self.halted}

    def reiniciar(self):
        self.estado = 'q0'
        self.pasos = 0
        self.halted = False
        self.accept = None

# -------------------------
# Lista de expresiones que pueden usarse
# -------------------------
REGEXES = [
    ("(a|b)*abb", r"^(?:a|b)*abb$"),
    ("0*1*", r"^0*1*$"),
    ("(ab)*", r"^(?:ab)*$"),
    ("1(01)*0", r"^1(?:01)*0$"),
    ("(a+b)*a(a+b)*  (contiene al menos una 'a')", r"^(?:a|b)*a(?:a|b)*$"),
    ("a*b", r"^a*b$"),
    ("a*", r"^a*$"),
    ("b*", r"^b*$"),
    ("(a|b)*ba", r"^(?:a|b)*ba$"),
    ("(ab|ba)*", r"^(?:ab|ba)*$"),
]

# -------------------------
# Interfaz gráfica (Tkinter)
# -------------------------
class SimuladorTuringApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulador de Máquina de Turing")
        self.root.geometry("1100x600")
        self.root.configure(bg='#f4f6fb')

        # Variables internas
        self.mt = MaquinaTuring()
        self.current_regex_index = 0
        self.auto_running = False
        self.auto_delay_ms = 400  # tiempo entre pasos cuando corre en automático
        self.visual_cells = 25  # número de celdas visibles en la cinta
        self.cell_width = 44
        self.cell_height = 56

        # Construcción de la interfaz
        self.configurar_estilos()
        self.crear_layout()
        self.dibujar_cinta_inicial("")

    def configurar_estilos(self):
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass
        # Estilos para ttk
        style.configure('TLabel', background='#f4f6fb', foreground='#173753', font=('Segoe UI', 10))
        style.configure('Titulo.TLabel', font=('Segoe UI', 16, 'bold'), background='#dfe9f3', foreground='#0f3446')
        style.configure('Subtitulo.TLabel', font=('Segoe UI', 10, 'italic'), background='#dfe9f3', foreground='#0f5a78')
        style.configure('TButton', font=('Segoe UI', 10), padding=6)

    def crear_layout(self):
        # panel superior: título y controles básicos
        frame_top = tk.Frame(self.root, bg='#dfe9f3', height=110)
        frame_top.pack(fill=tk.X, padx=12, pady=8)
        frame_top.pack_propagate(False)

        # Usar ttk.Label para aprovechar style
        titulo = ttk.Label(frame_top, text="Proyecto 3 - Simulador de Maquina de Turing", style='Titulo.TLabel')
        titulo.pack(anchor='w', padx=16, pady=(10, 2))
        subtitulo = ttk.Label(frame_top, text="Creador por: Ian Ponce - 1163524", style='Subtitulo.TLabel')
        subtitulo.pack(anchor='w', padx=16)

        # Controles: entrada, selección regex, botones
        controls = tk.Frame(frame_top, bg='#dfe9f3')
        controls.pack(fill=tk.X, padx=16, pady=8)

        tk.Label(controls, text="Cadena de entrada:", bg='#dfe9f3').grid(row=0, column=0, sticky='w')
        self.input_var = tk.StringVar()
        self.input_entry = ttk.Entry(controls, textvariable=self.input_var, width=36)
        self.input_entry.grid(row=0, column=1, padx=8, sticky='w')

        tk.Label(controls, text="Expresión regular:", bg='#dfe9f3').grid(row=1, column=0, sticky='w', pady=(6,0))
        regex_names = [r[0] for r in REGEXES]
        self.regex_var = tk.StringVar(value=regex_names[0])
        self.regex_combo = ttk.Combobox(controls, values=regex_names, textvariable=self.regex_var, state='readonly', width=56)
        self.regex_combo.grid(row=1, column=1, columnspan=3, sticky='w', padx=8, pady=(6,0))

        # Botones de control
        btn_frame = tk.Frame(controls, bg='#dfe9f3')
        btn_frame.grid(row=0, column=2, rowspan=2, padx=8)

        self.btn_load = ttk.Button(btn_frame, text="Preparar simulación", command=self.preparar_simulacion)
        self.btn_step = ttk.Button(btn_frame, text="Paso", command=self.paso)
        self.btn_auto = ttk.Button(btn_frame, text="Iniciar automático", command=self.toggle_auto)
        self.btn_reset = ttk.Button(btn_frame, text="Reiniciar", command=self.reset_simulador)
        self.btn_export = ttk.Button(btn_frame, text="Exportar reporte", command=self.exportar_reporte)

        self.btn_load.grid(row=0, column=0, padx=6, pady=2)
        self.btn_step.grid(row=0, column=1, padx=6, pady=2)
        self.btn_auto.grid(row=0, column=2, padx=6, pady=2)
        self.btn_reset.grid(row=0, column=3, padx=6, pady=2)
        self.btn_export.grid(row=1, column=0, columnspan=4, pady=(6,0), sticky='ew')

        # Panel central: cinta visual y detalles
        center = tk.Frame(self.root, bg='#f4f6fb')
        center.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0,12))

        # pantalla para la cinta
        tape_frame = tk.Frame(center, bg='#ffffff', relief=tk.FLAT, bd=0)
        tape_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0,12), pady=6)

        self.canvas = tk.Canvas(tape_frame, bg='#ffffff', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Panel lateral: estado, info, lista de regex
        side = tk.Frame(center, width=320, bg='#eff6fb')
        side.pack(side=tk.RIGHT, fill=tk.Y)
        side.pack_propagate(False)

        # Estado actual
        state_frame = tk.Frame(side, bg='#eff6fb', pady=10)
        state_frame.pack(fill=tk.X, padx=10, pady=(10,6))

        tk.Label(state_frame, text="Estado actual:", bg='#eff6fb', fg='#173753', font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        self.lbl_estado = tk.Label(state_frame, text="-", bg='#eff6fb', fg='#0f4a62', font=('Segoe UI', 12))
        self.lbl_estado.pack(anchor='w', pady=(4,0))

        tk.Label(state_frame, text="Información:", bg='#eff6fb', fg='#173753', font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(10,0))
        self.lbl_info = tk.Label(state_frame, text="-", bg='#eff6fb', fg='#0f4a62', font=('Segoe UI', 10), wraplength=290, justify='left')
        self.lbl_info.pack(anchor='w', pady=(4,0))

        # Resultado final
        result_frame = tk.Frame(side, bg='#eff6fb', pady=8)
        result_frame.pack(fill=tk.X, padx=10, pady=(6,10))

        tk.Label(result_frame, text="Resultado final:", bg='#eff6fb', fg='#173753', font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        self.lbl_result = tk.Label(result_frame, text="-", bg='#eff6fb', fg='#0f4a62', font=('Segoe UI', 12, 'bold'))
        self.lbl_result.pack(anchor='w', pady=(4,0))

        # Lista de expresiones (detalle)
        tk.Label(side, text="Expresiones regulares disponibles", bg='#eff6fb', fg='#173753', font=('Segoe UI', 10, 'bold')).pack(anchor='w', padx=10, pady=(8,0))
        self.list_regex = tk.Listbox(side, height=10, bg='#fbfdff', fg='#0f3b56', font=('Consolas', 10), activestyle='none')
        for i, (name, pat) in enumerate(REGEXES):
            self.list_regex.insert(tk.END, f"{i+1}. {name}")
        self.list_regex.pack(fill=tk.BOTH, padx=10, pady=(6,10), expand=False)

        # Ayuda / Manual
        help_frame = tk.Frame(side, bg='#eff6fb')
        help_frame.pack(fill=tk.X, padx=10, pady=(6,10))
        tk.Button(help_frame, text="Manual de usuario", command=self.mostrar_manual, relief=tk.FLAT, bg='#e1eef8').pack(fill=tk.X)

        # Preparar estructura visual de celdas
        self.canvas.bind("<Configure>", lambda e: self.redibujar_cinta())  # redibujar en cambio de tamaño

        # estado inicial
        self.preparado = False
        self.step_generator = None

    # ---------------------
    # Funciones de interfaz
    # ---------------------
    def mostrar_manual(self):
        texto = (
            "Manual de usuario - Simulador Máquina de Turing\n\n"
            "1. Escriba la cadena de entrada en el campo 'Cadena de entrada'.\n"
            "2. Seleccione una expresión regular de la lista desplegable.\n"
            "3. Pulse 'Preparar simulación' para inicializar la cinta.\n"
            "4. Use 'Paso' para ejecutar un único paso o 'Iniciar automático' para ejecutar automáticamente.\n"
            "5. 'Reiniciar' vuelve al estado inicial para ingresar otra cadena.\n\n"
            "La aceptación final de la cadena se determina con la expresión regular seleccionada.\n"
            "La simulación visual muestra el movimiento del cabezal y el estado actual."
        )
        messagebox.showinfo("Manual de usuario", texto)

    def exportar_reporte(self):
        #Exporta un reporte simple con datos de la última simulación.
        try:
            txt = []
            txt.append("REPORTE SIMULADOR MÁQUINA DE TURING\n")
            txt.append(f"Cadena: {self.input_var.get()}\n")
            txt.append(f"Expresión regular: {self.regex_var.get()}\n")
            txt.append(f"Pasos ejecutados: {self.mt.pasos}\n")
            txt.append(f"Estado final: {self.mt.estado}\n")
            txt.append(f"Aceptada: {self.mt.accept}\n")
            filename = "reporte_simulador_turing.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write("\n".join(txt))
            messagebox.showinfo("Exportado", f"Reporte guardado como {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar el reporte: {e}")

    # ---------------------
    # Funciones de simulación
    # ---------------------
    def preparar_simulacion(self):
        entrada = self.input_var.get().strip()
        self.mt.construir_cinta(entrada, padding=20)
        self.mt.reiniciar()
        self.preparado = True
        self.mt.accept = None
        self.lbl_result.config(text="-")
        self.lbl_estado.config(text=self.mt.estado)
        self.lbl_info.config(text="Simulación preparada. Use Paso o Iniciar automático.")
        self.current_regex_index = self._regex_index_from_combo()
        self.dibujar_cinta_inicial(entrada)

    def _regex_index_from_combo(self):
        name = self.regex_var.get()
        for i, (n, p) in enumerate(REGEXES):
            if n == name:
                return i
        return 0

    def paso(self):
        if not self.preparado:
            messagebox.showwarning("No preparado", "Pulse 'Preparar simulación' antes de ejecutar.")
            return
        estado_visual = self.mt.paso_simulacion()
        if estado_visual is None:
            self.finalizar_evaluacion()
            return
        cinta = estado_visual["cinta"]
        head = estado_visual["head"]
        estado = estado_visual["estado"]
        info = estado_visual["info"]
        halted = estado_visual["halted"]

        self.actualizar_visual(cinta, head)
        self.lbl_estado.config(text=estado)
        self.lbl_info.config(text=info)

        if halted:
            self.finalizar_evaluacion()

    def toggle_auto(self):
        if not self.preparado:
            messagebox.showwarning("No preparado", "Pulse 'Preparar simulación' antes de ejecutar.")
            return
        if not self.auto_running:
            self.auto_running = True
            self.btn_auto.config(text="Detener automático")
            self._auto_step()
        else:
            self.auto_running = False
            self.btn_auto.config(text="Iniciar automático")

    def _auto_step(self):
        if not self.auto_running:
            return
        estado_visual = self.mt.paso_simulacion()
        if estado_visual is None:
            self.finalizar_evaluacion()
            self.auto_running = False
            self.btn_auto.config(text="Iniciar automático")
            return

        cinta = estado_visual["cinta"]
        head = estado_visual["head"]
        estado = estado_visual["estado"]
        info = estado_visual["info"]
        halted = estado_visual["halted"]

        self.actualizar_visual(cinta, head)
        self.lbl_estado.config(text=estado)
        self.lbl_info.config(text=info)

        if halted:
            self.finalizar_evaluacion()
            self.auto_running = False
            self.btn_auto.config(text="Iniciar automático")
            return

        self.root.after(self.auto_delay_ms, self._auto_step)

    def finalizar_evaluacion(self):
        """
        Cuando la simulación termina, se evalua la cadena con la expresión regular que se ingresó.
        """
        cadena = self.input_var.get().strip()
        idx = self.current_regex_index
        pattern = REGEXES[idx][1]
        try:
            m = re.fullmatch(pattern, cadena)
            aceptada = bool(m)
        except re.error:
            aceptada = False

        self.mt.accept = aceptada
        self.lbl_result.config(text="ACEPTADA" if aceptada else "RECHAZADA")
        self.lbl_info.config(text=f"Simulación finalizada en {self.mt.pasos} pasos. La expresion fue: {'ACEPTADA' if aceptada else 'RECHAZADA'}")
        self.lbl_estado.config(text=self.mt.estado if not self.mt.halted else "q_final")

    # ---------------------
    # Visualización de la cinta 
    # ---------------------
    def dibujar_cinta_inicial(self, entrada):
        # Dibuja la cinta inicial con las celdas visibles centradas en la cabeza
        self.canvas.delete("all")
        width = self.canvas.winfo_width() or 800
        height = self.canvas.winfo_height() or 220
        num = self.visual_cells
        total_w = num * (self.cell_width + 6)
        start_x = max(10, (width - total_w)//2)
        y = max(20, (height - self.cell_height)//2)
        # Guardar coordenada y para usar en marcador de cabeza
        self.cinta_y = y

        # Positions de celdas
        self.cell_positions = []
        for i in range(num):
            x = start_x + i * (self.cell_width + 6)
            rect = self.canvas.create_rectangle(x, y, x + self.cell_width, y + self.cell_height, fill='#fbfdff', outline='#c9d8e8', width=2, tags=("cell", f"cell{i}"))
            txt = self.canvas.create_text(x + self.cell_width//2, y + self.cell_height//2, text="", font=('Consolas', 14), tags=("text", f"text{i}"))
            self.cell_positions.append((x, rect, txt))
        # marcador/cabezal (triángulo)
        self.head_marker = self.canvas.create_polygon(0,0,0,0,0,0, fill='#d8e7f4', outline='#9fb7d7', tags=("head",))
        # Actualizar con el contenido actual de la cinta
        self.actualizar_visual(self.mt.cinta, self.mt.head)

    def redibujar_cinta(self):
        # redibuja toda la cinta cuando la ventana cambia de tamaño
        self.dibujar_cinta_inicial(self.input_var.get())

    def actualizar_visual(self, cinta, head_index):
        # Actualiza las celdas visibles a partir de la cinta y la posición de la cabeza
        if not hasattr(self, "cell_positions") or not self.cell_positions:
            self.dibujar_cinta_inicial(self.input_var.get())

        num = self.visual_cells
        # ventana centrada en head_index
        left = max(0, head_index - num//2)
        if left + num > len(cinta):
            left = max(0, len(cinta) - num)
        # actualizar textos y colores
        for i in range(num):
            symbol = cinta[left + i] if 0 <= left + i < len(cinta) else MaquinaTuring.BLANK
            x, rect_id, txt_id = self.cell_positions[i]
            # actualizar símbolo
            self.canvas.itemconfigure(txt_id, text=symbol)
            # resaltar la celda bajo la cabeza
            if left + i == head_index:
                self.canvas.itemconfigure(rect_id, fill='#fcedd9')
                self.canvas.itemconfigure(rect_id, outline='#f0b66f')
            else:
                self.canvas.itemconfigure(rect_id, fill='#fbfdff')
                self.canvas.itemconfigure(rect_id, outline='#c9d8e8')
        # actualizar marcador de cabeza (triángulo hacia abajo)
        arrow_index = head_index - left
        if 0 <= arrow_index < num:
            x_pos = self.cell_positions[arrow_index][0] + self.cell_width//2
            y_top = self.cinta_y - 12
            size = 8
            points = [x_pos - size, y_top, x_pos + size, y_top, x_pos, y_top + size]
            self.canvas.coords(self.head_marker, *points)
            self.canvas.tag_raise(self.head_marker)

    # ---------------------
    # Reinicio y limpieza
    # ---------------------
    def reset_simulador(self):
        self.auto_running = False
        self.preparado = False
        self.mt = MaquinaTuring()
        self.input_var.set("")
        self.lbl_estado.config(text="-")
        self.lbl_info.config(text="-")
        self.lbl_result.config(text="-")
        self.btn_auto.config(text="Iniciar automático")
        self.dibujar_cinta_inicial("")
        messagebox.showinfo("Reiniciado", "Simulador reiniciado. Ingrese nueva cadena y seleccione una expresión.")

# -------------------------
# Main
# -------------------------
def main():
    root = tk.Tk()
    app = SimuladorTuringApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()
