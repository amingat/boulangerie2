# -*- coding: utf-8 -*-
"""
Trouves ton Pain !!!!
Version : lien "clique ici" ouvre le PDF au clic sur le bon pain
         puis écran noir avec "Allez Bisous 💋 💋 !!".
Base : cœurs jusqu’en bas (durée dynamique), "Pain aux figues (sucrés/salés)",
couleurs accentuées (vert/rouge), padding anti-coupe, espacement horizontal régulier.
(Portabilité macOS/Windows/Linux + support exécutable packagé)
"""
from pathlib import Path
import os
import sys
import shutil
import random
import platform
import subprocess
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont
import webbrowser
import sys
import subprocess
import webbrowser
import os

APP_TITLE = "Trouves ton Pain !!!!"
WELCOME   = "Bienvenue à la Boulangerie"
QUESTION  = "Choisis ton Pain !!! > En cliquant dessus 🖱️"

# --- Messages ---
LOST_MSG  = "Ce pain n'est malheureusement plus disponible"

WIN_MSG_MAIN = ("Félicitation \n"
                "tu as trouvé ton pain < 3 !\n"
                "Tu veux en apprendre plus sur ton pain \n"
                "Télécharges son CV juste ici")
WIN_LINK_LABEL = "clique ici"  # lien bleu, cliquable

# --- Helpers chemins (compatible exécutable packagé) ---
def base_path() -> Path:
    # PyInstaller: sys._MEIPASS pointe vers le dossier temporaire d'extraction
    return Path(getattr(sys, "_MEIPASS", Path(__file__).parent))

BASE_DIR   = base_path()
ASSETS_DIR = BASE_DIR / "assets"
BG_DIR     = ASSETS_DIR / "Boulangerie"
BAD_DIR    = ASSETS_DIR / "Mauvais Pain"
GOOD_DIR   = ASSETS_DIR / "Bon pain"

# --- PDF à ouvrir (placé à la racine du repo / bundle) ---
PDF_FILENAME = "CV - Arnaud MINGAT - Alternance -Développeur GenAI.pdf"

BASE_THUMB_W = 240
BASE_THUMB_H = 300
COLS, ROWS = 4, 2
BASE_ROW_SPACING = 20
TOP_EXTRA_MARGIN = 12
SIDE_MARGIN      = 20
BOTTOM_MARGIN    = 100

CAPTION_FONT_SIZE_BASE = 16
CAPTION_LINES_MAX      = 2
CAPTION_VPAD           = 6

# --- Animation coeurs (durée dynamique) ---
HEART_COUNT       = 40
HEART_MIN_SIZE    = 16
HEART_MAX_SIZE    = 36
HEART_MIN_SPEED   = 1.6   # px/tick
HEART_MAX_SPEED   = 3.6
HEART_TICK_MS     = 16    # ~60 FPS

def list_images(folder: Path):
    exts = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}
    return [p for p in folder.rglob("*") if p.suffix.lower() in exts] if folder.exists() else []

