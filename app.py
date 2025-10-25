import os
import sys
import sqlite3
from datetime import datetime, timedelta

import threading
import tempfile
import math

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from db import init_db, add_record, get_records, update_record, delete_record

# Try to import Pillow for image support; if not present, we'll skip logo
try:
	from PIL import Image, ImageTk
	_HAS_PIL = True
except Exception:
	_HAS_PIL = False


# Handle both normal Python execution and PyInstaller frozen executable
if getattr(sys, 'frozen', False):
	# Running as compiled executable (PyInstaller)
	application_path = os.path.dirname(sys.executable)
else:
	# Running as normal Python script
	application_path = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(application_path, "data.db")



class App:
	def __init__(self, root):
		self.root = root
		self.root.title("1. NSH Izgara Kesim Kayitlari")
		self.root.geometry("760x520")

		init_db(DB_PATH)

		frm = ttk.Frame(root, padding=10)
		frm.pack(fill=tk.BOTH, expand=True)

		# Top area: logo (if exists) on left and input area on right
		top_frame = ttk.Frame(frm)
		top_frame.pack(fill=tk.X, padx=5, pady=5)

		logo_label = ttk.Label(top_frame)
		logo_label.pack(side=tk.LEFT, padx=(0, 8))
		# Try to load logo.png from app dir
		logo_path = os.path.join(application_path, "logo.png")
		if _HAS_PIL and os.path.exists(logo_path):
			try:
				img = Image.open(logo_path)
				# Resize to fit into UI nicely
				img.thumbnail((120, 80), Image.LANCZOS)
				self._logo_img = ImageTk.PhotoImage(img)
				logo_label.configure(image=self._logo_img)
			except Exception:
				logo_label.configure(text="[Logo]")
		else:
			# If no PIL or no logo file, show a small text placeholder
			logo_label.configure(text="[Logo]")

		# Input area
		input_frame = ttk.LabelFrame(top_frame, text="Yeni Kayit")
		input_frame.pack(fill=tk.X, expand=True, side=tk.LEFT)

		ttk.Label(input_frame, text="Boy (m):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
		self.len_var = tk.StringVar()
		self.len_entry = ttk.Entry(input_frame, textvariable=self.len_var, width=12)
		self.len_entry.grid(row=0, column=1, padx=5, pady=5)

		ttk.Label(input_frame, text="Tampon: ").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
		self.buf_var = tk.StringVar(value="Sabit")
		self.buf_combo = ttk.Combobox(input_frame, textvariable=self.buf_var, values=["Sabit", "Hareketli"], state="readonly", width=12)
		self.buf_combo.grid(row=0, column=3, padx=5, pady=5)

		self.add_btn = ttk.Button(input_frame, text="Ekle", command=self.on_add)
		self.add_btn.grid(row=0, column=4, padx=8)

		self.cancel_btn = ttk.Button(input_frame, text="Iptal", command=self.cancel_edit, state="disabled")
		self.cancel_btn.grid(row=0, column=5, padx=8)

		refresh_btn = ttk.Button(input_frame, text="Yenile", command=self.refresh_list)
		refresh_btn.grid(row=0, column=6, padx=8)

		# allow pressing Enter to submit add/update
		self.editing_id = None
		self.len_entry.bind('<Return>', self.on_add)
		# bind Enter on tampon combobox too
		self.buf_combo.bind('<Return>', self.on_add)

		# Group selector (Hepsi, 5..10, Diger)
		ttk.Label(input_frame, text="Grup:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
		self.group_var = tk.StringVar(value="Hepsi")
		self.group_combo = ttk.Combobox(input_frame, textvariable=self.group_var, values=["Hepsi","5","6","7","8","9","10","Diger"], state="readonly", width=10)
		self.group_combo.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
		self.group_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_list())

		# Treeview
		cols = ("id", "boy", "tampon", "tarih")
		self.tree = ttk.Treeview(frm, columns=cols, show="headings", selectmode="browse")
		self.tree.heading("id", text="ID")
		self.tree.heading("boy", text="Boy (m)")
		self.tree.heading("tampon", text="Tampon")
		self.tree.heading("tarih", text="Tarih/Saat")
		self.tree.column("id", width=40, anchor=tk.CENTER)
		self.tree.column("boy", width=120, anchor=tk.CENTER)
		self.tree.column("tampon", width=120, anchor=tk.CENTER)
		self.tree.column("tarih", width=200, anchor=tk.CENTER)
		self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

		# double-click on tree row to edit
		self.tree.bind('<Double-1>', self.on_tree_double_click)
		# single click on empty area to cancel editing
		self.tree.bind('<Button-1>', self.on_tree_click)

		# Export buttons
		export_frame = ttk.Frame(frm)
		export_frame.pack(fill=tk.X, padx=5, pady=5)
		ex_xlsx = ttk.Button(export_frame, text="Excel olarak disa aktar (.xlsx)", command=self.export_excel)
		ex_xlsx.pack(side=tk.LEFT, padx=5)
		ex_pdf = ttk.Button(export_frame, text="PDF olarak disa aktar (.pdf)", command=self.export_pdf)
		ex_pdf.pack(side=tk.LEFT, padx=5)
		
		delete_btn = ttk.Button(export_frame, text="Secili satiri sil", command=self.delete_selected)
		delete_btn.pack(side=tk.LEFT, padx=5)

		# blinking state
		self.blink_items = {}  # item_id -> stop_time
		self._blink_running = False

		self.refresh_list()

		# Footer with author at bottom-right
		bottom_frame = ttk.Frame(frm)
		bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)
		footer = ttk.Label(bottom_frame, text="Selim Tasdemir")
		footer.pack(side=tk.RIGHT, padx=8, pady=4)

	def on_add(self, event=None):
		val = self.len_var.get().strip()
		if not val:
			messagebox.showwarning("Eksik", "Lutfen bir boy girin.")
			return
		try:
			# accept comma as decimal separator
			val_norm = val.replace(',', '.')
			boya = round(float(val_norm), 2)
		except ValueError:
			messagebox.showerror("Hata", "Boy sayisal olmalidir.")
			return
		tampon = self.buf_var.get()
		if self.editing_id is None:
			add_record(DB_PATH, boya, tampon)
		else:
			try:
				update_record(DB_PATH, int(self.editing_id), boya, tampon)
			except Exception as e:
				messagebox.showerror("Hata", f"Guncelleme sirasinda hata: {e}")
			# reset editing state
			self.editing_id = None
			self.add_btn.configure(text="Ekle")
			self.cancel_btn.configure(state="disabled")
		self.len_var.set("")
		self.refresh_list()

	def cancel_edit(self):
		"""Cancel editing mode and clear inputs"""
		self.editing_id = None
		self.add_btn.configure(text="Ekle")
		self.cancel_btn.configure(state="disabled")
		self.len_var.set("")
		self.tree.selection_remove(self.tree.selection())

	def on_tree_click(self, event):
		"""Handle single click on tree - cancel edit if clicking empty area"""
		row_id = self.tree.identify_row(event.y)
		if not row_id and self.editing_id is not None:
			# Clicked on empty area while editing - cancel
			self.cancel_edit()

	def on_tree_double_click(self, event):
		# identify row under mouse, populate inputs for editing
		row_id = self.tree.identify_row(event.y)
		if not row_id:
			return
		vals = self.tree.item(row_id, 'values')
		if not vals:
			return
		record_id = vals[0]
		boy_val = vals[1]
		tampon_val = vals[2]
		# populate fields
		self.len_var.set(str(boy_val))
		self.buf_var.set(tampon_val)
		self.editing_id = record_id
		self.add_btn.configure(text="Guncelle")
		self.cancel_btn.configure(state="normal")
		self.len_entry.focus_set()

	def delete_selected(self):
		"""Delete the selected row from database"""
		selected = self.tree.selection()
		if not selected:
			messagebox.showwarning("Secim Yok", "Lutfen silmek icin bir satir secin.")
			return
		
		vals = self.tree.item(selected[0], 'values')
		if not vals:
			return
		
		record_id = vals[0]
		boy_val = vals[1]
		
		# Confirm deletion
		confirm = messagebox.askyesno(
			"Silme Onay", 
			f"'{boy_val} m' kaydini silmek istediginizden emin misiniz?"
		)
		
		if confirm:
			try:
				delete_record(DB_PATH, int(record_id))
				# If we're editing this record, cancel edit mode
				if self.editing_id == record_id:
					self.cancel_edit()
				else:
					self.refresh_list()
				messagebox.showinfo("Basarili", "Kayit silindi.")
			except Exception as e:
				messagebox.showerror("Hata", f"Silme sirasinda hata: {e}")

	def refresh_list(self):
		for r in self.tree.get_children():
			self.tree.delete(r)
		rows = get_records(DB_PATH)
		now = datetime.utcnow()
		for row in rows:
			rid, boya, tampon, created_at = row
			dt = datetime.fromisoformat(created_at)
			disp = dt.strftime("%Y-%m-%d %H:%M:%S")
			# grouping: integer part of meters
			group_int = int(math.floor(boya))
			sel = self.group_var.get() if hasattr(self, 'group_var') else 'Hepsi'
			if sel != 'Hepsi':
				if sel == 'Diger':
					if 5 <= group_int <= 10:
						continue
				else:
					try:
						if group_int != int(sel):
							continue
					except Exception:
						pass
			# format boya to 2 decimals for display
			boy_display = f"{boya:.2f}"
			item = self.tree.insert("", tk.END, values=(rid, boy_display, tampon, disp))
			# if created within 24 hours, mark to blink
			if now - dt <= timedelta(hours=24):
				stop_time = dt + timedelta(hours=24)
				self.blink_items[item] = stop_time
		if not self._blink_running and self.blink_items:
			self._blink_running = True
			self._blink_loop()

	def _blink_loop(self):
		# Toggle background for items still within their 24h window
		now = datetime.utcnow()
		to_remove = []
		for item, stop in list(self.blink_items.items()):
			if now >= stop:
				# remove blinking
				try:
					self.tree.item(item, tags=())
					self.tree.tag_configure(item, background="")
				except Exception:
					pass
				to_remove.append(item)
		for r in to_remove:
			del self.blink_items[r]
		# apply alternating color for remaining
		# use a simple yellow/white alternation
		toggle = getattr(self, "_blink_toggle", False)
		color = "#fff59d" if toggle else ""
		for item in self.blink_items.keys():
			try:
				self.tree.tag_configure(item, background=color)
				self.tree.item(item, tags=(item,))
			except Exception:
				pass
		self._blink_toggle = not toggle
		if self.blink_items:
			# schedule next blink
			self.root.after(700, self._blink_loop)
		else:
			self._blink_running = False

	def export_excel(self):
		df = pd.read_sql_query("SELECT id, boy, tampon, created_at FROM records ORDER BY created_at ASC", sqlite3.connect(DB_PATH))
		if df.empty:
			messagebox.showinfo("Bos", "Disa aktarilacak kayit yok.")
			return
		# format boy column to 2 decimals
		df['boy'] = df['boy'].map(lambda x: round(float(x), 2))
		default = datetime.now().strftime("kesimler_%Y%m%d_%H%M%S.xlsx")
		path = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=default, filetypes=[("Excel", "*.xlsx")])
		if not path:
			return
		try:
			df.to_excel(path, index=False)
			messagebox.showinfo("Tamam", f"Excel dosyasi olusturuldu:\n{path}")
		except Exception as e:
			messagebox.showerror("Hata", f"Excel disa aktarilirken hata: {e}")

	def export_pdf(self):
		# read DB into dataframe
		df = pd.read_sql_query("SELECT id, boy, tampon, created_at FROM records ORDER BY created_at ASC", sqlite3.connect(DB_PATH))
		if df.empty:
			messagebox.showinfo("Bos", "Disa aktarilacak kayit yok.")
			return
		# format boy column to 2 decimals as strings for PDF
		df['boy'] = df['boy'].map(lambda x: f"{float(x):.2f}")
		default = datetime.now().strftime("kesimler_%Y%m%d_%H%M%S.pdf")
		path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=default, filetypes=[("PDF", "*.pdf")])
		if not path:
			return
		try:
			data = [list(df.columns)] + df.values.tolist()
			doc = SimpleDocTemplate(path, pagesize=landscape(A4))
			table = Table(data)
			style = TableStyle([
				("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
				("GRID", (0, 0), (-1, -1), 0.5, colors.black),
				("ALIGN", (0, 0), (-1, -1), "CENTER"),
			])
			table.setStyle(style)
			doc.build([table])
			messagebox.showinfo("Tamam", f"PDF olusturuldu:\n{path}")
		except Exception as e:
			messagebox.showerror("Hata", f"PDF disa aktarilirken hata: {e}")


def main():
	root = tk.Tk()
	app = App(root)
	root.mainloop()


if __name__ == "__main__":
	main()