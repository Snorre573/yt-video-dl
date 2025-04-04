import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import subprocess
import threading
import requests
import zipfile
import shutil
import sys

APP_DIR = os.path.join("C:\\yt-dlp-gui")
YTDLP_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
FFMPEG_ZIP_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"


def verificar_existencia_yt_dlp():
    try:
        subprocess.run(["yt-dlp", "--version"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        return os.path.exists(os.path.join(APP_DIR, "yt-dlp.exe"))


def verificar_existencia_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        return os.path.exists(os.path.join(APP_DIR, "ffmpeg.exe"))


def baixar_arquivo(url, destino, status_label, progress):
    r = requests.get(url, stream=True)
    total = int(r.headers.get("content-length", 0))
    baixado = 0
    with open(destino, "wb") as f:
        for chunk in r.iter_content(1024):
            if chunk:
                f.write(chunk)
                baixado += len(chunk)
                if total:
                    progresso = int(100 * baixado / total)
                    progress["value"] = progresso
                    status_label.config(text=f"Baixando... {progresso}%")
    progress["value"] = 100


def extrair_ffmpeg(zip_path, destino, status_label):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for f in zip_ref.namelist():
            if "ffmpeg.exe" in f and "/bin/" in f.replace("\\", "/"):
                zip_ref.extract(f, destino)
                src = os.path.join(destino, f)
                dst = os.path.join(APP_DIR, "ffmpeg.exe")
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.move(src, dst)
                break
    status_label.config(text="ffmpeg extraído com sucesso!")


def adicionar_path():
    path_atual = os.environ.get("PATH", "")
    if APP_DIR not in path_atual:
        subprocess.call(f'setx PATH "%PATH%;{APP_DIR}"', shell=True)


def setup_dependencias(root):
    def processo():
        os.makedirs(APP_DIR, exist_ok=True)
        if not verificar_existencia_yt_dlp():
            status_label.config(text="Baixando yt-dlp...")
            baixar_arquivo(YTDLP_URL, os.path.join(
                APP_DIR, "yt-dlp.exe"), status_label, progress)
        else:
            status_label.config(text="yt-dlp já está instalado.")

        if not verificar_existencia_ffmpeg():
            status_label.config(text="Baixando ffmpeg...")
            ffmpeg_zip = os.path.join(APP_DIR, "ffmpeg.zip")
            baixar_arquivo(FFMPEG_ZIP_URL, ffmpeg_zip, status_label, progress)
            status_label.config(text="Extraindo ffmpeg...")
            extrair_ffmpeg(ffmpeg_zip, APP_DIR, status_label)
            os.remove(ffmpeg_zip)
        else:
            status_label.config(text="ffmpeg já está instalado.")

        adicionar_path()
        status_label.config(text="Tudo pronto! Reiniciando app...")
        root.after(2000, lambda: [root.destroy(), abrir_app()])

    root = tk.Tk()
    root.title("Configurando Dependências")
    root.geometry("400x150")
    status_label = tk.Label(root, text="Inicializando...")
    status_label.pack(pady=10)
    progress = ttk.Progressbar(root, length=300)
    progress.pack(pady=10)
    threading.Thread(target=processo, daemon=True).start()
    root.mainloop()


def iniciar_interface():
    def download_video_audio(apenas_audio):
        url = url_entry.get().strip()
        if not url:
            messagebox.showerror("Erro", "Por favor, insira um link válido!")
            return

        output_dir = filedialog.askdirectory(
            title="Escolha a pasta de destino")
        if not output_dir:
            return

        download_btn.config(state=tk.DISABLED)
        progress_bar.start()

        def run_download():
            yt_dlp_path = "yt-dlp" if verificar_existencia_yt_dlp() else os.path.join(APP_DIR,
                                                                                      "yt-dlp.exe")
            cmd = [
                yt_dlp_path,
                "-f", "bestaudio" if apenas_audio else "bestvideo+bestaudio",
                "-o", os.path.join(output_dir, "%(title)s.%(ext)s")
            ]
            if apenas_audio:
                cmd += ["--extract-audio", "--audio-format", "mp3"]
            cmd.append(url)
            try:
                subprocess.run(cmd, check=True)
                messagebox.showinfo("Sucesso", "Download concluído!")
            except subprocess.CalledProcessError as e:
                messagebox.showerror("Erro", f"Erro ao baixar o vídeo: {e}")
            finally:
                download_btn.config(state=tk.NORMAL)
                progress_bar.stop()

        threading.Thread(target=run_download, daemon=True).start()

    top = tk.Tk()
    top.title("YouTube Downloader")
    top.geometry("450x300")
    top.configure(bg="#1e1e1e")

    style = ttk.Style(top)
    style.theme_use('clam')
    style.configure("TButton", foreground="#ffffff",
                    background="#3a3a3a", padding=6)
    style.configure("TLabel", foreground="#ffffff", background="#1e1e1e")
    style.configure("TProgressbar", troughcolor="#2e2e2e",
                    background="#4caf50")

    ttk.Label(top, text="Cole o link do vídeo aqui:").pack(pady=10)
    url_entry = ttk.Entry(top, width=60)
    url_entry.pack(pady=5)

    btn_frame = tk.Frame(top, bg="#1e1e1e")
    btn_frame.pack(pady=10)

    download_btn = ttk.Button(
        btn_frame, text="⬇️ Baixar Vídeo + Áudio", command=lambda: download_video_audio(False))
    download_btn.grid(row=0, column=0, padx=5)

    audio_btn = ttk.Button(btn_frame, text="🎵 Baixar Apenas Áudio (MP3)",
                           command=lambda: download_video_audio(True))
    audio_btn.grid(row=0, column=1, padx=5)

    progress_bar = ttk.Progressbar(top, mode='indeterminate', length=300)
    progress_bar.pack(pady=20)

    top.mainloop()


def abrir_app():
    if not (verificar_existencia_yt_dlp() and verificar_existencia_ffmpeg()):
        setup_dependencias(None)
    else:
        iniciar_interface()


if __name__ == "__main__":
    abrir_app()
