"""
Interfaz Gráfica de Usuario (GUI) para PdfSign.
Utiliza tkinter (nativo en Python) para crear un formulario de firma.
"""

import os
import sys
import json
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID

# Cambia esto:
from pdfsign import sign_pdf, analyze_pdf

# Por esto:
from pdfsign import sign_pdf, analyze_pdf, __version__

class PdfSignApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"PdfSign - Firma Digital de Documentos (v{__version__})")
        self.root.geometry("850x750")
        self.root.resizable(True, False) 
        
        self.config_file = "gui_settings.json"
        self.last_paths = self.load_settings()
        self.last_signed_pdf = None

        self.create_widgets()

    def load_settings(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    return json.load(f)
            except:
                pass
        
        cwd = os.getcwd()
        return {"pdf_dir": cwd, "cert_dir": cwd, "out_dir": cwd}

    def save_settings(self):
        with open(self.config_file, "w") as f:
            json.dump(self.last_paths, f)

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="20 20 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        main_frame.columnconfigure(1, weight=1)

        # 1. Documento PDF
        ttk.Label(main_frame, text="Documento PDF original:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.pdf_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.pdf_var).grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Button(main_frame, text="Buscar", command=self.browse_pdf).grid(row=0, column=2, sticky=tk.E)

        # Panel de información del PDF original (AHORA CON CAJA DE TEXTO SELECCIONABLE)
        self.info_frame = ttk.LabelFrame(main_frame, text="Estado del Documento Original", padding="10 10 10 10")
        self.info_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=10)
        
        self.info_text = tk.Text(self.info_frame, height=8, wrap=tk.WORD, bg="#f9f9f9", relief="flat")
        self.info_text.pack(fill=tk.BOTH, expand=True)
        self.set_text_content(self.info_text, "Selecciona un PDF para analizar sus firmas previas.")

        # 2. Certificado
        ttk.Label(main_frame, text="Certificado (.p12/.pfx):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.cert_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.cert_var).grid(row=2, column=1, sticky="ew", padx=5)
        ttk.Button(main_frame, text="Buscar", command=self.browse_cert).grid(row=2, column=2, sticky=tk.E)

        # 3. Contraseña con botón de Ver
        ttk.Label(main_frame, text="Contraseña del certificado:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.pass_var = tk.StringVar()
        self.pass_entry = ttk.Entry(main_frame, textvariable=self.pass_var, show="*")
        self.pass_entry.grid(row=3, column=1, sticky="ew", padx=5)
        
        self.show_pass_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            main_frame, 
            text="👁️ Ver", 
            variable=self.show_pass_var,
            command=self.toggle_password
        ).grid(row=3, column=2, sticky=tk.W)

        # 4. Tipo de Firma
        self.invisible_var = tk.BooleanVar(value=False)
        chk_invisible = ttk.Checkbutton(
            main_frame, 
            text="Firma invisible (sin sello gráfico)", 
            variable=self.invisible_var,
            command=self.toggle_reason_state
        )
        chk_invisible.grid(row=4, column=1, sticky=tk.W, pady=10)

        # 5. Motivo del Visado
        ttk.Label(main_frame, text="Motivo del Visado:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.reason_var = tk.StringVar(value="Visado")
        self.combo_reason = ttk.Combobox(
            main_frame, 
            textvariable=self.reason_var, 
            values=["Aprobado", "Visado", "Revisado", "Rechazado"],
            state="readonly"
        )
        self.combo_reason.grid(row=5, column=1, sticky="ew", padx=5)

        # 6. Archivo de Salida
        ttk.Label(main_frame, text="Guardar firmado como:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.out_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.out_var).grid(row=6, column=1, sticky="ew", padx=5)
        ttk.Button(main_frame, text="Guardar en...", command=self.browse_output).grid(row=6, column=2, sticky=tk.E)

        ttk.Separator(main_frame, orient=tk.HORIZONTAL).grid(row=7, column=0, columnspan=3, sticky="ew", pady=15)

        # 7. Botón Principal
        self.btn_sign = ttk.Button(main_frame, text="Firmar Documento", command=self.execute_signature)
        self.btn_sign.grid(row=8, column=1, pady=5)

        # 8. PANEL DE RESULTADO (AHORA CON CAJA DE TEXTO SELECCIONABLE)
        self.post_action_frame = ttk.LabelFrame(main_frame, text="Resultado del Documento Generado", padding="10 10 10 10")
        self.post_action_frame.grid(row=9, column=0, columnspan=3, sticky="ew", pady=10)
        self.post_action_frame.grid_remove() 
        
        self.output_info_text = tk.Text(self.post_action_frame, height=8, wrap=tk.WORD, bg="#f9f9f9", relief="flat")
        self.output_info_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.buttons_frame = ttk.Frame(self.post_action_frame)
        self.buttons_frame.pack(anchor=tk.CENTER)
        
        self.btn_view = ttk.Button(self.buttons_frame, text="👁️ Ver PDF Firmado", command=self.open_pdf)
        self.btn_delete = ttk.Button(self.buttons_frame, text="🗑️ Descartar y Borrar", command=self.delete_pdf)
        self.btn_new = ttk.Button(self.buttons_frame, text="📄 Nuevo Documento", command=self.reset_form)

    # --- Función Helper para actualizar las cajas de texto ---
    def set_text_content(self, text_widget, content):
        """Actualiza el contenido de un widget Text de forma segura."""
        text_widget.configure(state="normal")
        text_widget.delete("1.0", tk.END)
        text_widget.insert(tk.END, content)
        text_widget.configure(state="disabled")

    # --- Funciones de Comportamiento Visual ---
    def toggle_password(self):
        if self.show_pass_var.get():
            self.pass_entry.configure(show="")
        else:
            self.pass_entry.configure(show="*")

    def toggle_reason_state(self):
        if self.invisible_var.get():
            self.combo_reason.configure(state="disabled")
        else:
            self.combo_reason.configure(state="readonly")

    # --- Funciones de Navegación e Inspección ---
    def browse_pdf(self):
        filepath = filedialog.askopenfilename(
            initialdir=self.last_paths["pdf_dir"],
            title="Selecciona el PDF a firmar",
            filetypes=(("Archivos PDF", "*.pdf"), ("Todos los archivos", "*.*"))
        )
        if filepath:
            self.pdf_var.set(filepath)
            self.last_paths["pdf_dir"] = os.path.dirname(filepath)
            self.save_settings()
            
            if not self.out_var.get():
                nombre_base = os.path.splitext(filepath)[0]
                self.out_var.set(f"{nombre_base}_firmado.pdf")
                self.last_paths["out_dir"] = os.path.dirname(filepath)
                
            self.analyze_selected_pdf(filepath)

    # --- Función para limpiar la fecha bruta del PDF ---
    def format_pdf_date(self, raw_date):
        """Formatea la fecha bruta del PDF (ej. b'D:20261002083434Z') a algo legible."""
        if not raw_date or raw_date == 'No disponible':
            return 'Fecha no disponible'
        
        # Limpiamos los prefijos binarios de PDF
        clean_date = str(raw_date).replace("b'", "").replace("'", "").replace("D:", "")
        
        if len(clean_date) >= 14:
            try:
                # Extraemos YYYYMMDDHHMMSS
                yyyy = clean_date[0:4]
                mm = clean_date[4:6]
                dd = clean_date[6:8]
                hh = clean_date[8:10]
                minu = clean_date[10:12]
                ss = clean_date[12:14]
                return f"{dd}/{mm}/{yyyy} {hh}:{minu}:{ss}"
            except Exception:
                pass
        return clean_date

    # --- Funciones de Inspección Modificadas ---
    def analyze_selected_pdf(self, filepath):
        self.set_text_content(self.info_text, "⏳ Analizando documento original...")
        self.root.update()
        
        try:
            resultado = json.loads(analyze_pdf(filepath))
            if resultado["status"] == "error":
                self.set_text_content(self.info_text, f"❌ Error al leer PDF: {resultado['message']}")
                return
                
            firmas = resultado["data"]["signatures"]
            if not firmas:
                self.set_text_content(self.info_text, "ℹ El documento es original (0 firmas previas).")
            else:
                texto = f"✅ Contiene {len(firmas)} firma(s):\n"
                for i, f in enumerate(firmas, 1):
                    estado = "Íntegra" if f['is_intact'] else "Rota"
                    
                    # Leemos la clave correcta que genera pdf.py
                    fecha_bruta = f.get('signature_date', 'No disponible')
                    fecha_limpia = self.format_pdf_date(fecha_bruta)
                    
                    texto += f"  [{i}] {f['signer_name']}\n      📅 Fecha: {fecha_limpia} | Estado: {estado}\n\n"
                self.set_text_content(self.info_text, texto.strip())
        except Exception:
            self.set_text_content(self.info_text, "⚠️ No se pudo analizar el estado de las firmas.")

    def analyze_output_pdf(self, filepath):
        try:
            resultado = json.loads(analyze_pdf(filepath))
            if resultado["status"] == "error":
                self.set_text_content(self.output_info_text, f"❌ Error al leer PDF generado: {resultado['message']}")
                return
                
            firmas = resultado["data"]["signatures"]
            texto = f"✅ El nuevo documento contiene {len(firmas)} firma(s) en total:\n"
            for i, f in enumerate(firmas, 1):
                estado = "Íntegra" if f['is_intact'] else "Rota"
                
                # Leemos la clave correcta que genera pdf.py
                fecha_bruta = f.get('signature_date', 'No disponible')
                fecha_limpia = self.format_pdf_date(fecha_bruta)
                
                texto += f"  [{i}] {f['signer_name']}\n      📅 Fecha: {fecha_limpia} | Estado: {estado}\n\n"
            self.set_text_content(self.output_info_text, texto.strip())
        except Exception:
            self.set_text_content(self.output_info_text, "⚠️ No se pudo analizar el documento generado.")

    def browse_cert(self):
        filepath = filedialog.askopenfilename(
            initialdir=self.last_paths["cert_dir"],
            title="Selecciona tu certificado",
            filetypes=(("Certificados", "*.p12 *.pfx"), ("Todos los archivos", "*.*"))
        )
        if filepath:
            self.cert_var.set(filepath)
            self.last_paths["cert_dir"] = os.path.dirname(filepath)
            self.save_settings()

    def browse_output(self):
        filepath = filedialog.asksaveasfilename(
            initialdir=self.last_paths["out_dir"],
            title="Guardar PDF firmado",
            defaultextension=".pdf",
            filetypes=(("Archivos PDF", "*.pdf"),)
        )
        if filepath:
            self.out_var.set(filepath)
            self.last_paths["out_dir"] = os.path.dirname(filepath)
            self.save_settings()

    # --- Lógica de Firma y Control de Duplicados ---
    def execute_signature(self):
        pdf_path = self.pdf_var.get()
        cert_path = self.cert_var.get()
        password = self.pass_var.get()
        out_path = self.out_var.get()

        if not pdf_path or not cert_path or not out_path:
            messagebox.showwarning("Campos incompletos", "Por favor, rellena las rutas del PDF, certificado y destino.")
            return

        # --- CONTROL DE FIRMAS DUPLICADAS ---
        cert_cn = None
        try:
            password_bytes = password.encode('utf-8') if password else b''
            with open(cert_path, "rb") as f:
                p12_data = f.read()
            _, certificate, _ = pkcs12.load_key_and_certificates(p12_data, password_bytes)
            cn_attributes = certificate.subject.get_attributes_for_oid(NameOID.COMMON_NAME)
            cert_cn = cn_attributes[0].value if cn_attributes else "Firmante Desconocido"
        except Exception:
            pass

        if cert_cn:
            try:
                analisis = json.loads(analyze_pdf(pdf_path))
                if analisis["status"] == "success":
                    firmas_previas = [f["signer_name"] for f in analisis["data"]["signatures"]]
                    
                    # CORRECCIÓN: Comprobamos si cert_cn es una subcadena de alguna firma previa
                    ya_firmado = any(cert_cn in firma for firma in firmas_previas)
                    
                    if ya_firmado:
                        confirm = messagebox.askyesno(
                            "Firma duplicada", 
                            f"Este documento ya contiene una firma a nombre de:\n{cert_cn}\n\n¿Estás seguro de que quieres firmarlo otra vez?"
                        )
                        if not confirm:
                            return 
            except Exception:
                pass
        # ------------------------------------

        self.btn_sign.configure(text="Firmando...", state="disabled")
        self.root.update()

        resultado = json.loads(sign_pdf(
            input_pdf=pdf_path,
            cert_path=cert_path,
            password=password,
            output_pdf=out_path,
            reason=self.reason_var.get(),
            invisible=self.invisible_var.get()
        ))
        
        self.btn_sign.configure(text="Firmar Documento", state="normal")

        if resultado["status"] == "success":
            self.last_signed_pdf = out_path
            messagebox.showinfo("Éxito", f"Documento firmado correctamente por:\n{resultado['data']['signer_name']}")
            
            self.analyze_output_pdf(self.last_signed_pdf)
            self.post_action_frame.grid() 
            self.btn_view.pack(side=tk.LEFT, padx=5)
            self.btn_delete.pack(side=tk.LEFT, padx=5)
            self.btn_new.pack(side=tk.LEFT, padx=5)
        else:
            messagebox.showerror("Error al firmar", resultado["message"])

    def open_pdf(self):
        if not self.last_signed_pdf or not os.path.exists(self.last_signed_pdf):
            return
        try:
            if sys.platform == "win32":
                os.startfile(self.last_signed_pdf)
            elif sys.platform == "darwin":
                subprocess.call(["open", self.last_signed_pdf])
            else:
                subprocess.call(["xdg-open", self.last_signed_pdf])
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el archivo: {e}")

    def delete_pdf(self):
        if not self.last_signed_pdf or not os.path.exists(self.last_signed_pdf):
            return
        confirm = messagebox.askyesno("Borrar documento", f"¿Estás seguro de que deseas borrar el archivo generado?\n\n{self.last_signed_pdf}")
        if confirm:
            try:
                os.remove(self.last_signed_pdf)
                messagebox.showinfo("Borrado", "El documento firmado ha sido eliminado.")
                self.reset_form()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo borrar el archivo: {e}")

    def reset_form(self):
        self.pdf_var.set("")
        self.out_var.set("")
        self.pass_var.set("")
        self.set_text_content(self.info_text, "Selecciona un PDF para analizar sus firmas previas.")
        
        self.post_action_frame.grid_remove()
        self.last_signed_pdf = None

if __name__ == "__main__":
    root = tk.Tk()
    app = PdfSignApp(root)
    root.mainloop()