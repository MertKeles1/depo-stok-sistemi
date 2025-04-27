import os
import sys
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

class DepoStokSistemi:
    def __init__(self, root):
        self.root = root
        self.root.title("Depo Stok Yönetim Sistemi")
        self.root.geometry("1000x600")
        self.root.resizable(False, False)
        
        # Uygulama dizini ve veritabanı yolunu belirle
        if getattr(sys, 'frozen', False):
            # PyInstaller ile paketlenmiş uygulama için
            self.application_path = os.path.dirname(sys.executable)
        else:
            # Normal Python betiği için
            self.application_path = os.path.dirname(os.path.abspath(__file__))
        
        self.db_path = os.path.join(self.application_path, "depo_stok.db")
        
        # Veritabanı bağlantısını oluştur
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

                # Tema ve renk ayarları
        self.style = ttk.Style()
        self.style.theme_use('clam')  # 'clam', 'alt', 'default', 'classic' temalarından birini kullanabilirsiniz
        
        # Ana renkler
        self.primary_color = "#4a6984"  # Koyu mavi/gri
        self.secondary_color = "#f0f0f0"  # Açık gri
        self.accent_color = "#2e8b57"  # Deniz yeşili
        self.warning_color = "#e74c3c"  # Kırmızı
        
        # Tabloları oluştur
        self.tablolari_olustur()
        
        # Ana çerçeve oluştur
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Sekmeleri oluştur
        self.stok_sekmesi_olustur()
        self.urun_ekle_sekmesi_olustur()
        self.satis_sekmesi_olustur()
        self.musteri_bilgileri_sekmesi_olustur()
        self.raporlar_sekmesi_olustur()
        
        # Uygulama kapanırken veritabanı bağlantısını kapat
        self.root.protocol("WM_DELETE_WINDOW", self.kapat)
    
    def tablolari_olustur(self):
        # Ürünler tablosunu oluştur
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS urunler (
            id INTEGER PRIMARY KEY,
            urun_kodu TEXT UNIQUE,
            urun_adi TEXT,
            kategori TEXT,
            birim_fiyat REAL,
            stok_miktari INTEGER,
            eklenme_tarihi TEXT
        )
        """)
        
        # Satışlar tablosunu oluştur
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS satislar (
            id INTEGER PRIMARY KEY,
            urun_id INTEGER,
            miktar INTEGER,
            satis_tarihi TEXT,
            musteri_adi TEXT,
            musteri_soyadi TEXT,
            musteri_telefon TEXT,
            FOREIGN KEY (urun_id) REFERENCES urunler (id)
        )
        """)
        
        # Veritabanı boşsa örnek veriler ekle
        self.veritabani_ilk_kurulum_yap()
        
        self.conn.commit()

    def veritabani_ilk_kurulum_yap(self):
        # Veritabanında hiç ürün yoksa demo veriler ekle
        self.cursor.execute("SELECT COUNT(*) FROM urunler")
        urun_sayisi = self.cursor.fetchone()[0]
        
        if urun_sayisi == 0:
            # Demo ürünler ekle
            urunler = [
                ('URN001', 'Samsung Galaxy S21', 'Telefon', 8999.99, 10, self.turkce_tarih()),
                ('URN002', 'Apple iPhone 13', 'Telefon', 14999.99, 5, self.turkce_tarih()),
                ('URN003', 'Lenovo ThinkPad X1', 'Bilgisayar', 19999.99, 3, self.turkce_tarih()),
                ('URN004', 'Sony 55" 4K TV', 'Televizyon', 12499.99, 7, self.turkce_tarih()),
                ('URN005', 'Bosch Bulaşık Makinesi', 'Beyaz Eşya', 7999.99, 4, self.turkce_tarih())
            ]
            
            self.cursor.executemany("""
            INSERT INTO urunler (urun_kodu, urun_adi, kategori, birim_fiyat, stok_miktari, eklenme_tarihi)
            VALUES (?, ?, ?, ?, ?, ?)
            """, urunler)
            
            self.conn.commit()

    def turkce_tarih(self):
        ay_isimleri = {
            1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan",
            5: "Mayıs", 6: "Haziran", 7: "Temmuz", 8: "Ağustos",
            9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"
        }
        bugun = datetime.now()
        return f"{bugun.day} {ay_isimleri[bugun.month]} {bugun.year} {bugun.hour:02d}:{bugun.minute:02d}:{bugun.second:02d}"
    
    def stok_sekmesi_olustur(self):
        stok_frame = ttk.Frame(self.notebook)
        self.notebook.add(stok_frame, text="Stok Durumu")
        
        # Arama çerçevesi
        arama_frame = ttk.Frame(stok_frame)
        arama_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(arama_frame, text="Ürün Ara:").pack(side=tk.LEFT, padx=5)
        self.arama_entry = ttk.Entry(arama_frame, width=30)
        self.arama_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(arama_frame, text="Ara", command=self.urun_ara).pack(side=tk.LEFT, padx=5)
        ttk.Button(arama_frame, text="Tümünü Göster", command=self.tum_urunleri_goster).pack(side=tk.LEFT, padx=5)
        
        # Stok listesi
        liste_frame = ttk.Frame(stok_frame)
        liste_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.stok_tree = ttk.Treeview(liste_frame, columns=("ID", "Ürün Kodu", "Ürün Adı", "Kategori", "Birim Fiyat", "Stok Miktarı"))
        self.stok_tree.heading("ID", text="ID")
        self.stok_tree.heading("Ürün Kodu", text="Ürün Kodu")
        self.stok_tree.heading("Ürün Adı", text="Ürün Adı")
        self.stok_tree.heading("Kategori", text="Kategori")
        self.stok_tree.heading("Birim Fiyat", text="Birim Fiyat")
        self.stok_tree.heading("Stok Miktarı", text="Stok Miktarı")
        
        self.stok_tree.column("ID", width=50)
        self.stok_tree.column("Ürün Kodu", width=100)
        self.stok_tree.column("Ürün Adı", width=200)
        self.stok_tree.column("Kategori", width=100)
        self.stok_tree.column("Birim Fiyat", width=100)
        self.stok_tree.column("Stok Miktarı", width=100)
        
        self.stok_tree['show'] = 'headings'  # ID sütununu gizle
        self.stok_tree.pack(side=tk.LEFT, fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(liste_frame, orient="vertical", command=self.stok_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill='y')
        self.stok_tree.configure(yscrollcommand=scrollbar.set)
        
        # Stok güncelleme çerçevesi
        guncelleme_frame = ttk.LabelFrame(stok_frame, text="Stok Güncelleme")
        guncelleme_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(guncelleme_frame, text="Yeni Miktar:").grid(row=0, column=0, padx=5, pady=5)
        self.yeni_miktar_entry = ttk.Entry(guncelleme_frame, width=10)
        self.yeni_miktar_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(guncelleme_frame, text="Stok Güncelle", command=self.stok_guncelle).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(guncelleme_frame, text="Ürünü Sil", command=self.urun_sil).grid(row=0, column=3, padx=5, pady=5)
        
        # Stok listesini yükle
        self.tum_urunleri_goster()
    
    def urun_ekle_sekmesi_olustur(self):
        urun_ekle_frame = ttk.Frame(self.notebook)
        self.notebook.add(urun_ekle_frame, text="Ürün Ekle")
        
        form_frame = ttk.LabelFrame(urun_ekle_frame, text="Yeni Ürün Bilgileri")
        form_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Ürün bilgileri girişi
        ttk.Label(form_frame, text="Ürün Kodu:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.urun_kodu_entry = ttk.Entry(form_frame, width=30)
        self.urun_kodu_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(form_frame, text="Ürün Adı:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.urun_adi_entry = ttk.Entry(form_frame, width=30)
        self.urun_adi_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(form_frame, text="Kategori:").grid(row=2, column=0, padx=5, pady=5, sticky='w')
        self.kategori_entry = ttk.Entry(form_frame, width=30)
        self.kategori_entry.grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(form_frame, text="Birim Fiyat:").grid(row=3, column=0, padx=5, pady=5, sticky='w')
        self.fiyat_entry = ttk.Entry(form_frame, width=30)
        self.fiyat_entry.grid(row=3, column=1, padx=5, pady=5)
        
        ttk.Label(form_frame, text="Stok Miktarı:").grid(row=4, column=0, padx=5, pady=5, sticky='w')
        self.miktar_entry = ttk.Entry(form_frame, width=30)
        self.miktar_entry.grid(row=4, column=1, padx=5, pady=5)
        
        # Ürün ekle butonu
        ttk.Button(form_frame, text="Ürün Ekle", command=self.yeni_urun_ekle).grid(row=5, column=0, columnspan=2, pady=20)
    
    def satis_sekmesi_olustur(self):
        satis_frame = ttk.Frame(self.notebook)
        self.notebook.add(satis_frame, text="Satış Yap")
        
        # Ürün seçme
        urun_secme_frame = ttk.LabelFrame(satis_frame, text="Ürün Seçimi")
        urun_secme_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(urun_secme_frame, text="Ürün Kodu:").grid(row=0, column=0, padx=5, pady=5)
        self.satis_urun_kodu_entry = ttk.Entry(urun_secme_frame, width=20)
        self.satis_urun_kodu_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(urun_secme_frame, text="Ürün Bul", command=self.satis_urun_bul).grid(row=0, column=2, padx=5, pady=5)
        
        # Ürün bilgisi
        self.urun_bilgisi_label = ttk.Label(urun_secme_frame, text="")
        self.urun_bilgisi_label.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky='w')
        
        # Satış miktarı
        ttk.Label(urun_secme_frame, text="Satış Miktarı:").grid(row=2, column=0, padx=5, pady=5)
        self.satis_miktar_entry = ttk.Entry(urun_secme_frame, width=10)
        self.satis_miktar_entry.grid(row=2, column=1, padx=5, pady=5, sticky='w')
        
        # Müşteri bilgileri
        musteri_frame = ttk.LabelFrame(satis_frame, text="Müşteri Bilgileri")
        musteri_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(musteri_frame, text="Adı:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.musteri_adi_entry = ttk.Entry(musteri_frame, width=30)
        self.musteri_adi_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(musteri_frame, text="Soyadı:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.musteri_soyadi_entry = ttk.Entry(musteri_frame, width=30)
        self.musteri_soyadi_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(musteri_frame, text="Telefon:").grid(row=2, column=0, padx=5, pady=5, sticky='w')
        self.musteri_telefon_entry = ttk.Entry(musteri_frame, width=30)
        self.musteri_telefon_entry.grid(row=2, column=1, padx=5, pady=5)
        
        # Satış tamamla butonu
        ttk.Button(satis_frame, text="Satışı Tamamla", command=self.satis_yap).pack(pady=20)
    
    def raporlar_sekmesi_olustur(self):
        rapor_frame = ttk.Frame(self.notebook)
        self.notebook.add(rapor_frame, text="Raporlar")
        
        # Rapor seçenekleri
        ttk.Button(rapor_frame, text="Satış Raporu", command=self.satis_raporu_goster).pack(pady=10)
        ttk.Button(rapor_frame, text="Stok Raporu", command=self.stok_raporu_goster).pack(pady=10)
        
        # Rapor sonuçları
        self.rapor_frame = ttk.LabelFrame(rapor_frame, text="Rapor Sonuçları")
        self.rapor_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.rapor_tree = ttk.Treeview(self.rapor_frame)
        self.rapor_tree.pack(side=tk.LEFT, fill='both', expand=True)
        
        rapor_scrollbar = ttk.Scrollbar(self.rapor_frame, orient="vertical", command=self.rapor_tree.yview)
        rapor_scrollbar.pack(side=tk.RIGHT, fill='y')
        self.rapor_tree.configure(yscrollcommand=rapor_scrollbar.set)
        
        # Varsayılan sütun yapılandırması ekle
        self.rapor_tree['columns'] = ("bos",)
        self.rapor_tree.column("bos", width=800)  # Başlangıç genişliği
        self.rapor_tree.heading("bos", text="")
        self.rapor_tree['show'] = 'headings'
    
    def tum_urunleri_goster(self):
        # Treeview temizle
        for item in self.stok_tree.get_children():
            self.stok_tree.delete(item)
        
        # Tüm ürünleri veritabanından al
        self.cursor.execute("SELECT id, urun_kodu, urun_adi, kategori, birim_fiyat, stok_miktari FROM urunler")
        urunler = self.cursor.fetchall()
        
        # Ürünleri Treeview'a ekle
        for urun in urunler:
            self.stok_tree.insert("", "end", values=urun)
    
    def urun_ara(self):
        arama_terimi = self.arama_entry.get()
        
        # Treeview temizle
        for item in self.stok_tree.get_children():
            self.stok_tree.delete(item)
        
        # Arama sorgusunu çalıştır
        self.cursor.execute("""
        SELECT id, urun_kodu, urun_adi, kategori, birim_fiyat, stok_miktari FROM urunler
        WHERE urun_kodu LIKE ? OR urun_adi LIKE ? OR kategori LIKE ?
        """, (f"%{arama_terimi}%", f"%{arama_terimi}%", f"%{arama_terimi}%"))
        
        urunler = self.cursor.fetchall()
        
        # Bulunan ürünleri Treeview'a ekle
        for urun in urunler:
            self.stok_tree.insert("", "end", values=urun)
    
    def stok_guncelle(self):
        # Seçili ürünü al
        secili_urun = self.stok_tree.selection()
        if not secili_urun:
            messagebox.showerror("Hata", "Lütfen bir ürün seçin!")
            return
        
        urun_id = self.stok_tree.item(secili_urun[0])['values'][0]
        yeni_miktar = self.yeni_miktar_entry.get()
        
        # Geçerlilik kontrolü
        if not yeni_miktar or not yeni_miktar.isdigit():
            messagebox.showerror("Hata", "Geçerli bir miktar girin!")
            return
        
        # Stok güncelle
        try:
            self.cursor.execute("UPDATE urunler SET stok_miktari = ? WHERE id = ?", (yeni_miktar, urun_id))
            self.conn.commit()
            messagebox.showinfo("Başarılı", "Stok miktarı güncellendi!")
            self.tum_urunleri_goster()
            self.yeni_miktar_entry.delete(0, tk.END)
        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", str(e))
    
    def urun_sil(self):
        # Seçili ürünü al
        secili_urun = self.stok_tree.selection()
        if not secili_urun:
            messagebox.showerror("Hata", "Lütfen bir ürün seçin!")
            return
        
        urun_id = self.stok_tree.item(secili_urun[0])['values'][0]
        urun_adi = self.stok_tree.item(secili_urun[0])['values'][2]
        
        # Silme onayı
        onay = messagebox.askyesno("Onay", f"{urun_adi} ürününü silmek istediğinize emin misiniz?")
        if not onay:
            return
        
        # Ürünü sil
        try:
            self.cursor.execute("DELETE FROM urunler WHERE id = ?", (urun_id,))
            self.conn.commit()
            messagebox.showinfo("Başarılı", "Ürün silindi!")
            self.tum_urunleri_goster()
        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", str(e))
    
    def yeni_urun_ekle(self):
        # Form değerlerini al
        urun_kodu = self.urun_kodu_entry.get()
        urun_adi = self.urun_adi_entry.get()
        kategori = self.kategori_entry.get()
        
        try:
            birim_fiyat = float(self.fiyat_entry.get())
            stok_miktari = int(self.miktar_entry.get())
        except ValueError:
            messagebox.showerror("Hata", "Birim fiyat ve stok miktarı sayısal değer olmalıdır!")
            return
        
        # Boş alan kontrolü
        if not all([urun_kodu, urun_adi, kategori]):
            messagebox.showerror("Hata", "Lütfen tüm alanları doldurun!")
            return
        
        # Veritabanına ekle
        eklenme_tarihi = self.turkce_tarih()
        
        try:
            self.cursor.execute("""
            INSERT INTO urunler (urun_kodu, urun_adi, kategori, birim_fiyat, stok_miktari, eklenme_tarihi)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (urun_kodu, urun_adi, kategori, birim_fiyat, stok_miktari, eklenme_tarihi))
            
            self.conn.commit()
            messagebox.showinfo("Başarılı", "Ürün başarıyla eklendi!")
            
            # Formu temizle
            for entry in [self.urun_kodu_entry, self.urun_adi_entry, self.kategori_entry, 
                          self.fiyat_entry, self.miktar_entry]:
                entry.delete(0, tk.END)
                
            # Stok listesini güncelle
            self.tum_urunleri_goster()
            
        except sqlite3.IntegrityError:
            messagebox.showerror("Hata", "Bu ürün kodu zaten kullanılıyor!")
        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", str(e))
    
    def satis_urun_bul(self):
        urun_kodu = self.satis_urun_kodu_entry.get()
        
        if not urun_kodu:
            messagebox.showerror("Hata", "Lütfen bir ürün kodu girin!")
            return
        
        # Ürünü bul
        self.cursor.execute("""
        SELECT id, urun_adi, birim_fiyat, stok_miktari FROM urunler WHERE urun_kodu = ?
        """, (urun_kodu,))
        
        urun = self.cursor.fetchone()
        
        if urun:
            self.secili_urun_id = urun[0]
            self.urun_bilgisi_label.config(
                text=f"Ürün: {urun[1]}, Fiyat: {urun[2]} TL, Stok: {urun[3]}")
        else:
            messagebox.showerror("Hata", "Ürün bulunamadı!")
            self.urun_bilgisi_label.config(text="")
            self.secili_urun_id = None
    
    def satis_yap(self):
        # Ürün seçili mi kontrol et
        if not hasattr(self, 'secili_urun_id') or self.secili_urun_id is None:
            messagebox.showerror("Hata", "Lütfen önce bir ürün seçin!")
            return
        
        # Form değerlerini al
        try:
            satis_miktari = int(self.satis_miktar_entry.get())
        except ValueError:
            messagebox.showerror("Hata", "Geçerli bir miktar girin!")
            return
        
        musteri_adi = self.musteri_adi_entry.get()
        musteri_soyadi = self.musteri_soyadi_entry.get()
        musteri_telefon = self.musteri_telefon_entry.get()
        
        # Boş alan kontrolü
        if not all([musteri_adi, musteri_soyadi, musteri_telefon]):
            messagebox.showerror("Hata", "Lütfen müşteri bilgilerini doldurun!")
            return
        
        # Stok kontrolü
        self.cursor.execute("SELECT stok_miktari FROM urunler WHERE id = ?", (self.secili_urun_id,))
        stok = self.cursor.fetchone()[0]
        
        if satis_miktari > stok:
            messagebox.showerror("Hata", "Yetersiz stok! Mevcut stok: " + str(stok))
            return
        
        # Veritabanı işlemleri
        try:
            # Satış kaydı ekle
            satis_tarihi = self.turkce_tarih()
            self.cursor.execute("""
            INSERT INTO satislar (urun_id, miktar, satis_tarihi, musteri_adi, musteri_soyadi, musteri_telefon)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (self.secili_urun_id, satis_miktari, satis_tarihi, musteri_adi, musteri_soyadi, musteri_telefon))
            
            # Stok güncelle
            yeni_stok = stok - satis_miktari
            self.cursor.execute("UPDATE urunler SET stok_miktari = ? WHERE id = ?", 
                               (yeni_stok, self.secili_urun_id))
            
            self.conn.commit()
            messagebox.showinfo("Başarılı", "Satış işlemi tamamlandı!")
            
            # Formu temizle
            for entry in [self.satis_urun_kodu_entry, self.satis_miktar_entry, 
                         self.musteri_adi_entry, self.musteri_soyadi_entry, self.musteri_telefon_entry]:
                entry.delete(0, tk.END)
            
            self.urun_bilgisi_label.config(text="")
            self.secili_urun_id = None
            
            # Stok listesini güncelle
            self.tum_urunleri_goster()
            
        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", str(e))
    
    def satis_raporu_goster(self):
        # Rapor tree'yi temizle ve konfigüre et
        for item in self.rapor_tree.get_children():
            self.rapor_tree.delete(item)
    
        for col in self.rapor_tree['columns']:
            self.rapor_tree.heading(col, text="")
    
        # Sütunları tanımla
        self.rapor_tree['columns'] = ("id", "urun_adi", "miktar", "tarih", "musteri")
    
        # Sütun başlıklarını ayarla
        self.rapor_tree.heading("id", text="ID", anchor=tk.CENTER)
        self.rapor_tree.heading("urun_adi", text="Ürün Adı", anchor=tk.CENTER)
        self.rapor_tree.heading("miktar", text="Miktar", anchor=tk.CENTER)
        self.rapor_tree.heading("tarih", text="Satış Tarihi", anchor=tk.CENTER)
        self.rapor_tree.heading("musteri", text="Müşteri", anchor=tk.CENTER)
    
        # Sütun genişliklerini ayarla
        self.rapor_frame.update()  # Frame'in güncel genişliğini al
        frame_width = self.rapor_frame.winfo_width() - 20  # Scrollbar için yer bırak
    
        # Sütun genişliklerini oransal olarak ayarla
        self.rapor_tree.column("id", width=int(frame_width * 0.05), anchor=tk.CENTER)
        self.rapor_tree.column("urun_adi", width=int(frame_width * 0.30), anchor=tk.CENTER)
        self.rapor_tree.column("miktar", width=int(frame_width * 0.10), anchor=tk.CENTER)
        self.rapor_tree.column("tarih", width=int(frame_width * 0.25), anchor=tk.CENTER)
        self.rapor_tree.column("musteri", width=int(frame_width * 0.30), anchor=tk.CENTER)
    
        self.rapor_tree['show'] = 'headings'
    
        # Veritabanından satış verilerini al
        # Veritabanından satış verilerini al
        self.cursor.execute("""
        SELECT s.id, u.urun_adi, s.miktar, s.satis_tarihi, s.musteri_adi || ' ' || s.musteri_soyadi
        FROM satislar s
        JOIN urunler u ON s.urun_id = u.id
        ORDER BY s.satis_tarihi DESC
        """)
    
        satislar = self.cursor.fetchall()
    
        # Verileri ekle
        for satis in satislar:
            self.rapor_tree.insert("", "end", values=satis)
    
    def musteri_bilgileri_sekmesi_olustur(self):
        musteri_frame = ttk.Frame(self.notebook)
        self.notebook.add(musteri_frame, text="Müşteri Bilgileri")
    
        # Arama çerçevesi
        arama_frame = ttk.Frame(musteri_frame)
        arama_frame.pack(fill='x', padx=5, pady=5)
    
        ttk.Label(arama_frame, text="Müşteri Ara:").pack(side=tk.LEFT, padx=5)
        self.musteri_arama_entry = ttk.Entry(arama_frame, width=30)
        self.musteri_arama_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(arama_frame, text="Ara", command=self.musteri_ara).pack(side=tk.LEFT, padx=5)
        ttk.Button(arama_frame, text="Tüm Müşteriler", command=self.tum_musterileri_goster).pack(side=tk.LEFT, padx=5)
    
        # Müşteri listesi
        liste_frame = ttk.Frame(musteri_frame)
        liste_frame.pack(fill='both', expand=True, padx=5, pady=5)
    
        self.musteri_tree = ttk.Treeview(liste_frame, columns=("ID", "Adı", "Soyadı", "Telefon", "Son Alışveriş"))
        self.musteri_tree.heading("ID", text="ID", anchor=tk.CENTER)
        self.musteri_tree.heading("Adı", text="Adı", anchor=tk.CENTER)
        self.musteri_tree.heading("Soyadı", text="Soyadı", anchor=tk.CENTER)
        self.musteri_tree.heading("Telefon", text="Telefon", anchor=tk.CENTER)
        self.musteri_tree.heading("Son Alışveriş", text="Son Alışveriş", anchor=tk.CENTER)
    
        self.musteri_tree.column("ID", width=50, anchor=tk.CENTER)
        self.musteri_tree.column("Adı", width=150, anchor=tk.CENTER)
        self.musteri_tree.column("Soyadı", width=150, anchor=tk.CENTER)
        self.musteri_tree.column("Telefon", width=150, anchor=tk.CENTER)
        self.musteri_tree.column("Son Alışveriş", width=200, anchor=tk.CENTER)
    
        self.musteri_tree['show'] = 'headings'  # ID sütununu gizle
        self.musteri_tree.pack(side=tk.LEFT, fill='both', expand=True)
    
        scrollbar = ttk.Scrollbar(liste_frame, orient="vertical", command=self.musteri_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill='y')
        self.musteri_tree.configure(yscrollcommand=scrollbar.set)
    
        # Çift tıklama ile detay görüntüleme
        self.musteri_tree.bind("<Double-1>", self.musteri_detay_goster)
    
        # Müşteri listesini yükle
        self.tum_musterileri_goster()

    def tum_musterileri_goster(self):
        # Treeview temizle
        for item in self.musteri_tree.get_children():
            self.musteri_tree.delete(item)
    
        # Tüm müşterileri veritabanından al
        self.cursor.execute("""
        SELECT DISTINCT 
            s.musteri_adi as adi, 
            s.musteri_soyadi as soyadi, 
            s.musteri_telefon as telefon,
            MAX(s.satis_tarihi) as son_alisveris,
            MIN(s.id) as id
        FROM satislar s
        GROUP BY s.musteri_telefon
        ORDER BY s.musteri_adi
        """)
    
        musteriler = self.cursor.fetchall()
    
        # Müşterileri Treeview'a ekle
        for musteri in musteriler:
            self.musteri_tree.insert("", "end", values=(musteri[4], musteri[0], musteri[1], musteri[2], musteri[3]))

    def musteri_ara(self):
        arama_terimi = self.musteri_arama_entry.get()
    
        # Treeview temizle
        for item in self.musteri_tree.get_children():
            self.musteri_tree.delete(item)
    
        # Arama sorgusunu çalıştır
        self.cursor.execute("""
        SELECT DISTINCT 
            s.musteri_adi as adi, 
            s.musteri_soyadi as soyadi, 
            s.musteri_telefon as telefon,
            MAX(s.satis_tarihi) as son_alisveris,
            MIN(s.id) as id
        FROM satislar s
        WHERE 
            s.musteri_adi LIKE ? OR 
            s.musteri_soyadi LIKE ? OR 
            s.musteri_telefon LIKE ?
        GROUP BY s.musteri_telefon
        ORDER BY s.musteri_adi
        """, (f"%{arama_terimi}%", f"%{arama_terimi}%", f"%{arama_terimi}%"))
    
        musteriler = self.cursor.fetchall()
    
        # Bulunan müşterileri Treeview'a ekle
        for musteri in musteriler:
            self.musteri_tree.insert("", "end", values=(musteri[4], musteri[0], musteri[1], musteri[2], musteri[3]))

    def musteri_detay_goster(self, event):
        try:
            # Seçili müşteriyi al
            item = self.musteri_tree.selection()[0]
            musteri_id = self.musteri_tree.item(item, "values")[0]
        
            # Detay penceresi oluştur
            detay_pencere = tk.Toplevel(self.root)
            detay_pencere.title("Müşteri Alışveriş Detayları")
            detay_pencere.geometry("800x400")
            detay_pencere.resizable(False, False)
        
            # Müşteri bilgilerini al
            self.cursor.execute("""
            SELECT musteri_adi, musteri_soyadi, musteri_telefon
            FROM satislar
            WHERE id = ?
            """, (musteri_id,))
        
            musteri = self.cursor.fetchone()
            
            if not musteri:
                messagebox.showerror("Hata", "Müşteri bilgileri bulunamadı!")
                detay_pencere.destroy()
                return
        
            # Müşteri bilgileri başlığı
            ttk.Label(detay_pencere, 
                  text=f"Müşteri: {musteri[0]} {musteri[1]} - Tel: {musteri[2]}",
                  font=("Arial", 12, "bold")).pack(pady=10)
        
            # Alışveriş detayları tablosu
            frame = ttk.Frame(detay_pencere)
            frame.pack(fill='both', expand=True, padx=10, pady=10)
        
            detay_tree = ttk.Treeview(frame, columns=("Tarih", "Ürün", "Miktar", "Fiyat", "Toplam"))
            detay_tree.heading("Tarih", text="Satış Tarihi", anchor=tk.CENTER)
            detay_tree.heading("Ürün", text="Ürün Adı", anchor=tk.CENTER)
            detay_tree.heading("Miktar", text="Miktar", anchor=tk.CENTER)
            detay_tree.heading("Fiyat", text="Birim Fiyat", anchor=tk.CENTER)
            detay_tree.heading("Toplam", text="Toplam Tutar", anchor=tk.CENTER)
        
            detay_tree.column("Tarih", width=150, anchor=tk.CENTER)
            detay_tree.column("Ürün", width=250, anchor=tk.CENTER)
            detay_tree.column("Miktar", width=100, anchor=tk.CENTER)
            detay_tree.column("Fiyat", width=150, anchor=tk.CENTER)
            detay_tree.column("Toplam", width=150, anchor=tk.CENTER)
        
            detay_tree['show'] = 'headings'
            detay_tree.pack(side=tk.LEFT, fill='both', expand=True)
        
            scrollbar = ttk.Scrollbar(frame, orient="vertical", command=detay_tree.yview)
            scrollbar.pack(side=tk.RIGHT, fill='y')
            detay_tree.configure(yscrollcommand=scrollbar.set)
        
            # Alışveriş detaylarını al
            self.cursor.execute("""
            SELECT 
                s.satis_tarihi, 
                u.urun_adi, 
                s.miktar, 
                u.birim_fiyat,
                (s.miktar * u.birim_fiyat) as toplam_tutar
            FROM satislar s
            JOIN urunler u ON s.urun_id = u.id
            WHERE s.musteri_telefon = ?
            ORDER BY s.satis_tarihi DESC
            """, (musteri[2],))
        
            alisverisler = self.cursor.fetchall()
        
            # Alışverişleri tabloya ekle
            for alisveris in alisverisler:
                detay_tree.insert("", "end", values=(
                    alisveris[0], 
                    alisveris[1], 
                    alisveris[2], 
                    f"{alisveris[3]:.2f} TL", 
                    f"{alisveris[4]:.2f} TL"
                ))
        except Exception as e:
            messagebox.showerror("Hata", f"Müşteri detayları gösterilirken bir hata oluştu: {str(e)}")

    def stok_raporu_goster(self):
        # Rapor tree'yi temizle ve konfigüre et
        for item in self.rapor_tree.get_children():
            self.rapor_tree.delete(item)

        for col in self.rapor_tree['columns']:
            self.rapor_tree.heading(col, text="")

        # Sütunları tanımla
        self.rapor_tree['columns'] = ("urun_kodu", "urun_adi", "kategori", "stok", "deger")

        # Sütun başlıklarını ayarla
        self.rapor_tree.heading("urun_kodu", text="Ürün Kodu", anchor=tk.CENTER)
        self.rapor_tree.heading("urun_adi", text="Ürün Adı", anchor=tk.CENTER)
        self.rapor_tree.heading("kategori", text="Kategori", anchor=tk.CENTER)
        self.rapor_tree.heading("stok", text="Stok Miktarı", anchor=tk.CENTER)
        self.rapor_tree.heading("deger", text="Toplam Değer", anchor=tk.CENTER)

        # Sütun genişliklerini ayarla
        self.rapor_frame.update()  # Frame'in güncel genişliğini al
        frame_width = self.rapor_frame.winfo_width() - 20  # Scrollbar için yer bırak

        # Sütun genişliklerini oransal olarak ayarla
        self.rapor_tree.column("urun_kodu", width=int(frame_width * 0.15), anchor=tk.CENTER)
        self.rapor_tree.column("urun_adi", width=int(frame_width * 0.30), anchor=tk.CENTER)
        self.rapor_tree.column("kategori", width=int(frame_width * 0.20), anchor=tk.CENTER)
        self.rapor_tree.column("stok", width=int(frame_width * 0.15), anchor=tk.CENTER)
        self.rapor_tree.column("deger", width=int(frame_width * 0.20), anchor=tk.CENTER)

        self.rapor_tree['show'] = 'headings'

        # Veritabanından stok verilerini al
        self.cursor.execute("""
        SELECT urun_kodu, urun_adi, kategori, stok_miktari, stok_miktari * birim_fiyat as toplam_deger
        FROM urunler
        ORDER BY toplam_deger DESC
        """)

        stoklar = self.cursor.fetchall()

        # Verileri ekle
        for stok in stoklar:
            self.rapor_tree.insert("", "end", values=stok)

    def kapat(self):
        # Veritabanı bağlantısını kapat
        if hasattr(self, 'conn'):
            self.conn.close()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = DepoStokSistemi(root)
    root.mainloop()