"""
gestor_ropa_interior_profesional.py
Sistema profesional de gestión de productos y ventas (Tkinter).

- Autocompletado búsqueda por artículo/nombre.
- Carrito de venta con varios artículos y cantidades editables.
- Registro de cliente por venta (nombre, DNI, teléfono).
- Stock descontado automáticamente al registrar la venta.
- Reporte por rango de fechas en ventana nueva + exportar a Excel/PDF.
- Persistencia en JSON: productos.json y ventas.json.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from datetime import datetime
import json, os

# Optional libs for export
try:
    from openpyxl import Workbook
except Exception:
    Workbook = None

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
except Exception:
    SimpleDocTemplate = None

DATA_FILE = "productos.json"
VENTAS_FILE = "ventas.json"

class GestorRopaInterior:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestor - Ropa Interior (Profesional)")
        self.root.geometry("1200x760")
        self.productos = []
        self.ventas = []
        self.cargar_datos()
        self.cargar_ventas()
        self.crear_ui()

    # -------------------- I/O --------------------
    def cargar_datos(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.productos = data
                    else:
                        self.productos = []
            except Exception:
                messagebox.showwarning("Aviso", f"{DATA_FILE} corrupto. Iniciando inventario vacío.")
                self.productos = []
        else:
            self.productos = []

        # normalize types
        for p in self.productos:
            try: p["precio"] = float(p.get("precio", 0) or 0)
            except: p["precio"] = 0.0
            try: p["stock"] = int(p.get("stock", 0) or 0)
            except: p["stock"] = 0
            p["articulo"] = str(p.get("articulo","")).strip()
            p["nombre"] = str(p.get("nombre","")).strip()
            p["marca"] = str(p.get("marca","")).strip()

    def guardar_datos(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.productos, f, indent=4, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar productos: {e}")

    def cargar_ventas(self):
        if os.path.exists(VENTAS_FILE):
            try:
                with open(VENTAS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.ventas = data
                    else:
                        self.ventas = []
            except Exception:
                messagebox.showwarning("Aviso", f"{VENTAS_FILE} corrupto. Iniciando historial vacío.")
                self.ventas = []
        else:
            self.ventas = []

    def guardar_ventas(self):
        try:
            with open(VENTAS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.ventas, f, indent=4, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar ventas: {e}")

    # -------------------- UI --------------------
    def crear_ui(self):
        # Notebook
        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True, padx=8, pady=8)

        # Tab Productos
        tab_prod = ttk.Frame(nb)
        nb.add(tab_prod, text="Productos")
        self._ui_productos(tab_prod)

        # Tab Ventas
        tab_ventas = ttk.Frame(nb)
        nb.add(tab_ventas, text="Ventas")
        self._ui_ventas(tab_ventas)

        # Footer: info sobre dependencias
        info = "Export: openpyxl (Excel) and reportlab (PDF). Install with: pip install openpyxl reportlab"
        lbl = ttk.Label(self.root, text=info, foreground="gray")
        lbl.pack(fill="x", side="bottom", padx=8, pady=(0,6))

    # -------------------- UI Productos --------------------
    def _ui_productos(self, parent):
        frm = ttk.LabelFrame(parent, text="Agregar / Editar Producto", padding=10)
        frm.pack(fill="x", padx=10, pady=10)

        ttk.Label(frm, text="Artículo:").grid(row=0, column=0, sticky="w")
        self.ent_articulo = ttk.Entry(frm, width=20); self.ent_articulo.grid(row=0, column=1, padx=6)
        ttk.Label(frm, text="Nombre:").grid(row=0, column=2, sticky="w")
        self.ent_nombre = ttk.Entry(frm, width=40); self.ent_nombre.grid(row=0, column=3, padx=6)
        ttk.Label(frm, text="Marca:").grid(row=1, column=0, sticky="w")
        self.ent_marca = ttk.Entry(frm, width=20); self.ent_marca.grid(row=1, column=1, padx=6)
        ttk.Label(frm, text="Precio:").grid(row=1, column=2, sticky="w")
        self.ent_precio = ttk.Entry(frm, width=15); self.ent_precio.grid(row=1, column=3, sticky="w")
        ttk.Label(frm, text="Stock:").grid(row=1, column=4, sticky="w")
        self.ent_stock = ttk.Entry(frm, width=10); self.ent_stock.grid(row=1, column=5, padx=6)

        ttk.Button(frm, text="Agregar/Actualizar", command=self.agregar_o_actualizar_producto).grid(row=0, column=6, rowspan=2, padx=8)
        ttk.Button(frm, text="Limpiar", command=self.limpiar_form_producto).grid(row=0, column=7, rowspan=2, padx=4)

        # Tabla productos
        cols = ("articulo","nombre","marca","precio","stock")
        self.tree_prod = ttk.Treeview(parent, columns=cols, show="headings", selectmode="browse", height=14)
        for c, t, w in [("articulo","Artículo",100),("nombre","Nombre",360),("marca","Marca",120),("precio","Precio",100),("stock","Stock",80)]:
            self.tree_prod.heading(c, text=t)
            self.tree_prod.column(c, width=w, anchor=("e" if c=="precio" else "w"))
        self.tree_prod.pack(fill="both", expand=True, padx=10, pady=10)
        self.tree_prod.bind("<Double-1>", self._cargar_producto_para_editar)

        # Botones acciones
        frm_actions = ttk.Frame(parent); frm_actions.pack(fill="x", padx=10, pady=(0,10))
        ttk.Button(frm_actions, text="Eliminar seleccionado", command=self.eliminar_producto).pack(side="left", padx=6)
        ttk.Button(frm_actions, text="Aplicar % por Marca", command=self._dialog_aplicar_porcentaje_marca).pack(side="left", padx=6)
        ttk.Button(frm_actions, text="Actualizar stock (seleccion)", command=self._dialog_actualizar_stock_seleccion).pack(side="left", padx=6)

        self._refresh_tree_prod()

    def limpiar_form_producto(self):
        self.ent_articulo.delete(0, tk.END)
        self.ent_nombre.delete(0, tk.END)
        self.ent_marca.delete(0, tk.END)
        self.ent_precio.delete(0, tk.END)
        self.ent_stock.delete(0, tk.END)

    def agregar_o_actualizar_producto(self):
        art = self.ent_articulo.get().strip()
        nombre = self.ent_nombre.get().strip()
        marca = self.ent_marca.get().strip()
        try:
            precio = float(self.ent_precio.get())
            stock = int(self.ent_stock.get())
        except Exception:
            messagebox.showerror("Error", "Precio o stock inválidos.")
            return
        if not art or not nombre or not marca:
            messagebox.showerror("Error", "Artículo, Nombre y Marca son obligatorios.")
            return
        # si existe artículo, actualizar
        existing = next((p for p in self.productos if p["articulo"]==art), None)
        if existing:
            existing.update({"nombre":nombre,"marca":marca,"precio":precio,"stock":stock})
            messagebox.showinfo("Actualizado", f"Producto {art} actualizado.")
        else:
            self.productos.append({"articulo":art,"nombre":nombre,"marca":marca,"precio":precio,"stock":stock})
            messagebox.showinfo("Agregado", f"Producto {art} agregado.")
        self.guardar_datos(); self._refresh_tree_prod(); self.limpiar_form_producto()
        # also refresh venta product lists
        self._refresh_productos_venta()

    def _cargar_producto_para_editar(self, event):
        sel = self.tree_prod.selection()
        if not sel: return
        vals = self.tree_prod.item(sel[0], "values")
        art = vals[0]
        p = next((x for x in self.productos if x["articulo"]==art), None)
        if not p: return
        self.ent_articulo.delete(0, tk.END); self.ent_articulo.insert(0, p["articulo"])
        self.ent_nombre.delete(0, tk.END); self.ent_nombre.insert(0, p["nombre"])
        self.ent_marca.delete(0, tk.END); self.ent_marca.insert(0, p["marca"])
        self.ent_precio.delete(0, tk.END); self.ent_precio.insert(0, f"{p['precio']:.2f}")
        self.ent_stock.delete(0, tk.END); self.ent_stock.insert(0, str(p["stock"]))

    def eliminar_producto(self):
        sel = self.tree_prod.selection()
        if not sel:
            messagebox.showwarning("Seleccionar", "Seleccione un producto para eliminar.")
            return
        vals = self.tree_prod.item(sel[0], "values")
        art = vals[0]
        if not messagebox.askyesno("Confirmar", f"Eliminar artículo {art}?"):
            return
        self.productos = [p for p in self.productos if p["articulo"]!=art]
        self.guardar_datos()
        self._refresh_tree_prod()
        self._refresh_productos_venta()

    def _dialog_aplicar_porcentaje_marca(self):
        marcas = sorted({p["marca"] for p in self.productos if p.get("marca")})
        if not marcas:
            messagebox.showinfo("Info", "No hay marcas cargadas.")
            return
        marca = simpledialog.askstring("Marca", "Ingrese marca:\n" + ", ".join(marcas))
        if not marca: return
        try:
            pct = float(simpledialog.askstring("Porcentaje", "Ingrese porcentaje (+ aumento, - rebaja)"))
        except Exception:
            return
        count = 0
        for p in self.productos:
            if p["marca"].lower()==marca.lower():
                p["precio"] = round(p["precio"]*(1.0 + pct/100.0), 2)
                count += 1
        self.guardar_datos(); self._refresh_tree_prod(); self._refresh_productos_venta()
        messagebox.showinfo("Listo", f"Aplicado {pct}% a {count} productos de {marca}.")

    def _dialog_actualizar_stock_seleccion(self):
        sel = self.tree_prod.selection()
        if not sel:
            messagebox.showwarning("Seleccionar", "Seleccione producto(s) para actualizar stock.")
            return
        # take first selected for prompt
        vals = self.tree_prod.item(sel[0], "values")
        art = vals[0]
        p = next((x for x in self.productos if x["articulo"]==art), None)
        if not p: return
        try:
            qty = int(simpledialog.askstring("Agregar Stock", f"Ingrese cantidad a sumar para {p['nombre']} (stock actual {p['stock']}):"))
        except Exception:
            messagebox.showerror("Error", "Cantidad inválida.")
            return
        p["stock"] += qty
        self.guardar_datos(); self._refresh_tree_prod(); self._refresh_productos_venta()
        messagebox.showinfo("OK", f"Stock actualizado: {p['stock']}")

    def _refresh_tree_prod(self):
        self.tree_prod.delete(*self.tree_prod.get_children())
        for p in self.productos:
            self.tree_prod.insert("", tk.END, values=(p["articulo"], p["nombre"], p["marca"], f"${p['precio']:.2f}", p["stock"]))

    # -------------------- UI Ventas --------------------
    def _ui_ventas(self, parent):
        # Cliente frame
        frm_cli = ttk.LabelFrame(parent, text="Datos del cliente", padding=8)
        frm_cli.pack(fill="x", padx=10, pady=6)
        ttk.Label(frm_cli, text="Nombre:*").grid(row=0, column=0, sticky="w")
        self.ent_cli_nombre = ttk.Entry(frm_cli, width=28); self.ent_cli_nombre.grid(row=0, column=1, padx=6)
        ttk.Label(frm_cli, text="DNI:*").grid(row=0, column=2, sticky="w")
        self.ent_cli_dni = ttk.Entry(frm_cli, width=18); self.ent_cli_dni.grid(row=0, column=3, padx=6)
        ttk.Label(frm_cli, text="Teléfono:").grid(row=0, column=4, sticky="w")
        self.ent_cli_tel = ttk.Entry(frm_cli, width=18); self.ent_cli_tel.grid(row=0, column=5, padx=6)

        # Buscar y autocompletado
        frm_find = ttk.Frame(parent); frm_find.pack(fill="x", padx=10, pady=6)
        ttk.Label(frm_find, text="Buscar producto (artículo o nombre):").pack(side="left")
        self.ent_buscar = ttk.Combobox(frm_find, width=60)
        self.ent_buscar.pack(side="left", padx=6)
        self.ent_buscar.bind("<KeyRelease>", self._on_type_filter_products)
        ttk.Button(frm_find, text="Agregar al carrito", command=self._agregar_seleccion_al_carrito).pack(side="left", padx=6)
        ttk.Button(frm_find, text="Limpiar lista búsqueda", command=self._refresh_productos_venta).pack(side="left", padx=6)

        # Carrito (productos a vender)
        frm_cart = ttk.LabelFrame(parent, text="Carrito - artículos para la venta (doble clic cantidad para editar)", padding=8)
        frm_cart.pack(fill="both", expand=False, padx=10, pady=6)
        cols = ("articulo","nombre","marca","precio_unit","cantidad","subtotal","stock")
        self.tree_cart = ttk.Treeview(frm_cart, columns=cols, show="headings", height=8, selectmode="extended")
        headings = [("articulo","Artículo"),("nombre","Nombre"),("marca","Marca"),("precio_unit","P.Unit."),("cantidad","Cant."),("subtotal","Subtotal"),("stock","Stock")]
        for c,h in headings:
            self.tree_cart.heading(c, text=h)
            self.tree_cart.column(c, width=(120 if c in ("articulo","precio_unit","cantidad","subtotal","stock") else 320), anchor="center" if c in ("precio_unit","cantidad","subtotal","stock") else "w")
        self.tree_cart.pack(fill="both", padx=6, pady=6)
        self.tree_cart.bind("<Double-1>", self._edit_cart_quantity)

        # Cart actions
        frm_cart_act = ttk.Frame(parent); frm_cart_act.pack(fill="x", padx=10, pady=(0,8))
        ttk.Button(frm_cart_act, text="Quitar ítem(s)", command=self._quitar_items_carrito).pack(side="left", padx=6)
        ttk.Button(frm_cart_act, text="Vaciar carrito", command=self._vaciar_carrito).pack(side="left", padx=6)

        # Registrar venta
        frm_sale = ttk.Frame(parent); frm_sale.pack(fill="x", padx=10, pady=6)
        ttk.Button(frm_sale, text="Registrar Venta", command=self._confirmar_registrar_venta).pack(side="left", padx=6)
        self.lbl_total = ttk.Label(frm_sale, text="Total: $0.00", font=("Arial", 12, "bold"))
        self.lbl_total.pack(side="right", padx=10)

        # Historial de ventas
        frm_hist = ttk.LabelFrame(parent, text="Historial de Ventas (líneas por artículo vendido)", padding=8)
        frm_hist.pack(fill="both", expand=True, padx=10, pady=6)
        cols_h = ("fecha","cliente","dni","articulo","nombre","marca","cantidad","total_line")
        self.tree_hist = ttk.Treeview(frm_hist, columns=cols_h, show="headings")
        headers = [("fecha","Fecha"),("cliente","Cliente"),("dni","DNI"),("articulo","Artículo"),("nombre","Producto"),("marca","Marca"),("cantidad","Cant."),("total_line","Total $")]
        for c,h in headers:
            self.tree_hist.heading(c, text=h); self.tree_hist.column(c, width=120 if c in ("fecha","dni","cantidad","total_line") else 200)
        self.tree_hist.pack(fill="both", expand=True)
        self._refresh_historial()

        # Reporte frame (fecha inicio/fin + generar)
        frm_report = ttk.LabelFrame(parent, text="Reporte por rango de fechas", padding=8)
        frm_report.pack(fill="x", padx=10, pady=6)
        ttk.Label(frm_report, text="Inicio (dd/mm/yyyy):").grid(row=0, column=0, sticky="w")
        self.ent_fi = ttk.Entry(frm_report, width=14); self.ent_fi.grid(row=0,column=1,padx=6)
        ttk.Label(frm_report, text="Fin (dd/mm/yyyy):").grid(row=0, column=2, sticky="w")
        self.ent_ff = ttk.Entry(frm_report, width=14); self.ent_ff.grid(row=0,column=3,padx=6)
        ttk.Button(frm_report, text="Generar Reporte", command=self._abrir_reporte_ventana).grid(row=0,column=4,padx=6)

        # initialize search combobox contents
        self._refresh_productos_venta()

    # -------------------- Productos -> Venta helpers --------------------
    def _refresh_productos_venta(self):
        # set combobox values to "articulo - nombre (marca)" strings
        vals = [f"{p['articulo']} - {p['nombre']} ({p['marca']})" for p in self.productos]
        self.ent_buscar['values'] = vals
        # clear cart product selection not necessary

    def _on_type_filter_products(self, event):
        text = self.ent_buscar.get().strip().lower()
        vals = []
        if text == "":
            vals = [f"{p['articulo']} - {p['nombre']} ({p['marca']})" for p in self.productos]
        else:
            for p in self.productos:
                if text in p['articulo'].lower() or text in p['nombre'].lower():
                    vals.append(f"{p['articulo']} - {p['nombre']} ({p['marca']})")
        self.ent_buscar['values'] = vals
        # optionally auto-open dropdown:
        try:
            self.ent_buscar.event_generate('<Down>')
        except Exception:
            pass

    def _agregar_seleccion_al_carrito(self):
        sel = self.ent_buscar.get().strip()
        if not sel:
            messagebox.showwarning("Seleccionar", "Seleccione un producto (escriba y elegí).")
            return
        # parse articulo
        art = sel.split(" - ")[0].strip()
        p = next((x for x in self.productos if x['articulo']==art), None)
        if not p:
            messagebox.showerror("Error", "Producto no encontrado.")
            return
        # ask quantity
        try:
            qty = simpledialog.askinteger("Cantidad", f"Ingrese cantidad para {p['nombre']} (stock {p['stock']}):", minvalue=1, maxvalue=p['stock'])
        except Exception:
            qty = None
        if not qty:
            return
        # if product already in cart, increase quantity
        for iid in self.tree_cart.get_children():
            vals = self.tree_cart.item(iid, "values")
            if vals[0] == p['articulo']:
                new_q = int(vals[4]) + qty
                if new_q > p['stock']:
                    messagebox.showerror("Error", "No hay stock suficiente para sumar esa cantidad.")
                    return
                subtotal = round(new_q * p['precio'], 2)
                self.tree_cart.item(iid, values=(p['articulo'], p['nombre'], p['marca'], f"${p['precio']:.2f}", new_q, f"${subtotal:.2f}", p['stock']))
                self._update_total_label()
                return
        # else add new line
        subtotal = round(qty * p['precio'], 2)
        self.tree_cart.insert("", tk.END, values=(p['articulo'], p['nombre'], p['marca'], f"${p['precio']:.2f}", qty, f"${subtotal:.2f}", p['stock']))
        self._update_total_label()

    def _edit_cart_quantity(self, event):
        # double-click a row -> prompt new quantity (with stock check)
        iid = self.tree_cart.identify_row(event.y)
        if not iid: return
        vals = self.tree_cart.item(iid, "values")
        articulo = vals[0]
        p = next((x for x in self.productos if x['articulo']==articulo), None)
        if not p: return
        try:
            current_q = int(vals[4])
        except:
            current_q = 0
        q = simpledialog.askinteger("Editar cantidad", f"Ingrese nueva cantidad para {p['nombre']} (stock {p['stock']}):", minvalue=0, maxvalue=p['stock'])
        if q is None:
            return
        if q == 0:
            # remove row
            self.tree_cart.delete(iid)
        else:
            subtotal = round(q * p['precio'], 2)
            self.tree_cart.item(iid, values=(p['articulo'], p['nombre'], p['marca'], f"${p['precio']:.2f}", q, f"${subtotal:.2f}", p['stock']))
        self._update_total_label()

    def _quitar_items_carrito(self):
        sel = self.tree_cart.selection()
        if not sel:
            messagebox.showwarning("Seleccionar", "Seleccione ítem(s) para quitar.")
            return
        for iid in sel:
            self.tree_cart.delete(iid)
        self._update_total_label()

    def _vaciar_carrito(self):
        if not self.tree_cart.get_children():
            return
        if not messagebox.askyesno("Confirmar", "Vaciar todo el carrito?"):
            return
        self.tree_cart.delete(*self.tree_cart.get_children())
        self._update_total_label()

    def _update_total_label(self):
        total = 0.0
        for iid in self.tree_cart.get_children():
            vals = self.tree_cart.item(iid, "values")
            # subtotal stored as string like '$12.50'
            try:
                subtotal = float(str(vals[5]).replace("$","").replace(",",""))
            except:
                subtotal = 0.0
            total += subtotal
        self.lbl_total.config(text=f"Total: ${total:.2f}")

    # -------------------- Registrar venta --------------------
    def _confirmar_registrar_venta(self):
        # validations
        nombre = self.ent_cli_nombre.get().strip()
        dni = self.ent_cli_dni.get().strip()
        tel = self.ent_cli_tel.get().strip()
        if not nombre:
            messagebox.showerror("Error", "El nombre del cliente es obligatorio.")
            return
        if not dni.isdigit():
            messagebox.showerror("Error", "DNI inválido (solo números).")
            return
        # build productos_vendidos
        items = []
        for iid in self.tree_cart.get_children():
            vals = self.tree_cart.item(iid, "values")
            articulo = vals[0]; nombre_p = vals[1]; marca = vals[2]
            cantidad = int(vals[4])
            precio_unit = float(str(vals[3]).replace("$",""))
            if cantidad <= 0:
                messagebox.showerror("Error", f"Cantidad inválida para {nombre_p}.")
                return
            # check stock again
            p = next((x for x in self.productos if x['articulo']==articulo), None)
            if not p or p['stock'] < cantidad:
                messagebox.showerror("Error", f"No hay stock suficiente para {nombre_p}.")
                return
            items.append({"articulo":articulo,"nombre":nombre_p,"marca":marca,"cantidad":cantidad,"precio":precio_unit})
        if not items:
            messagebox.showwarning("Carrito vacío", "No hay productos para vender.")
            return
        # confirm total
        total = sum(it["cantidad"]*it["precio"] for it in items)
        if not messagebox.askyesno("Confirmar venta", f"Registrar venta por ${total:.2f} para cliente {nombre}?"):
            return
        # apply stock update
        for it in items:
            p = next((x for x in self.productos if x['articulo']==it['articulo']), None)
            if p:
                p['stock'] -= it['cantidad']
        venta = {
            "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "cliente": nombre,
            "dni": dni,
            "tel": tel,
            "productos": items,
            "total": round(total,2)
        }
        self.ventas.append(venta)
        self.guardar_ventas()
        self.guardar_datos()
        # refresh UI
        self._refresh_productos_venta()
        self._refresh_tree_prod()
        self._refresh_historial()
        self.tree_cart.delete(*self.tree_cart.get_children())
        self._update_total_label()
        # clear client
        self.ent_cli_nombre.delete(0, tk.END); self.ent_cli_dni.delete(0, tk.END); self.ent_cli_tel.delete(0, tk.END)
        messagebox.showinfo("Venta registrada", f"Venta registrada por ${venta['total']:.2f}.")

    # -------------------- Historial --------------------
    def _refresh_historial(self):
        self.tree_hist.delete(*self.tree_hist.get_children())
        # each row = line item (venta x producto)
        for v in self.ventas:
            fecha = v.get("fecha","")
            cliente = v.get("cliente","")
            dni = v.get("dni","")
            for prod in v.get("productos", []):
                total_line = round(prod["precio"]*prod["cantidad"],2)
                self.tree_hist.insert("", tk.END, values=(fecha, cliente, dni, prod["articulo"], prod["nombre"], prod["marca"], prod["cantidad"], f"${total_line:.2f}"))

    # -------------------- Reporte --------------------
    def _abrir_reporte_ventana(self):
        fi = self.ent_fi.get().strip()
        ff = self.ent_ff.get().strip()
        try:
            fecha_inicio = datetime.strptime(fi, "%d/%m/%Y")
            fecha_fin = datetime.strptime(ff, "%d/%m/%Y")
        except Exception:
            messagebox.showerror("Error", "Formato de fecha inválido. Use dd/mm/yyyy")
            return

        ventas_filtradas = []
        total_gan = 0.0
        for v in self.ventas:
            try:
                fv = datetime.strptime(v["fecha"], "%d/%m/%Y %H:%M")
            except Exception:
                continue
            # compare by date (ignore time)
            if fecha_inicio <= fv.date() <= fecha_fin.date() if isinstance(fv, datetime) else False:
                ventas_filtradas.append(v)
                for prod in v.get("productos", []):
                    total_gan += prod["precio"]*prod["cantidad"]
        if not ventas_filtradas:
            messagebox.showinfo("Reporte", "No se encontraron ventas en ese período.")
            return

        # build report window
        w = tk.Toplevel(self.root)
        w.title(f"Reporte {fi} -> {ff}")
        w.geometry("1000x600")
        txt = tk.Text(w, wrap="none")
        txt.pack(fill="both", expand=True)
        # header
        header = f"{'Fecha':20} {'Cliente':20} {'DNI':10} {'Tel':12} {'Artículo':10} {'Producto':25} {'Marca':12} {'Cant':4} {'Total $':8}\n"
        txt.insert(tk.END, header)
        txt.insert(tk.END, "-"*140 + "\n")
        for v in ventas_filtradas:
            fecha = v["fecha"]; cliente = v["cliente"]; dni=v["dni"]; tel = v.get("tel","")
            for prod in v["productos"]:
                line_total = prod["precio"]*prod["cantidad"]
                txt.insert(tk.END, f"{fecha:20} {cliente:20} {dni:10} {tel:12} {prod['articulo']:10} {prod['nombre'][:25]:25} {prod['marca'][:12]:12} {prod['cantidad']:4} ${line_total:8.2f}\n")
        txt.insert(tk.END, "\nGanancia total periodo: ${:.2f}\n".format(total_gan))
        txt.config(state="disabled")

        # export buttons
        frm = ttk.Frame(w); frm.pack(pady=6)
        if Workbook:
            ttk.Button(frm, text="Exportar a Excel", command=lambda:self._exportar_excel_reporte(ventas_filtradas)).pack(side="left", padx=6)
        else:
            ttk.Button(frm, text="Exportar a Excel (openpyxl falta)", state="disabled").pack(side="left", padx=6)
        if SimpleDocTemplate:
            ttk.Button(frm, text="Exportar a PDF", command=lambda:self._exportar_pdf_reporte(ventas_filtradas)).pack(side="left", padx=6)
        else:
            ttk.Button(frm, text="Exportar a PDF (reportlab falta)", state="disabled").pack(side="left", padx=6)

    def _exportar_excel_reporte(self, ventas_filtradas):
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files","*.xlsx")], initialfile="reporte_ventas.xlsx")
        if not path: return
        try:
            wb = Workbook(); ws = wb.active; ws.title = "Reporte Ventas"
            ws.append(["Fecha","Cliente","DNI","Tel","Artículo","Producto","Marca","Cantidad","Total"])
            for v in ventas_filtradas:
                for prod in v["productos"]:
                    ws.append([v["fecha"], v["cliente"], v["dni"], v.get("tel",""), prod["articulo"], prod["nombre"], prod["marca"], prod["cantidad"], prod["precio"]*prod["cantidad"]])
            wb.save(path)
            messagebox.showinfo("Exportado", f"Reporte guardado en {path}")
        except Exception as e:
            messagebox.showerror("Error exportando", str(e))

    def _exportar_pdf_reporte(self, ventas_filtradas):
        path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files","*.pdf")], initialfile="reporte_ventas.pdf")
        if not path: return
        try:
            doc = SimpleDocTemplate(path, pagesize=A4)
            elements = []
            styles = getSampleStyleSheet()
            elements.append(Paragraph("Reporte de Ventas", styles["Title"]))
            elements.append(Spacer(1,12))
            data = [["Fecha","Cliente","DNI","Tel","Artículo","Producto","Marca","Cantidad","Total"]]
            for v in ventas_filtradas:
                for prod in v["productos"]:
                    data.append([v["fecha"], v["cliente"], v["dni"], v.get("tel",""), prod["articulo"], prod["nombre"], prod["marca"], str(prod["cantidad"]), f"{prod['precio']*prod['cantidad']:.2f}"])
            table = Table(data, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND',(0,0),(-1,0),colors.gray),
                ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
                ('GRID',(0,0),(-1,-1),0.4,colors.black),
                ('FONTSIZE',(0,0),(-1,-1),8),
            ]))
            elements.append(table)
            doc.build(elements)
            messagebox.showinfo("Exportado", f"PDF guardado en {path}")
        except Exception as e:
            messagebox.showerror("Error exportando PDF", str(e))

# -------------------- RUN --------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = GestorRopaInterior(root)
    root.mainloop()
