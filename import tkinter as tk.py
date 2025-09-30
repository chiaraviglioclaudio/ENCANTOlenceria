import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
from datetime import datetime

try:
    from openpyxl import Workbook
except ImportError:
    Workbook = None

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
except ImportError:
    SimpleDocTemplate = None

DATA_FILE = "productos.json"
VENTAS_FILE = "ventas.json"

class SistemaRopaInterior:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Gestión - Ropa Interior")
        self.productos = []
        self.ventas = []

        self.cargar_datos()
        self.cargar_ventas()
        self.crear_interfaz()

    def crear_interfaz(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True)

        # --- PESTAÑA PRODUCTOS ---
        tab_productos = ttk.Frame(notebook)
        notebook.add(tab_productos, text="Productos")

        frame_form = ttk.LabelFrame(tab_productos, text="Cargar Producto", padding=10)
        frame_form.pack(fill="x", padx=10, pady=10)

        ttk.Label(frame_form, text="Artículo:").grid(row=0, column=0, padx=5, pady=5)
        self.entry_articulo = ttk.Entry(frame_form, width=30)
        self.entry_articulo.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame_form, text="Nombre:").grid(row=1, column=0, padx=5, pady=5)
        self.entry_nombre = ttk.Entry(frame_form, width=30)
        self.entry_nombre.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(frame_form, text="Marca:").grid(row=2, column=0, padx=5, pady=5)
        self.entry_marca = ttk.Entry(frame_form, width=30)
        self.entry_marca.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(frame_form, text="Precio:").grid(row=3, column=0, padx=5, pady=5)
        self.entry_precio = ttk.Entry(frame_form, width=30)
        self.entry_precio.grid(row=3, column=1, padx=5, pady=5)

        ttk.Label(frame_form, text="Stock:").grid(row=4, column=0, padx=5, pady=5)
        self.entry_stock = ttk.Entry(frame_form, width=30)
        self.entry_stock.grid(row=4, column=1, padx=5, pady=5)

        ttk.Button(frame_form, text="Agregar Producto", command=self.agregar_producto).grid(row=5, column=0, columnspan=2, pady=10)

        self.tree = ttk.Treeview(tab_productos, columns=("Articulo", "Marca", "Precio", "Stock"), show="headings", height=12)
        self.tree.heading("Articulo", text="Artículo")
        self.tree.heading("Marca", text="Marca")
        self.tree.heading("Precio", text="Precio")
        self.tree.heading("Stock", text="Stock")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        self.actualizar_tabla()

        frame_botones = ttk.Frame(tab_productos, padding=10)
        frame_botones.pack(fill="x")
        ttk.Button(frame_botones, text="Modificar Precios por Marca (%)", command=self.modificar_precios_marca).pack(side="left", padx=5)
        ttk.Button(frame_botones, text="Actualizar Stock", command=self.actualizar_stock).pack(side="left", padx=5)
        ttk.Button(frame_botones, text="Eliminar Producto", command=self.eliminar_producto).pack(side="left", padx=5)

        # --- PESTAÑA VENTAS ---
        tab_ventas = ttk.Frame(notebook)
        notebook.add(tab_ventas, text="Ventas")

        frame_busqueda = ttk.Frame(tab_ventas, padding=10)
        frame_busqueda.pack(fill="x")
        ttk.Label(frame_busqueda, text="Buscar por Artículo:").pack(side="left")
        self.entry_buscar_articulo = ttk.Entry(frame_busqueda, width=20)
        self.entry_buscar_articulo.pack(side="left", padx=5)
        ttk.Button(frame_busqueda, text="Buscar", command=self.buscar_por_articulo).pack(side="left")
        ttk.Button(frame_busqueda, text="Limpiar", command=self.actualizar_combo_productos).pack(side="left")

        frame_ventas = ttk.LabelFrame(tab_ventas, text="Registrar Venta", padding=10)
        frame_ventas.pack(fill="x", padx=10, pady=10)

        ttk.Label(frame_ventas, text="Producto:").grid(row=0, column=0, padx=5, pady=5)
        self.combo_productos = ttk.Combobox(frame_ventas, state="readonly", width=50)
        self.combo_productos.grid(row=0, column=1, padx=5, pady=5)
        self.actualizar_combo_productos()

        ttk.Label(frame_ventas, text="Cantidad:").grid(row=1, column=0, padx=5, pady=5)
        self.entry_cantidad_venta = ttk.Entry(frame_ventas, width=10)
        self.entry_cantidad_venta.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        ttk.Button(frame_ventas, text="Registrar Venta", command=self.registrar_venta).grid(row=2, column=0, columnspan=2, pady=10)

        frame_historial = ttk.LabelFrame(tab_ventas, text="Historial de Ventas", padding=10)
        frame_historial.pack(fill="both", expand=True, padx=10, pady=10)

        self.tree_ventas = ttk.Treeview(frame_historial, columns=("Fecha", "Articulo", "Producto", "Marca", "Cantidad", "Total"), show="headings", height=10)
        self.tree_ventas.heading("Fecha", text="Fecha")
        self.tree_ventas.heading("Articulo", text="Artículo")
        self.tree_ventas.heading("Producto", text="Producto")
        self.tree_ventas.heading("Marca", text="Marca")
        self.tree_ventas.heading("Cantidad", text="Cant.")
        self.tree_ventas.heading("Total", text="Total $")
        self.tree_ventas.pack(fill="both", expand=True)

        self.actualizar_tabla_ventas()

        frame_exportar = ttk.Frame(tab_ventas, padding=10)
        frame_exportar.pack(fill="x")
        ttk.Button(frame_exportar, text="Exportar Ventas a Excel", command=self.exportar_excel).pack(side="left", padx=5)
        ttk.Button(frame_exportar, text="Exportar Ventas a PDF", command=self.exportar_pdf).pack(side="left", padx=5)

    # --- FUNCIONES PRODUCTOS ---
    def actualizar_stock(self):
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showerror("Error", "Seleccione un producto para actualizar stock.")
            return

        idx = self.tree.index(seleccion[0])
        producto = self.productos[idx]

        try:
            cantidad = int(simpledialog.askstring("Actualizar Stock", f"Ingrese la cantidad a agregar para '{producto['nombre']}' (stock actual: {producto['stock']}):"))
            if cantidad <= 0:
                raise ValueError
        except (ValueError, TypeError):
            messagebox.showerror("Error", "Cantidad inválida.")
            return

        producto['stock'] += cantidad
        self.guardar_datos()
        self.actualizar_tabla()
        self.actualizar_combo_productos()
        messagebox.showinfo("Stock Actualizado", f"El stock de '{producto['nombre']}' ahora es {producto['stock']}")