def face_friendly_crop(img, target_ratio: float):
    """Recadre au ratio demandé en privilégiant le haut (visages)."""
    img = img.convert("RGB")
    w, h = img.size
    src_ratio = w / h
    if src_ratio > target_ratio:
        new_w = int(h * target_ratio)
        left = max(0, (w - new_w) // 2)
        return img.crop((left, 0, left + new_w, h))
    else:
        new_h = int(w / target_ratio)
        top = max(0, min(h - new_h, int(h * 0.15)))
        return img.crop((0, top, w, top + new_h))

def load_font(size: int) -> ImageFont.FreeTypeFont:
    """Charge une police multiplateforme (Windows/macOS/Linux), fallback PIL si indisponible."""
    candidates = []
    if platform.system() == "Windows":
        candidates += [
            r"C:\Windows\Fonts\segoeuib.ttf",   # Segoe UI Semibold
            r"C:\Windows\Fonts\arialbd.ttf",
            r"C:\Windows\Fonts\ARIALBD.TTF",
        ]
    elif platform.system() == "Darwin":  # macOS
        candidates += [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/HelveticaNeue.ttc",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
    else:  # Linux
        candidates += [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ]
    for fp in candidates:
        try:
            return ImageFont.truetype(fp, size=size)
        except Exception:
            pass
    try:
        return ImageFont.truetype("arialbd.ttf", size=size)
    except Exception:
        return ImageFont.load_default()

def emoji_font_tuple(size: int):
    """Tuple de police pour le cœur (emoji) selon l’OS."""
    if platform.system() == "Windows":
        return ("Segoe UI Emoji", size)
    elif platform.system() == "Darwin":
        return ("Apple Color Emoji", size)
    else:
        # Beaucoup de distros mappent l’emoji via fallback; DejaVu ou Noto Color Emoji si dispo
        return ("DejaVu Sans", size)

class BakeryApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1280x800")
        self.minsize(900, 650)
        self.canvas = tk.Canvas(self, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)

        self.bg_raw = self._load_fixed_background()
        self.bg_tk = None

        bad_files = list_images(BAD_DIR)
        good_files = list_images(GOOD_DIR)
        if not bad_files and not good_files:
            messagebox.showerror("Alerte", "Aucune image trouvée.\nAjoutez des photos dans 'assets/Bon pain' et 'assets/Mauvais Pain'.")
            self.destroy(); return

        # 7 mauvais + 1 bon
        good_pick = random.choice(good_files) if good_files else None
        bad_pool = bad_files.copy(); random.shuffle(bad_pool)
        bad_selection = bad_pool[:7] if len(bad_pool) >= 7 else (bad_pool * 7)[:7]

        # Le bon pain est fixé : "Pain aux figues (sucrés/salés)"
        self.good_caption = "Pain aux figues\n(sucrés/salés)"

        # Titres : 7 aléatoires + le bon pain (placé en dernier puis aligné avec l’image bonne)
        bread_names_pool = [
            "Pain aux graines", "Pain au sésame", "Pain complet", "Pain de campagne",
            "Pain aux noix", "Pain aux céréales", "Pain brioché", "Pain au levain",
            "Baguette", "Pain au son", "Pain aux olives", "Pain rustique",
            "Pain au maïs", "Pain ciabatta", "Pain pita"
        ]
        random.shuffle(bread_names_pool)
        other_captions = bread_names_pool[:7]
        self.captions = other_captions + [self.good_caption]

        # Entrées (7 mauvais + 1 bon)
        self.entries = [{"path": p, "is_good": False} for p in bad_selection]
        if good_pick:
            self.entries.append({"path": good_pick, "is_good": True})
        else:
            if self.entries: self.entries[-1]["is_good"] = True

        random.shuffle(self.entries)

        # Aligner l’image "bonne" avec la légende "Pain aux figues (sucrés/salés)"
        good_index = next((i for i, e in enumerate(self.entries) if e["is_good"]), None)
        fig_index = len(self.captions) - 1
        if good_index is not None and good_index != fig_index:
            self.entries[good_index], self.entries[fig_index] = self.entries[fig_index], self.entries[good_index]

        # caches & états
        self.thumb_base, self.thumb_tk = {}, {}
        self.caption_imgs, self.photo_items, self.caption_ids = [], {}, []
        self.text_items, self.heart_items = [], []
        self.link_items = []  # IDs des liens
        self.heart_running, self.won = False, False
        self.replaced_paths = set()

        self.bind("<Configure>", self._on_resize)
        self.after(0, self._relayout)

    # ---------- Fond ----------
    def _load_fixed_background(self):
        preferred = BG_DIR / "youschool-devenir-boulanger.webp"
        if preferred.exists(): return Image.open(preferred).convert("RGB")
        for name in ["fond.jpg", "fond.png", "fond.webp"]:
            p = BG_DIR / name
            if p.exists(): return Image.open(p).convert("RGB")
        files = list_images(BG_DIR)
        return Image.open(files[0]).convert("RGB") if files else Image.new("RGB", (1600, 900), (245, 222, 179))

    # ---------- Texte avec contour (titres) ----------
    def _draw_text_with_stroke(self, x, y, text, font, fill, stroke_color="#000000", stroke_px=2, anchor="n"):
        shadow_ids = []
        for dx, dy in [(-stroke_px,0),(stroke_px,0),(0,-stroke_px),(0,stroke_px),(-stroke_px,-stroke_px),(stroke_px,-stroke_px),(-stroke_px,stroke_px),(stroke_px,stroke_px)]:
            sid = self.canvas.create_text(x + dx, y + dy, text=text, font=font, fill=stroke_color, anchor=anchor)
            shadow_ids.append(sid)
        main_id = self.canvas.create_text(x, y, text=text, font=font, fill=fill, anchor=anchor)
        return main_id, shadow_ids

    # ---------- Image de légende (bande noire + texte blanc lisible) ----------
    def _render_caption_img(self, text: str, width: int, font_size: int) -> ImageTk.PhotoImage:
        font = load_font(font_size)
        ascent, descent = font.getmetrics()
        line_h = ascent + descent
        cap_h = CAPTION_VPAD * 2 + CAPTION_LINES_MAX * line_h

        img = Image.new("RGBA", (max(40, width), cap_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rectangle([(0, 0), (img.width, img.height)], fill=(0, 0, 0, 150))

        def break_lines(t, max_w):
            words = t.split()
            lines, cur = [], ""
            for w in words:
                test = (cur + " " + w).strip()
                if draw.textlength(test, font=font) <= max_w or not cur:
                    cur = test
                else:
                    lines.append(cur); cur = w
            if cur: lines.append(cur)
            return lines[:CAPTION_LINES_MAX]

        max_text_w = img.width - 12
        lines = break_lines(text, max_text_w)
        total_text_h = len(lines) * line_h
        y0 = (img.height - total_text_h) // 2

        for i, line in enumerate(lines):
            y = y0 + i * line_h
            # contour noir
            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,-1),(-1,1),(1,1)]:
                draw.text((img.width//2 + dx, y + dy), line, font=font, fill=(0,0,0,255), anchor="mm")
            # texte blanc
            draw.text((img.width//2, y), line, font=font, fill=(255,255,255,255), anchor="mm")

        return ImageTk.PhotoImage(img)

    # ---------- Layout ----------
    def _relayout(self):
        self.canvas.delete("all")
        # reset états d'affichage
        self.text_items.clear(); self.photo_items.clear(); self.caption_ids.clear()
        self.caption_imgs.clear(); self.heart_items.clear(); self.link_items.clear()
        self.heart_running = False

        w, h = max(1, self.canvas.winfo_width()), max(1, self.canvas.winfo_height())
        bg = self.bg_raw.copy().resize((w, h), Image.LANCZOS)
        self.bg_tk = ImageTk.PhotoImage(bg)
        self.canvas.create_image(0, 0, image=self.bg_tk, anchor="nw")

        # Titres
        cx = w // 2
        y_cursor = 20
        wid, _ = self._draw_text_with_stroke(cx, y_cursor, WELCOME, ("Segoe UI", 36, "bold"),
                                             fill="#1769ff", stroke_color="#000000", stroke_px=2, anchor="n")
        bbox = self.canvas.bbox(wid); y_cursor = (bbox[3] if bbox else y_cursor) + 8
        qid, _ = self._draw_text_with_stroke(cx, y_cursor, QUESTION, ("Segoe UI", 28, "bold"),
                                             fill="#ffffff", stroke_color="#000000", stroke_px=2, anchor="n")
        bbox = self.canvas.bbox(qid); y_cursor = (bbox[3] if bbox else y_cursor) + TOP_EXTRA_MARGIN

        # Espace dispo pour la grille
        avail_w = w - 2 * SIDE_MARGIN
        avail_h = h - y_cursor - BOTTOM_MARGIN

        caption_font_size = max(12, int(CAPTION_FONT_SIZE_BASE))
        caption_block_h_base = CAPTION_VPAD * 2 + CAPTION_LINES_MAX * (caption_font_size + 6)
        grid_h_base = ROWS * (BASE_THUMB_H + caption_block_h_base) + (ROWS - 1) * BASE_ROW_SPACING
        scale = min(1.0, avail_h / grid_h_base)

        tw = int(BASE_THUMB_W * scale)
        th = int(BASE_THUMB_H * scale)
        caption_font_size = max(12, int(CAPTION_FONT_SIZE_BASE * scale))

        # Préparer miniatures (recadrage visage-friendly)
        target_ratio = BASE_THUMB_W / BASE_THUMB_H
        for e in self.entries:
            p = e["path"]
            if p not in self.thumb_base:
                base = Image.open(p)
                self.thumb_base[p] = face_friendly_crop(base, target_ratio)
            self.thumb_tk[p] = ImageTk.PhotoImage(self.thumb_base[p].resize((tw, th), Image.LANCZOS))

        # Répartition horizontale régulière
        total_w_photos = COLS * tw
        gaps = COLS + 1
        spacing = max((avail_w - total_w_photos) / gaps, 8)

        idx = 0
        y = y_cursor
        for _r in range(ROWS):
            x = SIDE_MARGIN + spacing
            for _c in range(COLS):
                if idx >= len(self.entries): break
                e = self.entries[idx]
                title = self.captions[idx % len(self.captions)]
                p = e["path"]; img_tk = self.thumb_tk[p]

                cx_item = x + tw / 2
                cy_item = y + th / 2

                img_id = self.canvas.create_image(cx_item, cy_item, image=img_tk, anchor="center")
                self.photo_items[img_id] = {"path": p, "is_good": e["is_good"], "cell_w": tw, "cell_h": th}
                self.canvas.tag_bind(img_id, "<Button-1>", self._on_photo_click)

                cap_img = self._render_caption_img(title, width=tw, font_size=caption_font_size)
                self.caption_imgs.append(cap_img)
                cap_h = cap_img.height()
                cap_y = y + th + 4
                cap_id = self.canvas.create_image(cx_item, cap_y + cap_h / 2, image=cap_img, anchor="center")
                self.caption_ids.append(cap_id)

                x += tw + spacing
                idx += 1
            y += th + cap_h + BASE_ROW_SPACING

    def _on_resize(self, event):
        self.after(0, self._relayout)

    # ---------- Ouvrir le PDF puis écran noir "Bisous" ----------
    def _open_pdf(self, *_):
        """Ouvre le PDF avec l’app par défaut (Windows/macOS/Linux).
        Repli : ouvre file:// dans le navigateur. Puis écran 'Bisous'."""
        src = BASE_DIR / PDF_FILENAME
        if not src.exists():
            messagebox.showerror("Ouverture du PDF", f"Fichier introuvable :\n{src}")
            return

        opened = False
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(src))  # Windows
                opened = True
            elif sys.platform == "darwin":
                subprocess.run(["open", str(src)], check=False)  # macOS
                opened = True
            else:
                # Linux/other
                subprocess.run(["xdg-open", str(src)], check=False)
                opened = True
        except Exception:
            pass

        if not opened:
            try:
                webbrowser.open(src.as_uri())
                opened = True
            except Exception as e:
                messagebox.showerror("Ouverture du PDF", f"Impossible d'ouvrir le PDF :\n{e}")

        if opened:
            self.after(300, self._show_bye_overlay)

    def _show_bye_overlay(self):
        """Efface l'UI et affiche un écran noir avec le message final en grand."""
        # Stoppe l'animation des cœurs et nettoie
        self.heart_running = False
        for it, _ in list(self.heart_items):
            try:
                self.canvas.delete(it)
            except tk.TclError:
                pass
        self.heart_items.clear()

        self.canvas.delete("all")
        w = max(1, self.canvas.winfo_width())
        h = max(1, self.canvas.winfo_height())
        # fond noir plein écran
        self.canvas.create_rectangle(0, 0, w, h, fill="#000000", outline="")

        # message centré géant
        msg = "Allez Bisous 💋 💋 !!"
        big_font = ("Segoe UI", 64, "bold") if platform.system() == "Windows" else ("Helvetica", 64, "bold")

        # petit contour pour lisibilité
        def draw_centered_with_stroke(text, fill="#ffffff"):
            for dx, dy in [(-2,0),(2,0),(0,-2),(0,2),(-2,-2),(2,-2),(-2,2),(2,2)]:
                self.canvas.create_text(w//2 + dx, h//2 + dy, text=text, font=big_font, fill="#000000", anchor="center")
            self.canvas.create_text(w//2, h//2, text=text, font=big_font, fill=fill, anchor="center")

        draw_centered_with_stroke(msg, fill="#ffffff")

    # ---------- (Conservée) Téléchargement du PDF ----------
    def _download_pdf(self, *_):
        """Copie le PDF vers le dossier Téléchargements de l'utilisateur."""
        src = BASE_DIR / PDF_FILENAME
        if not src.exists():
            messagebox.showerror("Téléchargement", f"Fichier introuvable :\n{src}")
            return

        downloads_dir = Path.home() / "Downloads"
        downloads_dir.mkdir(parents=True, exist_ok=True)

        dst = downloads_dir / src.name
        if dst.exists():
            stem, suffix = dst.stem, dst.suffix
            k = 1
            while True:
                candidate = downloads_dir / f"{stem} ({k}){suffix}"
                if not candidate.exists():
                    dst = candidate
                    break
                k += 1
        try:
            shutil.copyfile(src, dst)
            messagebox.showinfo("Téléchargement", f"PDF enregistré dans :\n{dst}")
        except Exception as e:
            messagebox.showerror("Téléchargement", f"Échec de l'enregistrement :\n{e}")

    # ---------- Clic sur une photo ----------
    def _on_photo_click(self, event):
        if self.won: return
        ids = self.canvas.find_withtag("current")
        if not ids: return
        item_id = ids[0]
        meta = self.photo_items.get(item_id)
        if not meta or meta["path"] in self.replaced_paths: return

        p = meta["path"]
        is_good = meta["is_good"]
        info_main = WIN_MSG_MAIN if is_good else LOST_MSG

        cx, cy = self.canvas.coords(item_id)
        self.canvas.delete(item_id)
        self.photo_items.pop(item_id, None)

        # Respect strict des lignes (pas de coupe) pour le message gagnant
        font = load_font(14)
        cell_w = meta["cell_w"]
        max_w = int(cell_w - 16)

        meas_draw = ImageDraw.Draw(Image.new("RGBA", (10, 10)))

        if is_good:
            raw_lines = info_main.splitlines()
            line_widths = [meas_draw.textlength(line, font=font) for line in raw_lines]
            need_w = (max(line_widths) if line_widths else 0) + 24
            txt_w = max(max_w, int(need_w))
            lines = raw_lines
        else:
            words = info_main.split()
            lines, cur = [], ""
            for w in words:
                test = (cur + " " + w).strip()
                if meas_draw.textlength(test, font=font) <= max_w or not cur:
                    cur = test
                else:
                    lines.append(cur); cur = w
            if cur: lines.append(cur)
            lines = lines[:6]
            txt_w = max_w

        ascent, descent = font.getmetrics()
        line_h = ascent + descent
        PAD_TOP, PAD_BOT = 12, 12
        txt_h = PAD_TOP + len(lines) * line_h + PAD_BOT

        img = Image.new("RGBA", (txt_w, txt_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        fill_col = (16, 200, 16, 255) if is_good else (122, 26, 26, 255)
        stroke_col = (0, 0, 0, 255)

        y = PAD_TOP
        for line in lines:
            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,-1),(-1,1),(1,1)]:
                draw.text((txt_w // 2 + dx, y + dy), line, font=font, fill=stroke_col, anchor="mm")
            draw.text((txt_w // 2, y), line, font=font, fill=fill_col, anchor="mm")
            y += line_h

        txt_tk = ImageTk.PhotoImage(img)
        self.caption_imgs.append(txt_tk)
        self.canvas.create_image(cx, cy, image=txt_tk, anchor="center")

        # Lien "clique ici" qui ouvre le PDF
        if is_good and not self.won:
            link_y = cy + (txt_h // 2) + 8
            link_id = self.canvas.create_text(
                cx, link_y,
                text=WIN_LINK_LABEL,
                font=("Segoe UI", 14, "underline"),
                fill="#1769ff",
                anchor="n"
            )
            self.canvas.tag_bind(link_id, "<Button-1>", self._open_pdf)
            self.link_items.append(link_id)

            self.won = True
            self._start_hearts_animation()

        self.replaced_paths.add(p)

    # ---------- Animation coeurs ----------
    def _start_hearts_animation(self):
        """Fait tomber les cœurs jusqu’en bas complet, durée calculée pour y parvenir."""
        w = max(1, self.canvas.winfo_width())
        h = max(1, self.canvas.winfo_height())
        self.heart_items.clear()

        for _ in range(HEART_COUNT):
            x = random.randint(0, w - 20)
            y = random.randint(-h, 0)
            size = random.randint(HEART_MIN_SIZE, HEART_MAX_SIZE)
            speed = random.uniform(HEART_MIN_SPEED, HEART_MAX_SPEED)
            it = self.canvas.create_text(x, y, text="❤", font=emoji_font_tuple(size), fill="red")
            self.canvas.tag_raise(it)
            self.heart_items.append((it, speed))

        self.heart_running = True
        self._animate_hearts()

        max_distance_px = 2 * h + 40
        ticks_needed = int(max_distance_px / HEART_MIN_SPEED) + 2
        duration_ms = ticks_needed * HEART_TICK_MS
        self.after(duration_ms, self._stop_hearts_animation)

    def _animate_hearts(self):
        if not self.heart_running:
            return
        for it, speed in self.heart_items:
            self.canvas.move(it, 0, speed)
        self.after(HEART_TICK_MS, self._animate_hearts)

    def _stop_hearts_animation(self):
        self.heart_running = False
        for it, _ in self.heart_items:
            try:
                self.canvas.delete(it)
            except tk.TclError:
                pass
        self.heart_items.clear()

if __name__ == "__main__":
    app = BakeryApp()
    app.mainloop()
